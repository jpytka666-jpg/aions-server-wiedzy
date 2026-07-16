#!/usr/bin/env python3
"""Poranny brief operatora — profil + opcjonalny health (Fala 6 scheduler MVP)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from control_plane.scheduler import (  # noqa: E402
    collect_deadlines,
    load_operator_profile,
    run_scheduler,
    summary_to_dict,
)


def _light_health(repo_root: Path) -> dict[str, Any]:
    checks: dict[str, Any] = {"status": "ok", "checks": []}

    python_env = repo_root / ".aions" / "python.env"
    checks["checks"].append(
        {"name": "python.env", "ok": python_env.is_file(), "path": str(python_env)}
    )

    aions_path = os.environ.get("AIONS_PATH", r"E:\server wiedzy\aions_core")
    aions_dir = Path(aions_path)
    checks["checks"].append(
        {"name": "aions_path", "ok": aions_dir.is_dir(), "path": str(aions_dir)}
    )

    profile_path = aions_dir / "memory" / "operator_profile.json"
    checks["checks"].append(
        {"name": "operator_profile", "ok": profile_path.is_file(), "path": str(profile_path)}
    )

    if not all(c["ok"] for c in checks["checks"]):
        checks["status"] = "degraded"
    return checks


def _status_label_pl(status: str) -> str:
    mapping = {
        "completed": "zakończone",
        "in_progress": "w toku",
        "active": "aktywne",
        "blocked": "zablokowane",
    }
    return mapping.get(status, status)


def _priority_label_pl(priority: str) -> str:
    mapping = {"high": "wysoki", "medium": "średni", "normal": "normalny", "low": "niski"}
    return mapping.get(priority, priority)


def format_brief(
    *,
    with_health: bool = False,
    horizon_days: int = 7,
    emit_scheduler: bool = False,
) -> str:
    loaded = load_operator_profile()
    profile = loaded.get("profile") or {}
    identity = profile.get("identity") or {}
    name = identity.get("name", "operator")
    now = datetime.now().astimezone()
    lines: list[str] = [
        f"=== AIONS — poranny brief ({now.strftime('%Y-%m-%d %H:%M')}) ===",
        f"Cześć, {name}.",
        "",
    ]

    if not loaded.get("loaded"):
        lines.extend(
            [
                f"⚠ Nie wczytano profilu operatora ({loaded.get('path', '?')}).",
                f"   Błąd: {loaded.get('error', 'nieznany')}",
                "",
            ]
        )
    else:
        active_cases = [
            c
            for c in (profile.get("active_cases") or [])
            if isinstance(c, dict) and c.get("status") != "completed"
        ]
        lines.append("Aktywne sprawy:")
        if active_cases:
            for case in active_cases:
                status = _status_label_pl(str(case.get("status", "?")))
                title = case.get("title", case.get("id", "?"))
                summary = case.get("summary", "")
                lines.append(f"  • [{status}] {title}")
                if summary:
                    lines.append(f"    {summary}")
        else:
            lines.append("  (brak otwartych spraw)")
        lines.append("")

        deadlines = collect_deadlines(profile, horizon_days=horizon_days)
        lines.append(f"Terminy (najbliższe {horizon_days} dni):")
        if deadlines:
            for item in deadlines:
                days = item["days_left"]
                if days < 0:
                    when = f"po terminie ({abs(days)} dni)"
                elif days == 0:
                    when = "dziś"
                elif days == 1:
                    when = "jutro"
                else:
                    when = f"za {days} dni"
                lines.append(f"  • {item['title']} — {item['due_date']} ({when})")
        else:
            lines.append("  (brak zdefiniowanych terminów w profilu)")
        lines.append("")

        goals = profile.get("goals") or []
        if goals:
            lines.append("Cele:")
            for goal in goals:
                if not isinstance(goal, dict):
                    continue
                prio = _priority_label_pl(str(goal.get("priority", "normal")))
                title = goal.get("title", goal.get("id", "?"))
                desc = goal.get("description", "")
                lines.append(f"  • [{prio}] {title}")
                if desc:
                    lines.append(f"    {desc}")
            lines.append("")

        decisions = profile.get("decisions") or []
        if decisions:
            latest = decisions[-1]
            if isinstance(latest, dict):
                lines.append("Ostatnia decyzja:")
                lines.append(
                    f"  • {latest.get('date', '?')}: {latest.get('topic', '?')} — {latest.get('decision', '')}"
                )
                lines.append("")

    if with_health:
        health = _light_health(ROOT)
        status = "OK" if health["status"] == "ok" else "DEGRADED"
        lines.append(f"Zdrowie systemu: {status}")
        for check in health["checks"]:
            mark = "✓" if check["ok"] else "✗"
            lines.append(f"  {mark} {check['name']}")
        lines.append("")

    if emit_scheduler:
        summary = run_scheduler(emit=True, horizon_days=horizon_days)
        lines.append(
            f"Scheduler: {len(summary.jobs)} zadań, zdarzenia zapisane w AIONS_LOG_DIR/control_plane/"
        )
        lines.append("")

    lines.append("— AIONS proactive scheduler MVP —")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Poranny brief operatora AIONS (profil + opcjonalny health).")
    parser.add_argument("--health", action="store_true", help="Dołącz lekki health check środowiska.")
    parser.add_argument("--horizon", type=int, default=7, help="Horyzont terminów w dniach (domyślnie 7).")
    parser.add_argument("--emit-scheduler", action="store_true", help="Uruchom scheduler i zapisz zdarzenia JSONL.")
    parser.add_argument("--json", action="store_true", help="Wypisz JSON zamiast tekstu.")
    args = parser.parse_args()

    if args.json:
        loaded = load_operator_profile()
        payload = {
            "brief": format_brief(
                with_health=args.health,
                horizon_days=args.horizon,
                emit_scheduler=args.emit_scheduler,
            ),
            "profile": loaded,
            "scheduler": summary_to_dict(run_scheduler(emit=args.emit_scheduler, horizon_days=args.horizon))
            if loaded.get("loaded")
            else None,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(
            format_brief(
                with_health=args.health,
                horizon_days=args.horizon,
                emit_scheduler=args.emit_scheduler,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
