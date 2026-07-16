"""Skill linux.pkg.list — apt list --installed / dpkg -l (SSH, read-only)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from runtime.transport.ssh_executor import SSHExecutor  # noqa: E402


APT_RE = re.compile(r'^(?P<name>[^/\s]+)/\S+\s+(?P<version>\S+)\s+\S+')


def _parse_apt_list(text: str) -> list:
    items = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("Listing..."):
            continue
        m = APT_RE.match(line)
        if not m:
            continue
        items.append({"name": m.group("name"), "version": m.group("version")})
    return items


def run(inputs: dict, ctx) -> dict:
    inputs = inputs or {}
    limit = int(inputs.get("limit") or 50)
    host_alias = inputs.get("host_alias") or "aions-node-1"
    ex = SSHExecutor(host_alias=host_alias)

    list_res = ex.run(f"apt list --installed 2>/dev/null | head -n {limit + 1}", timeout=30)
    total_res = ex.run("dpkg -l | grep -c '^ii'", timeout=20)

    packages = _parse_apt_list(list_res["stdout"]) if list_res["rc"] == 0 else []

    total = None
    if total_res["rc"] == 0:
        try:
            total = int(total_res["stdout"].strip())
        except ValueError:
            total = None

    return {
        "ok": list_res["rc"] == 0,
        "total": total,
        "packages": packages[:limit],
        "count": len(packages[:limit]),
        "error": None if list_res["rc"] == 0 else list_res["stderr"],
    }
