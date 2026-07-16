"""AIONS Skill Engine — multi-dimensional telemetry & ranking.

Not just success/(success+failed). We also track speed so a fast 97% skill can be
preferred over a slow 99% one for simple tasks.
"""
from __future__ import annotations
import datetime
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
STATS_PATH = REPO / "runtime" / "state" / "skill_stats.json"


def _load():
    if STATS_PATH.exists():
        try:
            return json.loads(STATS_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save(d):
    STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATS_PATH.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def record(oid, success, ms, risk="low"):
    d = _load()
    e = d.get(oid, {"success": 0, "failed": 0, "avg_ms": 0})
    n_prev = e["success"] + e["failed"]
    e["success" if success else "failed"] += 1
    n = e["success"] + e["failed"]
    e["avg_ms"] = int((e["avg_ms"] * n_prev + ms) / max(n, 1))
    e["success_rate"] = round(e["success"] / max(n, 1), 3)
    e["risk"] = risk
    if success:
        e["last_ok"] = datetime.datetime.utcnow().isoformat() + "Z"
    speed = 1.0 / (1.0 + e["avg_ms"] / 1000.0)          # 1.0 fast -> ~0 slow
    e["confidence"] = round(0.8 * e["success_rate"] + 0.2 * speed, 3)
    d[oid] = e
    _save(d)
    return e


def get(oid):
    return _load().get(oid, {"success": 0, "failed": 0, "success_rate": 0.0,
                             "confidence": 0.0, "avg_ms": 0})


def rank(oid, prefer="balanced"):
    """Weighted score used to choose between competing objects.
    prefer: 'fast' | 'reliable' | 'balanced'."""
    e = get(oid)
    sr = e.get("success_rate", 0.0)
    speed = 1.0 / (1.0 + e.get("avg_ms", 0) / 1000.0)
    if prefer == "fast":
        return round(0.4 * sr + 0.6 * speed, 3)
    if prefer == "reliable":
        return round(0.9 * sr + 0.1 * speed, 3)
    return round(0.7 * sr + 0.3 * speed, 3)
