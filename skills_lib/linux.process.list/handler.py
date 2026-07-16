"""Skill linux.process.list — ps aux --sort=-%cpu (SSH, read-only)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from runtime.transport.ssh_executor import SSHExecutor  # noqa: E402


def _parse_ps(text: str, limit: int) -> list:
    lines = [ln for ln in text.strip().splitlines() if ln.strip()]
    if not lines:
        return []
    rows = []
    for line in lines[1:]:  # skip header
        parts = line.split(None, 10)
        if len(parts) < 11:
            continue
        user, pid, cpu, mem, vsz, rss, tty, stat, start, time_, command = parts
        try:
            pid_i = int(pid)
        except ValueError:
            continue
        rows.append({
            "user": user,
            "pid": pid_i,
            "cpu": float(cpu),
            "mem": float(mem),
            "command": command,
        })
    return rows[:limit]


def run(inputs: dict, ctx) -> dict:
    inputs = inputs or {}
    limit = int(inputs.get("limit") or 30)
    host_alias = inputs.get("host_alias") or "aions-node-1"
    ex = SSHExecutor(host_alias=host_alias)

    cmd = f"ps aux --sort=-%cpu | head -n {limit + 1}"
    res = ex.run(cmd, timeout=20)
    if res["rc"] != 0:
        return {"ok": False, "error": f"ps failed rc={res['rc']}: {res['stderr']}", "processes": []}

    processes = _parse_ps(res["stdout"], limit)
    return {"ok": True, "processes": processes, "count": len(processes)}
