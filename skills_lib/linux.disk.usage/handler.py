"""Skill linux.disk.usage — df -h + top 10 largest top-level dirs in / (SSH, read-only)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from runtime.transport.ssh_executor import SSHExecutor  # noqa: E402


def _parse_df(text: str) -> list:
    lines = [ln for ln in text.strip().splitlines() if ln.strip()]
    if not lines:
        return []
    rows = []
    for line in lines[1:]:
        parts = line.split()
        if len(parts) < 6:
            continue
        rows.append({
            "filesystem": parts[0],
            "size": parts[1],
            "used": parts[2],
            "avail": parts[3],
            "use_pct": parts[4],
            "mounted_on": " ".join(parts[5:]),
        })
    return rows


def _parse_du(text: str) -> list:
    rows = []
    for line in text.strip().splitlines():
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        size, path = parts
        rows.append({"size": size, "path": path.strip()})
    return rows


def run(inputs: dict, ctx) -> dict:
    inputs = inputs or {}
    host_alias = inputs.get("host_alias") or "aions-node-1"
    ex = SSHExecutor(host_alias=host_alias)

    df_res = ex.run("df -h", timeout=30)
    if df_res["rc"] != 0:
        return {"ok": False, "error": f"df failed rc={df_res['rc']}: {df_res['stderr']}",
                "filesystems": [], "top_dirs": []}

    du_cmd = "sudo -n du -xh --max-depth=1 / 2>/dev/null | sort -rh | head -n 10"
    du_res = ex.run(du_cmd, timeout=60)

    filesystems = _parse_df(df_res["stdout"])
    top_dirs = _parse_du(du_res["stdout"]) if du_res["rc"] == 0 else []

    return {
        "ok": True,
        "filesystems": filesystems,
        "top_dirs": top_dirs,
        "du_error": None if du_res["rc"] == 0 else du_res["stderr"],
    }
