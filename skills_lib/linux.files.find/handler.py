"""Skill linux.files.find — find <path> -maxdepth <depth> -name <name> (SSH, read-only)."""
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
        return {"ok": False, "error": "missing required input: name"}
    path = inputs.get("path") or "/"
    depth = int(inputs.get("depth") or 4)
    host_alias = inputs.get("host_alias") or "aions-node-1"
    ex = SSHExecutor(host_alias=host_alias)

    cmd = f"find {shlex.quote(path)} -maxdepth {depth} -name {shlex.quote(name)} 2>/dev/null"
    res = ex.run(cmd, timeout=60)
    # find returns rc=1 when it hit permission-denied dirs even though
    # the (partial) results on stdout are still valid — only rc>1 is a hard error.
    ok = res["rc"] in (0, 1)
    paths = [ln.strip() for ln in res["stdout"].strip().splitlines() if ln.strip()] if ok else []

    return {
        "ok": ok,
        "path": path,
        "name": name,
        "depth": depth,
        "paths": paths,
        "count": len(paths),
        "error": None if ok else res["stderr"],
    }
