"""Skill linux.uptime.info — uptime -p + uptime (SSH, read-only).

Forge candidate for A5 (linux verify-gate pipeline). Mirrors the
linux.memory.info pattern: pure SSHExecutor read, no state mutation.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from runtime.transport.ssh_executor import SSHExecutor  # noqa: E402

_MARKER = "---UPTIME---"
_LOAD_RE = re.compile(r"load average:\s*([\d.]+),\s*([\d.]+),\s*([\d.]+)")
_USERS_RE = re.compile(r"(\d+)\s+users?")


def _to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def run(inputs: dict, ctx) -> dict:
    inputs = inputs or {}
    host_alias = inputs.get("host_alias") or "aions-node-1"
    ex = SSHExecutor(host_alias=host_alias)

    cmd = f"uptime -p && echo '{_MARKER}' && uptime"
    res = ex.run(cmd, timeout=15)
    if res["rc"] != 0:
        return {"ok": False, "error": f"uptime failed rc={res['rc']}: {res['stderr']}"}

    parts = res["stdout"].split(_MARKER)
    pretty = parts[0].strip() if parts else ""
    tail = parts[1] if len(parts) > 1 else ""

    load_1m = load_5m = load_15m = None
    m = _LOAD_RE.search(tail)
    if m:
        load_1m, load_5m, load_15m = (_to_float(g) for g in m.groups())

    users = None
    mu = _USERS_RE.search(tail)
    if mu:
        try:
            users = int(mu.group(1))
        except ValueError:
            users = None

    return {
        "ok": True,
        "pretty": pretty,
        "load_1m": load_1m,
        "load_5m": load_5m,
        "load_15m": load_15m,
        "users": users,
    }
