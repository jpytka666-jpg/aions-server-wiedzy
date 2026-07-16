"""Skill linux.users.sessions — who / last -n 10 (SSH, read-only)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from runtime.transport.ssh_executor import SSHExecutor  # noqa: E402


WHO_RE = re.compile(r'^(\S+)\s+(\S+)\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})(?:\s+\(([^)]+)\))?')


def _parse_who(text: str) -> list:
    items = []
    for line in text.strip().splitlines():
        m = WHO_RE.match(line.strip())
        if not m:
            continue
        user, tty, dt, ip = m.groups()
        items.append({"user": user, "tty": tty, "datetime": dt, "from": ip})
    return items


def _parse_last(text: str) -> list:
    items = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("wtmp begins"):
            continue
        parts = line.split(None, 2)
        if len(parts) < 2:
            continue
        user, tty = parts[0], parts[1]
        rest = parts[2] if len(parts) > 2 else ""
        items.append({"user": user, "tty": tty, "detail": rest})
    return items


def run(inputs: dict, ctx) -> dict:
    inputs = inputs or {}
    host_alias = inputs.get("host_alias") or "aions-node-1"
    ex = SSHExecutor(host_alias=host_alias)

    who_res = ex.run("who", timeout=15)
    last_res = ex.run("last -n 10", timeout=15)

    logged_in = _parse_who(who_res["stdout"]) if who_res["rc"] == 0 else []
    recent = _parse_last(last_res["stdout"]) if last_res["rc"] == 0 else []

    ok = who_res["rc"] == 0 and last_res["rc"] == 0
    return {
        "ok": ok,
        "logged_in": logged_in,
        "recent": recent,
        "error": None if ok else f"who_rc={who_res['rc']} last_rc={last_res['rc']}",
    }
