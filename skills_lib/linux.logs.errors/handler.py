"""Skill linux.logs.errors — journalctl -p err --since <since> --no-pager -n 100
(SSH, read-only)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from runtime.transport.ssh_executor import SSHExecutor  # noqa: E402

_LINE_RE = re.compile(
    r"^(?P<ts>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(?P<host>\S+)\s+(?P<proc>[^:]+):\s?(?P<msg>.*)$"
)


def _parse_journal(text: str) -> list:
    entries = []
    for line in text.strip().splitlines():
        if not line.strip():
            continue
        m = _LINE_RE.match(line)
        if m:
            entries.append({
                "timestamp": m.group("ts"),
                "host": m.group("host"),
                "process": m.group("proc").strip(),
                "message": m.group("msg").strip(),
            })
        else:
            entries.append({"raw": line})
    return entries


def run(inputs: dict, ctx) -> dict:
    inputs = inputs or {}
    since = inputs.get("since") or "1 hour ago"
    host_alias = inputs.get("host_alias") or "aions-node-1"
    ex = SSHExecutor(host_alias=host_alias)

    safe_since = since.replace("'", "'\\''")  # single-quote escape for the remote shell
    cmd = f"sudo -n journalctl -p err --since '{safe_since}' --no-pager -n 100"
    res = ex.run(cmd, timeout=30)

    if res["rc"] != 0:
        return {"ok": False, "error": f"journalctl failed rc={res['rc']}: {res['stderr']}",
                "since": since, "entries": [], "count": 0}

    entries = _parse_journal(res["stdout"])
    return {"ok": True, "since": since, "count": len(entries), "entries": entries}
