"""Skill linux.service.list — systemctl list-units --type=service --state=running,failed (SSH, read-only)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from runtime.transport.ssh_executor import SSHExecutor  # noqa: E402


def _parse_units(text: str) -> list:
    items = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        line = line.lstrip("\u25cf").strip()  # strip leading bullet marker on failed units
        parts = line.split(None, 4)
        if len(parts) < 4:
            continue
        name, load, active, sub = parts[0], parts[1], parts[2], parts[3]
        description = parts[4] if len(parts) > 4 else ""
        items.append({"name": name, "load": load, "active": active, "sub": sub, "description": description})
    return items


def run(inputs: dict, ctx) -> dict:
    inputs = inputs or {}
    host_alias = inputs.get("host_alias") or "aions-node-1"
    ex = SSHExecutor(host_alias=host_alias)

    cmd = "systemctl list-units --type=service --state=running,failed --no-pager --no-legend"
    res = ex.run(cmd, timeout=30)
    if res["rc"] != 0:
        return {"ok": False, "error": f"systemctl failed rc={res['rc']}: {res['stderr']}", "services": []}

    services = _parse_units(res["stdout"])
    return {"ok": True, "services": services, "count": len(services)}
