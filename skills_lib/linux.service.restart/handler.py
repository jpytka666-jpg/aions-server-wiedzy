"""Skill linux.service.restart — sudo -n systemctl restart <name> (SSH, mutating).

risk: medium — bramka silnika klasyfikuje to jako "mutate": wykonanie jest
zawsze dozwolone, ale kazde uruchomienie jest audytowane (gate.audit).
"""
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
    name = inputs.get("name")
    if not name:
        return {"ok": False, "error": "missing required input: name", "restarted": False, "active": None}

    host_alias = inputs.get("host_alias") or "aions-node-1"
    ex = SSHExecutor(host_alias=host_alias)

    safe_name = shlex.quote(name)
    restart_res = ex.run(f"sudo -n systemctl restart {safe_name}", timeout=30)
    restarted = restart_res["rc"] == 0

    status_res = ex.run(f"systemctl is-active {safe_name}", timeout=15)
    active = (status_res["stdout"].strip() or status_res["stderr"].strip() or None)

    return {
        "ok": restarted,
        "restarted": restarted,
        "active": active,
        "name": name,
        "restart_rc": restart_res["rc"],
        "restart_error": None if restarted else restart_res["stderr"],
    }
