"""Skill linux.files.search — grep -rn <pattern> <path> --include=<glob> (SSH, read-only)."""
from __future__ import annotations

import shlex
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from runtime.transport.ssh_executor import SSHExecutor  # noqa: E402


def _parse_matches(text: str) -> list:
    items = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        count, path_ = parts
        try:
            count = int(count)
        except ValueError:
            continue
        items.append({"file": path_, "count": count})
    return items


def run(inputs: dict, ctx) -> dict:
    inputs = inputs or {}
    pattern = inputs.get("pattern")
    if not pattern:
        return {"ok": False, "error": "missing required input: pattern"}
    path = inputs.get("path") or "/"
    glob = inputs.get("glob") or "*"
    host_alias = inputs.get("host_alias") or "aions-node-1"
    ex = SSHExecutor(host_alias=host_alias)

    cmd = (
        f"grep -rn {shlex.quote(pattern)} {shlex.quote(path)} "
        f"--include={shlex.quote(glob)} 2>/dev/null | cut -d: -f1 | sort | uniq -c | sort -rn"
    )
    res = ex.run(cmd, timeout=60)
    matches = _parse_matches(res["stdout"]) if res["rc"] == 0 else []

    return {
        "ok": res["rc"] == 0,
        "pattern": pattern,
        "path": path,
        "glob": glob,
        "matches": matches,
        "files_matched": len(matches),
        "error": None if res["rc"] == 0 else res["stderr"],
    }
