"""AIONS Skill Engine — security gate (risk classes) + audit log.

Every skill run passes through here before its handler executes. `classify`
maps a skill's declared `risk` to an access class; unknown or missing risk
is treated as the most restrictive class (fail-closed). `check` decides
whether the run may proceed. `audit` appends one JSON record per run to a
per-node, per-day JSONL log, regardless of the decision.
"""
from __future__ import annotations
import datetime
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
STATE = REPO / "runtime" / "state"
AUDIT_DIR = REPO / "runtime" / "audit"
APPROVALS_FILE = STATE / "approvals.json"

MAPPING = {"low": "read", "medium": "mutate", "high": "destructive"}


def classify(skill_meta: dict) -> str:
    """Map skill_meta['risk'] to an access class.

    Missing or unrecognized risk values fail closed to "destructive" so a
    malformed or unclassified skill can never slip through as low-risk.
    """
    risk = (skill_meta or {}).get("risk")
    return MAPPING.get(risk, "destructive")


def _is_approved(skill_id: str) -> bool:
    if not APPROVALS_FILE.exists():
        return False
    try:
        approvals = json.loads(APPROVALS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return False
    if not isinstance(approvals, list):
        return False
    now = datetime.datetime.now(datetime.timezone.utc)
    for entry in approvals:
        if not isinstance(entry, dict) or entry.get("skill_id") != skill_id:
            continue
        try:
            expires = datetime.datetime.fromisoformat(entry.get("expires", ""))
        except (TypeError, ValueError):
            continue
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=datetime.timezone.utc)
        if expires > now:
            return True
    return False


def check(skill_meta: dict, inputs: dict, node_id: str = "windows-primary") -> dict:
    """Decide whether a skill run may proceed.

    read      -> always allowed
    mutate    -> always allowed, but callers must still audit the run
    destructive -> allowed only with a live (non-expired) approvals.json
                   entry for this skill_id; otherwise blocked
    """
    risk_class = classify(skill_meta)

    if risk_class == "read":
        return {"allowed": True, "decision": "auto", "risk_class": risk_class}

    if risk_class == "mutate":
        return {"allowed": True, "decision": "logged", "risk_class": risk_class}

    # destructive
    skill_id = (skill_meta or {}).get("id", "")
    if _is_approved(skill_id):
        return {"allowed": True, "decision": "logged", "risk_class": risk_class}
    return {"allowed": False, "decision": "approval_required", "risk_class": risk_class}


def audit(entry: dict, node_id: str) -> None:
    """Append one JSON line describing a skill run to the audit log.

    Log file: runtime/audit/<node_id>/<YYYY-MM-DD>.jsonl (created if missing).
    Append-only, utf-8, one JSON object per line. `inputs` is stringified and
    truncated to 500 characters so oversized payloads can't bloat the log.
    """
    ts = entry.get("ts") or datetime.datetime.now(datetime.timezone.utc).isoformat()
    record = dict(entry)
    record["ts"] = ts
    if record.get("inputs") is not None:
        record["inputs"] = str(record["inputs"])[:500]

    day_dir = AUDIT_DIR / node_id
    day_dir.mkdir(parents=True, exist_ok=True)
    log_path = day_dir / f"{ts[:10]}.jsonl"

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
