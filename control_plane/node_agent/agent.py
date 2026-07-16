#!/usr/bin/env python3
"""AIONS Node Agent — lightweight daemon speaking the native AIONS Core protocol.

Runs on a Linux worker VM (e.g. proxmox-9100). Registers itself with AIONS
Core (POST /v1/nodes/register), sends periodic heartbeats with basic host
metrics (POST /v1/nodes/{node_id}/heartbeat), and exposes a minimal local
HTTP API so Core (or an operator) can execute shell commands on this host:

    GET  /v1/health   -> {"status": "ok", "node_id": ..., "uptime_s": ...}
    POST /v1/execute  -> {"cmd": "...", "timeout": <=60}
                          header X-AIONS-Token must match config token
                          -> {"rc", "stdout", "stderr", "duration_ms"}

Python 3.10 standard library ONLY — no pip dependencies. Uses http.server,
urllib.request, json, subprocess, threading, /proc and `df` for metrics.

Config file (JSON), default /opt/aions/node_agent/config.json:
    {
      "node_id": "proxmox-9100",
      "core_url": "http://192.168.1.171:8765",
      "token": "<random hex>",
      "bind": "0.0.0.0",
      "port": 8899
    }

Notes on the Core protocol (control_plane/node_registry.py + api.py):
  - POST {core_url}/v1/nodes/register
        body: {node_id, host, capabilities[], memory_mb, tools[], health,
               load, permissions[]}
        -> {"status": "registered", "node": {...}}
  - POST {core_url}/v1/nodes/{node_id}/heartbeat
        body: {health, load}  (extra keys are accepted and ignored by the
               current pydantic model, but sent anyway for forward-compat
               and for anyone tailing Core logs / a future schema bump)
        -> {"status": "ok", "node": {...}}

  The current NodeRecord schema (runtime/node/schema.json) has no generic
  "metadata" object, so hostname/ip/platform are folded into the accepted
  fields: `host` carries the routable IP, and `capabilities` gets
  "linux" plus a "hostname:<value>" tag so the info is visible in the
  registry without inventing new Core-side fields (Core/API/registry are
  NOT modified by this agent — out of scope for C1).
"""

from __future__ import annotations

import json
import logging
import logging.handlers
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

AGENT_VERSION = "1.0.0"
DEFAULT_CONFIG_PATH = os.environ.get(
    "AIONS_NODE_AGENT_CONFIG", "/opt/aions/node_agent/config.json"
)
MAX_OUTPUT_BYTES = 64 * 1024  # 64KB cap on stdout/stderr
MAX_CMD_TIMEOUT = 60
HEARTBEAT_INTERVAL_SEC = 30
REG_BACKOFF_START = 5
REG_BACKOFF_MAX = 60

START_TS = time.monotonic()

_LOG = logging.getLogger("aions.node_agent")


# --------------------------------------------------------------------------
# Config + logging
# --------------------------------------------------------------------------


