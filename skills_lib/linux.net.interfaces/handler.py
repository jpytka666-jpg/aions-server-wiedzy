"""Skill linux.net.interfaces — ip -j addr (SSH, read-only)."""
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

    res = ex.run_json("ip -j addr", timeout=20)
    if res["rc"] != 0 or res.get("json") is None:
        return {
            "ok": False,
            "error": res.get("json_error") or f"ip -j addr failed rc={res['rc']}: {res['stderr']}",
            "interfaces": [],
        }

    interfaces = []
    for iface in res["json"]:
        ipv4 = []
        for addr in (iface.get("addr_info") or []):
            if addr.get("family") == "inet":
                ipv4.append(f"{addr.get('local')}/{addr.get('prefixlen')}")
        interfaces.append({
            "name": iface.get("ifname"),
            "state": iface.get("operstate"),
            "ipv4": ipv4,
        })

    return {"ok": True, "interfaces": interfaces, "count": len(interfaces)}
