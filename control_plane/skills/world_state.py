"""AIONS Skill Engine — world state (swiadomosc stanu swiata).

A tiny live model of the world so skills do not repeat actions. Skills read and
update it; the planner uses it to skip actions that are already satisfied or that
must be avoided under current conditions.
"""
from __future__ import annotations
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
STATE_PATH = REPO / "runtime" / "state" / "world_state.json"

_DEFAULT = {
    "browser": "unknown",
    "moodle": "logged_out",
    "notepad": "closed",
    "git_repo": "unknown",
    "docker": "unknown",
    "wsl": "unknown",
    "internet": "unknown",
    "vpn": "unknown",
}

_FALSY = {"unknown", "closed", "logged_out", "off", "false", "down", "no"}


def load() -> dict:
    if STATE_PATH.exists():
        try:
            return {**_DEFAULT, **json.loads(STATE_PATH.read_text(encoding="utf-8"))}
        except Exception:
            return dict(_DEFAULT)
    return dict(_DEFAULT)


def save(d: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def get(key: str, default=None):
    return load().get(key, default)


def set(key: str, value) -> dict:
    d = load()
    d[key] = value
    save(d)
    return d


def matches(condition: str) -> bool:
    """Evaluate a condition against current world state.

    Supports 'key==value', 'key!=value', or a bare 'key' (truthy check).
    """
    d = load()
    for op in ("==", "!="):
        if op in condition:
            k, v = [x.strip() for x in condition.split(op, 1)]
            cur = str(d.get(k, "unknown"))
            return (cur == v) if op == "==" else (cur != v)
    return str(d.get(condition.strip(), "unknown")).lower() not in _FALSY
