"""Skill test.gate.destructive -- TEST ONLY.

Creates /tmp/aions_gate_test on the remote host via SSH. Used exclusively to
exercise the security gate (control_plane/skills/gate.py) from
runtime/transport/test_gate.py. Deliberately classified risk=high
(destructive) so the gate must block it without a live approval.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from runtime.transport.ssh_executor import SSHExecutor  # noqa: E402


def run(inputs: dict, ctx) -> dict:
    inputs = inputs or {}
    host_alias = inputs.get("host_alias") or "aions-node-1"
    ex = SSHExecutor(host_alias=host_alias)
    res = ex.run("touch /tmp/aions_gate_test", timeout=15)
    if res["rc"] != 0:
        return {"ok": False, "error": f"touch failed rc={res['rc']}: {res['stderr']}"}
    return {"ok": True}
