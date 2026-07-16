"""Skill linux.files.read — head -n <max_lines> <path> (SSH, read-only)."""
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
    path = inputs.get("path")
    if not path:
        return {"ok": False, "error": "missing required input: path"}
    max_lines = int(inputs.get("max_lines") or 100)
    host_alias = inputs.get("host_alias") or "aions-node-1"
    ex = SSHExecutor(host_alias=host_alias)

    head_res = ex.run(f"head -n {max_lines} {shlex.quote(path)}", timeout=20)
    if head_res["rc"] != 0:
        return {"ok": False, "error": f"read failed rc={head_res['rc']}: {head_res['stderr']}",
                "path": path, "content": "", "truncated": False}

    wc_res = ex.run(f"wc -l < {shlex.quote(path)}", timeout=20)
    total_lines = None
    if wc_res["rc"] == 0:
        try:
            total_lines = int(wc_res["stdout"].strip())
        except ValueError:
            total_lines = None

    content = head_res["stdout"]
    truncated = bool(total_lines is not None and total_lines > max_lines)

    return {
        "ok": True,
        "path": path,
        "content": content,
        "max_lines": max_lines,
        "total_lines": total_lines,
        "truncated": truncated,
    }
