"""Skill linux.net.ping — ping -c <count> -W 3 <host> (SSH, read-only)."""
from __future__ import annotations

import re
import shlex
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from runtime.transport.ssh_executor import SSHExecutor  # noqa: E402


def run(inputs: dict, ctx) -> dict:
    inputs = inputs or {}
    host = inputs.get("host")
    if not host:
        return {"ok": False, "error": "missing required input: host"}
    count = int(inputs.get("count") or 3)
    host_alias = inputs.get("host_alias") or "aions-node-1"
    ex = SSHExecutor(host_alias=host_alias)

    cmd = f"ping -c {count} -W 3 {shlex.quote(host)}"
    res = ex.run(cmd, timeout=count * 3 + 10)

    text = res["stdout"]
    transmitted = received = None
    loss_pct = None
    avg_ms = None

    m = re.search(r'(\d+)\s+packets transmitted,\s*(\d+)\s+received', text)
    if m:
        transmitted = int(m.group(1))
        received = int(m.group(2))

    m = re.search(r'(\d+(?:\.\d+)?)%\s+packet loss', text)
    if m:
        loss_pct = float(m.group(1))

    m = re.search(r'=\s*[\d.]+/([\d.]+)/[\d.]+/[\d.]+\s*ms', text)
    if m:
        avg_ms = float(m.group(1))

    reachable = bool(received and received > 0)
    # ping rc: 0 = at least one reply, 1 = no reply but host resolved (valid
    # data, host just unreachable), 2 = transport/DNS error.
    ok = res["rc"] in (0, 1) and transmitted is not None

    return {
        "ok": ok,
        "host": host,
        "transmitted": transmitted,
        "received": received,
        "loss_pct": loss_pct,
        "avg_ms": avg_ms,
        "reachable": reachable,
        "error": None if ok else res["stderr"],
        "raw": text,
    }
