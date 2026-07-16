"""Skill linux.files.list — ls -la <path> (SSH, read-only)."""
from __future__ import annotations

import re
import shlex
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from runtime.transport.ssh_executor import SSHExecutor  # noqa: E402


LS_RE = re.compile(
    r'^([\-dlbcps][rwxXsStT\-]{9}[+.]?)\s+(\d+)\s+(\S+)\s+(\S+)\s+(\d+)\s+'
    r'(\w{3}\s+\d{1,2}\s+(?:\d{2}:\d{2}|\d{4}))\s+(.*)$'
)


def _parse_ls(text: str) -> list:
    items = []
    for line in text.strip().splitlines():
        line = line.rstrip()
        if not line or line.startswith("total "):
            continue
        m = LS_RE.match(line)
        if not m:
            continue
        perms, links, owner, group, size, mtime, name = m.groups()
        items.append({
            "name": name,
            "size": int(size),
            "perms": perms,
            "owner": owner,
            "mtime": mtime,
            "is_dir": perms.startswith("d"),
        })
    return items


def run(inputs: dict, ctx) -> dict:
    inputs = inputs or {}
    path = inputs.get("path") or "/home"
    host_alias = inputs.get("host_alias") or "aions-node-1"
    ex = SSHExecutor(host_alias=host_alias)

    cmd = f"ls -la {shlex.quote(path)}"
    res = ex.run(cmd, timeout=20)
    if res["rc"] != 0:
        return {"ok": False, "error": f"ls failed rc={res['rc']}: {res['stderr']}",
                "path": path, "items": []}

    items = _parse_ls(res["stdout"])
    return {"ok": True, "path": path, "items": items, "count": len(items), "raw": res["stdout"]}
