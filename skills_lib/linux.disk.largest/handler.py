"""Skill linux.disk.largest — du -ah <path> | sort -rh | head -20 (SSH, read-only)."""
from __future__ import annotations

import shlex
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from runtime.transport.ssh_executor import SSHExecutor  # noqa: E402


def _parse_du_sorted(text: str) -> list:
    items = []
    for line in text.strip().splitlines():
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        size, path_ = parts
        items.append({"size": size, "path": path_.strip()})
    return items


def run(inputs: dict, ctx) -> dict:
    inputs = inputs or {}
    path = inputs.get("path") or "/"
    host_alias = inputs.get("host_alias") or "aions-node-1"
    ex = SSHExecutor(host_alias=host_alias)

    cmd = f"sudo -n du -ahx {shlex.quote(path)} 2>/dev/null | sort -rh | head -n 20"
    res = ex.run(cmd, timeout=90)
    items = _parse_du_sorted(res["stdout"])

    return {
        "ok": res["rc"] == 0,
        "path": path,
        "items": items,
        "count": len(items),
        "error": None if res["rc"] == 0 else res["stderr"],
    }
