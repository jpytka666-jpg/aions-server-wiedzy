#!/usr/bin/env python3
"""
AIONS sessionStart hook — inject recent auto-log entries into agent context.

Reads logs/conversation_dumps/autolog_YYYY-MM-DD.jsonl (today, then yesterday)
and returns Cursor hook JSON with additional_context.
Stdlib only; no MCP/Chroma dependency.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[2]
DUMPS_DIR = REPO_ROOT / "logs" / "conversation_dumps"
DEFAULT_LIMIT = 20


def _today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _date_str(offset_days: int) -> str:
    return (datetime.now() - timedelta(days=offset_days)).strftime("%Y-%m-%d")


def _read_autolog_file(date: str) -> List[Dict[str, Any]]:
    dump_file = DUMPS_DIR / f"autolog_{date}.jsonl"
    if not dump_file.exists():
        return []
    entries: List[Dict[str, Any]] = []
    try:
        with open(dump_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return entries


def _collect_entries(limit: int = DEFAULT_LIMIT) -> tuple[List[Dict[str, Any]], List[str]]:
    """Return (entries, dates_used) newest-last within limit."""
    dates = [_today_str(), _date_str(1)]
    combined: List[Dict[str, Any]] = []
    used: List[str] = []

    for date in dates:
        day_entries = _read_autolog_file(date)
        if day_entries:
            used.append(date)
            combined.extend(day_entries)

    if len(combined) > limit:
        combined = combined[-limit:]
    return combined, used


def _format_entry(entry: Dict[str, Any]) -> str:
    ts = str(entry.get("timestamp", ""))[:19]
    tool = entry.get("tool", "?")
    args = entry.get("args", "")
    result = str(entry.get("result", ""))[:200]
    return f"[{ts}] {tool}({args})\n  -> {result}"


def build_context(limit: int = DEFAULT_LIMIT) -> str:
    entries, dates = _collect_entries(limit)
    if not entries:
        return (
            "## AIONS Auto-Log (sessionStart hook)\n"
            "Brak wpisów auto-log na dziś/wczoraj. "
            "Użyj `session_bootstrap()` lub `conv_history()` jeśli potrzebujesz kontekstu.\n"
        )

    lines = [
        "## AIONS Auto-Log (sessionStart hook — auto-wstrzyknięte)",
        f"Ostatnie {len(entries)} wpisów narzędzi z: {', '.join(dates)}.",
        "Pełny tekst rozmowy NIE jest tu — tylko wywołania MCP. "
        "Przy długiej przerwie użyj `conv_history()`.",
        "",
    ]
    lines.extend(_format_entry(e) for e in entries)
    return "\n".join(lines)


def main() -> int:
    try:
        raw = sys.stdin.read()
        if raw.strip():
            json.loads(raw)  # validate hook input; fields unused for now
    except json.JSONDecodeError:
        pass

    context = build_context(DEFAULT_LIMIT)
    payload = {
        "env": {
            "AIONS_REPO_ROOT": str(REPO_ROOT),
            "AIONS_AUTOLOG_HOOK": "1",
        },
        "additional_context": context,
    }
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
