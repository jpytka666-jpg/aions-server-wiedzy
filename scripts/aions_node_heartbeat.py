#!/usr/bin/env python3
"""AIONS node heartbeat client — POST /v1/nodes/{id}/heartbeat every ~60s.

Windows-friendly: run via scripts/aions_python.ps1 or directly with venv Python.

Env:
  AIONS_NODE_ID       Node id (default: windows-primary / linux-primary from platform)
  AIONS_CORE_URL      Core API base (default: http://127.0.0.1:8765)
  AIONS_NODE_STATE    Optional dir with node_registration.json (reads node_id)

Examples:
  .\\scripts\\aions_python.ps1 scripts\\aions_node_heartbeat.py --once
  .\\scripts\\aions_python.ps1 scripts\\aions_node_heartbeat.py --interval 60
  AIONS_NODE_ID=proxmox-vm9100 AIONS_CORE_URL=http://127.0.0.1:8765 \\
    python scripts/aions_node_heartbeat.py --interval 60
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_CORE = os.environ.get("AIONS_CORE_URL", "http://127.0.0.1:8765")
DEFAULT_INTERVAL = int(os.environ.get("AIONS_HEARTBEAT_INTERVAL_SEC", "60"))


def _default_node_id() -> str:
    env_id = os.environ.get("AIONS_NODE_ID", "").strip()
    if env_id:
        return env_id
    state_dir = Path(os.environ.get("AIONS_NODE_STATE", "/var/lib/aions"))
    reg_file = state_dir / "node_registration.json"
    if reg_file.is_file():
        try:
            data = json.loads(reg_file.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("node_id"):
                return str(data["node_id"])
        except (OSError, json.JSONDecodeError):
            pass
    win = platform.system().lower() == "windows"
    return "windows-primary" if win else "linux-primary"


def _probe_load() -> float:
    try:
        import psutil  # type: ignore[import-untyped]

        return round(min(1.0, max(0.0, psutil.cpu_percent(interval=0.1) / 100.0)), 3)
    except Exception:
        return 0.0


def send_heartbeat(
    *,
    core_url: str,
    node_id: str,
    health: str = "ok",
    load: float | None = None,
    timeout: float = 10.0,
) -> dict[str, Any]:
    base = core_url.rstrip("/")
    url = f"{base}/v1/nodes/{node_id}/heartbeat"
    payload: dict[str, Any] = {"health": health}
    if load is not None:
        payload["load"] = max(0.0, min(1.0, load))
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def heartbeat_once(
    *,
    core_url: str,
    node_id: str,
    health: str,
    auto_load: bool,
    timeout: float,
) -> dict[str, Any]:
    load = _probe_load() if auto_load else None
    return send_heartbeat(
        core_url=core_url,
        node_id=node_id,
        health=health,
        load=load,
        timeout=timeout,
    )


def run_loop(
    *,
    core_url: str,
    node_id: str,
    interval: int,
    health: str,
    auto_load: bool,
    timeout: float,
    max_ticks: int | None,
) -> int:
    tick = 0
    while True:
        tick += 1
        ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        try:
            result = heartbeat_once(
                core_url=core_url,
                node_id=node_id,
                health=health,
                auto_load=auto_load,
                timeout=timeout,
            )
            status = result.get("status", "ok")
            node = result.get("node") or {}
            load = node.get("load", "?")
            print(f"[{ts}] heartbeat OK node={node_id} status={status} load={load}", flush=True)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:200]
            print(
                f"[{ts}] heartbeat HTTP {exc.code} node={node_id}: {detail}",
                file=sys.stderr,
                flush=True,
            )
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            print(f"[{ts}] heartbeat FAIL node={node_id}: {exc}", file=sys.stderr, flush=True)

        if max_ticks is not None and tick >= max_ticks:
            return 0
        time.sleep(max(5, interval))


def main() -> int:
    parser = argparse.ArgumentParser(description="AIONS node heartbeat (Core API client)")
    parser.add_argument("--core-url", default=DEFAULT_CORE, help="Core API base URL")
    parser.add_argument("--node-id", default="", help="Node id (default: env or platform)")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL, help="Seconds between beats")
    parser.add_argument("--once", action="store_true", help="Send one heartbeat and exit")
    parser.add_argument("--health", default="ok", help="Health status string")
    parser.add_argument("--no-load", action="store_true", help="Skip CPU load in payload")
    parser.add_argument("--timeout", type=float, default=10.0, help="HTTP timeout seconds")
    parser.add_argument("--ticks", type=int, default=0, help="Max loop ticks (0 = infinite)")
    args = parser.parse_args()

    node_id = args.node_id.strip() or _default_node_id()
    auto_load = not args.no_load
    max_ticks = 1 if args.once else (args.ticks if args.ticks > 0 else None)

    if args.once or (args.ticks == 1):
        try:
            result = heartbeat_once(
                core_url=args.core_url,
                node_id=node_id,
                health=args.health,
                auto_load=auto_load,
                timeout=args.timeout,
            )
            print(json.dumps(result, ensure_ascii=False))
            return 0
        except urllib.error.HTTPError as exc:
            print(f"HTTP {exc.code}: {exc.read().decode(errors='replace')}", file=sys.stderr)
            return 1
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            print(f"heartbeat failed: {exc}", file=sys.stderr)
            return 1

    print(
        f"[AIONS] heartbeat loop node={node_id} core={args.core_url} interval={args.interval}s",
        flush=True,
    )
    return run_loop(
        core_url=args.core_url,
        node_id=node_id,
        interval=args.interval,
        health=args.health,
        auto_load=auto_load,
        timeout=args.timeout,
        max_ticks=max_ticks,
    )


if __name__ == "__main__":
    raise SystemExit(main())
