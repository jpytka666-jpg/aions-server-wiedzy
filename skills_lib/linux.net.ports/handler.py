"""Skill linux.net.ports — ss -tlnp (SSH, read-only)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from runtime.transport.ssh_executor import SSHExecutor  # noqa: E402


PROC_RE = re.compile(r'\(\("([^"]+)"')


def _split_addr_port(s: str):
    if s.startswith("["):
        host, _, port = s.rpartition("]:")
        host = host + "]"
    else:
        host, _, port = s.rpartition(":")
    return host, port


def run(inputs: dict, ctx) -> dict:
    inputs = inputs or {}
    host_alias = inputs.get("host_alias") or "aions-node-1"
    ex = SSHExecutor(host_alias=host_alias)

    cmd = "sudo -n ss -tlnp"
    res = ex.run(cmd, timeout=20)
    if res["rc"] != 0:
        return {"ok": False, "error": f"ss failed rc={res['rc']}: {res['stderr']}", "listening": []}

    lines = [ln for ln in res["stdout"].strip().splitlines() if ln.strip()]
    listening = []
    for line in lines:
        if line.strip().startswith("State"):
            continue
        parts = line.split(None, 5)
        if len(parts) < 5:
            continue
        state, recvq, sendq, local_addr, peer_addr = parts[:5]
        process_field = parts[5] if len(parts) > 5 else ""
        _, port = _split_addr_port(local_addr)
        m = PROC_RE.search(process_field)
        proc_name = m.group(1) if m else None
        listening.append({
            "proto": "tcp",
            "local": local_addr,
            "port": port,
            "process": proc_name,
        })

    return {"ok": True, "listening": listening, "count": len(listening)}
