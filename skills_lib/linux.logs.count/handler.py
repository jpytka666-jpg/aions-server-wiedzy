"""Skill linux.logs.count -- journalctl -p err --since <since> --no-pager | wc -l
(SSH, read-only). Liczy WSZYSTKIE wpisy bledow bez sufitu -n, w odroznieniu od
linux.logs.errors ktory tnie wynik do ostatnich 100 wpisow. Uzywany przez
operator loop do wykrywania log spike (potrzebna dokladna liczba, nie probka).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from runtime.transport.ssh_executor import SSHExecutor  # noqa: E402


def run(inputs: dict, ctx) -> dict:
    inputs = inputs or {}
    since = inputs.get("since") or "10 minutes ago"
    host_alias = inputs.get("host_alias") or "aions-node-1"
    ex = SSHExecutor(host_alias=host_alias)

    safe_since = since.replace("'", "'\\''")  # single-quote escape for the remote shell
    cmd = f"sudo -n journalctl -p err --since '{safe_since}' --no-pager | wc -l"
    res = ex.run(cmd, timeout=30)

    if res["rc"] != 0:
        return {"ok": False, "error": f"journalctl|wc failed rc={res['rc']}: {res['stderr']}",
                "since": since, "count": 0}

    try:
        count = int(res["stdout"].strip())
    except (TypeError, ValueError):
        return {"ok": False, "error": f"could not parse wc -l output: {res['stdout']!r}",
                "since": since, "count": 0}

    return {"ok": True, "since": since, "count": count}
