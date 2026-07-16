"""Skill linux.process.find — pgrep -af <pattern> (SSH, read-only)."""
from __future__ import annotations

import shlex
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from runtime.transport.ssh_executor import SSHExecutor  # noqa: E402


def run(inputs: dict, ctx) -> dict:
    inputs = inputs or {}
    pattern = inputs.get("pattern")
    if not pattern:
        return {"ok": False, "error": "missing required input: pattern"}
    host_alias = inputs.get("host_alias") or "aions-node-1"
    ex = SSHExecutor(host_alias=host_alias)

    cmd = f"pgrep -af {shlex.quote(pattern)}"
    res = ex.run(cmd, timeout=20)
    # pgrep: rc=0 matches found, rc=1 no matches (valid empty result), rc>=2 error.
    if res["rc"] not in (0, 1):
        return {"ok": False, "error": f"pgrep failed rc={res['rc']}: {res['stderr']}",
                "pattern": pattern, "processes": []}

    processes = []
    for line in res["stdout"].strip().splitlines():
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        pid, cmdline = parts
        try:
            pid_i = int(pid)
        except ValueError:
            continue
        processes.append({"pid": pid_i, "cmdline": cmdline})

    return {"ok": True, "pattern": pattern, "processes": processes, "count": len(processes)}