def load_config(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        raise SystemExit(f"config not found: {p}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"failed to read config {p}: {exc}") from exc

    required = ["node_id", "core_url", "token"]
    missing = [k for k in required if not data.get(k)]
    if missing:
        raise SystemExit(f"config missing required keys: {missing}")

    data.setdefault("bind", "0.0.0.0")
    data.setdefault("port", 8899)
    return data


def setup_logging(config_path: str) -> None:
    log_dir = Path(config_path).resolve().parent
    log_file = log_dir / "agent.log"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

    _LOG.setLevel(logging.INFO)
    fmt = logging.Formatter(
        "%(asctime)s %(levelname)s [%(threadName)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    try:
        fh = logging.handlers.RotatingFileHandler(
            str(log_file), maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        fh.setFormatter(fmt)
        _LOG.addHandler(fh)
    except OSError as exc:  # pragma: no cover - filesystem edge cases
        print(f"WARNING: could not open log file {log_file}: {exc}", file=sys.stderr)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    _LOG.addHandler(sh)


# --------------------------------------------------------------------------
# Host metrics (no psutil — /proc + df only)
# --------------------------------------------------------------------------


def get_cpu_load_1m() -> float:
    try:
        with open("/proc/loadavg", "r", encoding="utf-8") as fh:
            return float(fh.read().split()[0])
    except (OSError, ValueError, IndexError):
        return 0.0


def get_cpu_count() -> int:
    try:
        return max(1, os.cpu_count() or 1)
    except Exception:
        return 1


def get_normalized_load() -> float:
    """Core's `load` field is normalized 0.0-1.0; loadavg/nproc, clamped."""
    load1 = get_cpu_load_1m()
    n = get_cpu_count()
    return round(max(0.0, min(1.0, load1 / n)), 3)


def get_mem_used_pct() -> float:
    try:
        info: dict[str, int] = {}
        with open("/proc/meminfo", "r", encoding="utf-8") as fh:
            for line in fh:
                parts = line.split(":")
                if len(parts) != 2:
                    continue
                key = parts[0].strip()
                val = parts[1].strip().split()[0]
                info[key] = int(val)
        total = info.get("MemTotal", 0)
        avail = info.get("MemAvailable", info.get("MemFree", 0))
        if total <= 0:
            return 0.0
        used_pct = (total - avail) / total * 100.0
        return round(max(0.0, min(100.0, used_pct)), 2)
    except (OSError, ValueError):
        return 0.0


def get_mem_total_mb() -> int:
    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("MemTotal:"):
                    kb = int(line.split()[1])
                    return kb // 1024
    except (OSError, ValueError, IndexError):
        pass
    return 0


def get_disk_used_pct(path: str = "/") -> float:
    try:
        st = os.statvfs(path)
        total = st.f_blocks * st.f_frsize
        free = st.f_bfree * st.f_frsize
        if total <= 0:
            return 0.0
        used_pct = (total - free) / total * 100.0
        return round(max(0.0, min(100.0, used_pct)), 2)
    except OSError:
        # Fallback to `df` if statvfs is unavailable for some reason.
        try:
            out = subprocess.run(
                ["df", "-P", path], capture_output=True, text=True, timeout=5
            )
            lines = out.stdout.strip().splitlines()
            if len(lines) >= 2:
                pct = lines[1].split()[4].rstrip("%")
                return float(pct)
        except Exception:
            pass
        return 0.0


def get_metrics() -> dict[str, float]:
    return {
        "cpu_load_1m": get_cpu_load_1m(),
        "mem_used_pct": get_mem_used_pct(),
        "disk_used_pct": get_disk_used_pct("/"),
    }


def get_local_ip(core_host: str) -> str:
    """Best-effort local outbound IP toward core_host (UDP connect, no packet sent)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect((core_host, 80))
            return s.getsockname()[0]
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "127.0.0.1"


def parse_core_host(core_url: str) -> str:
    from urllib.parse import urlparse

    return urlparse(core_url).hostname or "127.0.0.1"


# --------------------------------------------------------------------------
# Core protocol client (register + heartbeat)
# --------------------------------------------------------------------------


class CoreClient:
    def __init__(self, config: dict[str, Any]) -> None:
        self.node_id: str = config["node_id"]
        self.core_url: str = config["core_url"].rstrip("/")
        self.hostname = socket.gethostname()
        self.ip = get_local_ip(parse_core_host(self.core_url))
        self.registered = False

    def _post(self, path: str, payload: dict[str, Any], timeout: float = 10.0) -> dict[str, Any]:
        url = f"{self.core_url}{path}"
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def register(self) -> bool:
        payload = {
            "node_id": self.node_id,
            "host": self.ip,
            "capabilities": ["shell", "linux", "node-agent", f"hostname:{self.hostname}"],
            "memory_mb": get_mem_total_mb(),
            "tools": ["execute"],
            "health": "ok",
            "load": get_normalized_load(),
            "permissions": ["execute"],
        }
        try:
            result = self._post("/v1/nodes/register", payload)
            _LOG.info("registered with Core: %s", result)
            self.registered = True
            return True
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:300]
            _LOG.warning("registration HTTP %s: %s", exc.code, detail)
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            _LOG.warning("registration failed: %s", exc)
        return False

    def heartbeat(self) -> bool:
        metrics = get_metrics()
        payload = {
            "health": "ok",
            "load": get_normalized_load(),
            # Extra metrics — accepted-and-ignored by the current Core
            # pydantic model, kept for forward compatibility / operator
            # visibility (e.g. via a future Core log/inspection tool).
            "cpu_load_1m": metrics["cpu_load_1m"],
            "mem_used_pct": metrics["mem_used_pct"],
            "disk_used_pct": metrics["disk_used_pct"],
        }
        try:
            result = self._post(f"/v1/nodes/{self.node_id}/heartbeat", payload)
            _LOG.info("heartbeat ok: %s", result.get("status"))
            return True
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:300]
            if exc.code == 404:
                # Node unknown to Core (e.g. Core restarted / not yet
                # registered) — flag so the main loop re-registers.
                _LOG.warning("heartbeat 404 (node unknown to Core), will re-register: %s", detail)
                self.registered = False
            else:
                _LOG.warning("heartbeat HTTP %s: %s", exc.code, detail)
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            _LOG.warning("heartbeat failed: %s", exc)
        return False


def registration_and_heartbeat_loop(client: CoreClient, stop_event: threading.Event) -> None:
    """Registers at startup (retry w/ backoff), then heartbeats every 30s.

    Runs entirely independent of the local HTTP server: if Core is
    unreachable (firewall, Core down, network blip) the agent keeps
    retrying in the background and continues serving /v1/execute locally.
    """
    backoff = REG_BACKOFF_START
    while not stop_event.is_set():
        if not client.registered:
            ok = client.register()
            if ok:
                backoff = REG_BACKOFF_START
                # Send an immediate heartbeat right after registering.
                client.heartbeat()
                stop_event.wait(HEARTBEAT_INTERVAL_SEC)
                continue
            _LOG.warning("Core unreachable, retrying registration in %ss (local agent stays up)", backoff)
            stop_event.wait(backoff)
            backoff = min(REG_BACKOFF_MAX, backoff * 2)
            continue

        client.heartbeat()
        stop_event.wait(HEARTBEAT_INTERVAL_SEC)


# --------------------------------------------------------------------------
# Local HTTP API: GET /v1/health, POST /v1/execute
# --------------------------------------------------------------------------


class AgentState:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.node_id: str = config["node_id"]
        self.token: str = config["token"]


_STATE: AgentState | None = None


def _truncate(s: str, limit: int = MAX_OUTPUT_BYTES) -> str:
    b = s.encode("utf-8", errors="replace")
    if len(b) <= limit:
        return s
    return b[:limit].decode("utf-8", errors="ignore") + "\n...[truncated]"


class Handler(BaseHTTPRequestHandler):
    server_version = f"AIONSNodeAgent/{AGENT_VERSION}"

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
        _LOG.info("http %s - %s", self.address_string(), fmt % args)

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self) -> None:  # noqa: N802
        assert _STATE is not None
        if self.path.rstrip("/") == "/v1/health" or self.path == "/v1/health":
            uptime = time.monotonic() - START_TS
            self._send_json(
                200,
                {"status": "ok", "node_id": _STATE.node_id, "uptime_s": round(uptime, 1)},
            )
            return
        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        assert _STATE is not None
        if self.path.rstrip("/") != "/v1/execute":
            self._send_json(404, {"error": "not_found"})
            return

        token = self.headers.get("X-AIONS-Token", "")
        if not token or token != _STATE.token:
            self._send_json(401, {"error": "unauthorized"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(length) if length > 0 else b"{}"
            body = json.loads(raw.decode("utf-8") or "{}")
        except (ValueError, json.JSONDecodeError):
            self._send_json(400, {"error": "invalid_json"})
            return

        cmd = body.get("cmd")
        if not isinstance(cmd, str) or not cmd.strip():
            self._send_json(400, {"error": "cmd_required"})
            return

        timeout = body.get("timeout", 30)
        try:
            timeout = int(timeout)
        except (TypeError, ValueError):
            timeout = 30
        timeout = max(1, min(MAX_CMD_TIMEOUT, timeout))

        start = time.monotonic()
        try:
            proc = subprocess.run(
                ["bash", "-c", cmd],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            rc = proc.returncode
            stdout = proc.stdout
            stderr = proc.stderr
        except subprocess.TimeoutExpired as exc:
            rc = -1
            stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
            stderr = ((exc.stderr or "") if isinstance(exc.stderr, str) else "") + f"\n[agent] timeout after {timeout}s"
        except OSError as exc:
            rc = -1
            stdout = ""
            stderr = f"[agent] exec failed: {exc}"
        duration_ms = int((time.monotonic() - start) * 1000)

        _LOG.info("execute cmd=%r rc=%s duration_ms=%s", cmd[:200], rc, duration_ms)
        self._send_json(
            200,
            {
                "rc": rc,
                "stdout": _truncate(stdout),
                "stderr": _truncate(stderr),
                "duration_ms": duration_ms,
            },
        )


def run_http_server(config: dict[str, Any]) -> ThreadingHTTPServer:
    bind = config.get("bind", "0.0.0.0")
    port = int(config.get("port", 8899))
    httpd = ThreadingHTTPServer((bind, port), Handler)
    _LOG.info("HTTP API listening on %s:%s", bind, port)
    return httpd


# --------------------------------------------------------------------------
# Entrypoint
# --------------------------------------------------------------------------


def main() -> int:
    config_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CONFIG_PATH
    config = load_config(config_path)
    setup_logging(config_path)

    global _STATE
    _STATE = AgentState(config)

    _LOG.info(
        "AIONS node agent v%s starting: node_id=%s core=%s bind=%s:%s",
        AGENT_VERSION,
        config["node_id"],
        config["core_url"],
        config.get("bind"),
        config.get("port"),
    )

    client = CoreClient(config)
    stop_event = threading.Event()
    beat_thread = threading.Thread(
        target=registration_and_heartbeat_loop,
        args=(client, stop_event),
        name="core-heartbeat",
        daemon=True,
    )
    beat_thread.start()

    httpd = run_http_server(config)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        _LOG.info("shutting down")
        stop_event.set()
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
