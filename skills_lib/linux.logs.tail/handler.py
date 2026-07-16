"""Skill linux.logs.tail — journalctl -u <unit> -n <lines> (SSH, read-only)."""
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
    unit = inputs.get("unit")
    if not unit:
        return {"ok": False, "error": "missing required input: unit"}
    lines_n = int(inputs.get("lines") or 50)
    host_alias = inputs.get("host_alias") or "aions-node-1"
    ex = SSHExecutor(host_alias=host_alias)

    cmd = f"sudo -n journalctl -u {shlex.quote(unit)} -n {lines_n} --no-pager"
    res = ex.run(cmd, timeout=30)
    if res["rc"] != 0:
        return {"ok": False, "error": f"journalctl failed rc={res['rc']}: {res['stderr']}",
                "unit": unit, "lines": []}

    out_lines = [ln for ln in res["stdout"].splitlines()]
    return {"ok": True, "unit": unit, "lines": out_lines, "count": len(out_lines)}
