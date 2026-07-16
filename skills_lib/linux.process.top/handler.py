"""Skill linux.process.top — ps aux --sort=-%cpu | head -15 (SSH, read-only)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from runtime.transport.ssh_executor import SSHExecutor  # noqa: E402


def _parse_ps(text: str) -> list:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if len(lines) < 2:
        return []
    rows = []
    for line in lines[1:]:  # skip header
        parts = line.split(None, 10)
        if len(parts) < 11:
            continue
        rows.append({
            "user": parts[0],
            "pid": int(parts[1]) if parts[1].isdigit() else parts[1],
            "cpu_pct": _to_float(parts[2]),
            "mem_pct": _to_float(parts[3]),
            "vsz": parts[4],
            "rss": parts[5],
            "tty": parts[6],
            "stat": parts[7],
            "start": parts[8],
            "time": parts[9],
            "command": parts[10],
        })
    return rows


def _to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def run(inputs: dict, ctx) -> dict:
    inputs = inputs or {}
    host_alias = inputs.get("host_alias") or "aions-node-1"
    ex = SSHExecutor(host_alias=host_alias)

    res = ex.run("ps aux --sort=-%cpu | head -15", timeout=20)
    if res["rc"] != 0:
        return {"ok": False, "error": f"ps failed rc={res['rc']}: {res['stderr']}", "processes": []}

    processes = _parse_ps(res["stdout"])
    return {"ok": True, "processes": processes}
