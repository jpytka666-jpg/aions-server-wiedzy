"""Skill linux.service.status — systemctl status <name> --no-pager (SSH, read-only)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from runtime.transport.ssh_executor import SSHExecutor  # noqa: E402


def _parse_status(text: str) -> dict:
    out = {"active_state": None, "sub_state": None, "loaded": None,
           "description": None, "main_pid": None}

    m = re.search(r"^\s*Loaded:\s*(.+)$", text, re.MULTILINE)
    if m:
        out["loaded"] = m.group(1).strip()

    m = re.search(r"Active:\s*(\S+)\s*\(([^)]+)\)", text)
    if m:
        out["active_state"] = m.group(1)
        out["sub_state"] = m.group(2)

    m = re.search(r"Main PID:\s*(\d+)", text)
    if m:
        out["main_pid"] = int(m.group(1))

    lines = text.strip().splitlines()
    if lines:
        m2 = re.match(r"^\S+\s*-\s*(.+)$", lines[0].strip())
        if m2:
            out["description"] = m2.group(1).strip()

    return out


def run(inputs: dict, ctx) -> dict:
    inputs = inputs or {}
    name = inputs.get("name")
    if not name:
        return {"ok": False, "error": "missing required input: name"}

    host_alias = inputs.get("host_alias") or "aions-node-1"
    ex = SSHExecutor(host_alias=host_alias)

    cmd = f"systemctl status {name} --no-pager"
    res = ex.run(cmd, timeout=20)

    # systemctl exit codes: 0=active, 3=inactive/dead/failed — both are valid,
    # meaningful data about the unit's state, not a transport error.
    known_data = res["rc"] in (0, 3) and res["stdout"].strip() != ""
    if not known_data and res["rc"] not in (0, 3):
        return {"ok": False, "error": f"systemctl failed rc={res['rc']}: {res['stderr']}",
                "service": name, "rc": res["rc"]}

    parsed = _parse_status(res["stdout"])
    return {
        "ok": True,
        "rc": res["rc"],
        "service": name,
        **parsed,
        "raw": res["stdout"],
    }
