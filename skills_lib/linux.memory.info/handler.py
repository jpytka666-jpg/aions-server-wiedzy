"""Skill linux.memory.info — free -m + /proc/loadavg (SSH, read-only)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from runtime.transport.ssh_executor import SSHExecutor  # noqa: E402

_MARKER = "---LOADAVG---"


def _parse_free(text: str) -> dict:
    result = {}
    for line in text.splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0].startswith("Mem:") and len(parts) >= 4:
            result["mem"] = {
                "total_mb": _to_int(parts[1]),
                "used_mb": _to_int(parts[2]),
                "free_mb": _to_int(parts[3]),
                "shared_mb": _to_int(parts[4]) if len(parts) > 4 else None,
                "buff_cache_mb": _to_int(parts[5]) if len(parts) > 5 else None,
                "available_mb": _to_int(parts[6]) if len(parts) > 6 else None,
            }
        elif parts[0].startswith("Swap:") and len(parts) >= 4:
            result["swap"] = {
                "total_mb": _to_int(parts[1]),
                "used_mb": _to_int(parts[2]),
                "free_mb": _to_int(parts[3]),
            }
    return result


def _parse_loadavg(text: str) -> dict:
    parts = text.strip().split()
    if len(parts) < 3:
        return {}
    out = {
        "load_1m": _to_float(parts[0]),
        "load_5m": _to_float(parts[1]),
        "load_15m": _to_float(parts[2]),
    }
    if len(parts) > 3:
        out["running_kernel_entities"] = parts[3]
    if len(parts) > 4:
        out["last_pid"] = parts[4]
    return out


def _to_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def run(inputs: dict, ctx) -> dict:
    inputs = inputs or {}
    host_alias = inputs.get("host_alias") or "aions-node-1"
    ex = SSHExecutor(host_alias=host_alias)

    cmd = f"free -m && echo '{_MARKER}' && cat /proc/loadavg"
    res = ex.run(cmd, timeout=15)
    if res["rc"] != 0:
        return {"ok": False, "error": f"free/loadavg failed rc={res['rc']}: {res['stderr']}"}

    parts = res["stdout"].split(_MARKER)
    free_part = parts[0] if parts else ""
    load_part = parts[1] if len(parts) > 1 else ""

    memory = _parse_free(free_part)
    loadavg = _parse_loadavg(load_part)

    return {"ok": True, "memory": memory, "loadavg": loadavg}
