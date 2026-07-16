"""Proactive scheduler MVP — job queue from operator_profile deadlines + summary events."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class JobKind(str, Enum):
    DAILY_BRIEF = "daily_brief"
    DEADLINE_CHECK = "deadline_check"
    CASE_REMINDER = "case_reminder"


@dataclass
class ScheduledJob:
    id: str
    kind: JobKind
    title: str
    due_at: Optional[str] = None
    payload: dict[str, Any] = field(default_factory=dict)
    priority: str = "normal"


@dataclass
class SchedulerEvent:
    event_type: str
    timestamp: str
    summary: str
    jobs: list[dict[str, Any]] = field(default_factory=list)
    deadlines: list[dict[str, Any]] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class SchedulerSummary:
    generated_at: str
    operator: str
    jobs: list[ScheduledJob]
    events: list[SchedulerEvent]
    profile_path: str
    profile_loaded: bool


def _resolve_aions_path() -> Path:
    env = os.environ.get("AIONS_PATH", "").strip()
    if env:
        return Path(env)
    for candidate in (
        Path(r"E:\server wiedzy\aions_core"),
        Path("/mnt/d/AIONS_DEV/cbms"),
        Path("/mnt/e/server wiedzy/aions_core"),
    ):
        if candidate.exists():
            return candidate
    return Path(r"E:\server wiedzy\aions_core")


def operator_profile_path(aions_path: Path | None = None) -> Path:
    return (aions_path or _resolve_aions_path()) / "memory" / "operator_profile.json"


def load_operator_profile(aions_path: Path | None = None) -> dict[str, Any]:
    path = operator_profile_path(aions_path)
    if not path.is_file():
        return {"loaded": False, "path": str(path), "error": "operator_profile.json not found"}
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    return {"loaded": True, "path": str(path), "profile": data}


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value[:10])
    except (TypeError, ValueError):
        return None


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def collect_deadlines(profile: dict[str, Any], *, horizon_days: int = 14) -> list[dict[str, Any]]:
    """Merge explicit deadlines[] with optional due_date on active_cases."""
    today = date.today()
    horizon = today + timedelta(days=horizon_days)
    seen: set[str] = set()
    items: list[dict[str, Any]] = []

    for entry in profile.get("deadlines") or []:
        if not isinstance(entry, dict):
            continue
        due = _parse_date(str(entry.get("due_date", "")))
        if not due:
            continue
        item_id = str(entry.get("id") or entry.get("title") or due.isoformat())
        if item_id in seen:
            continue
        seen.add(item_id)
        items.append(
            {
                "id": item_id,
                "title": entry.get("title", item_id),
                "due_date": due.isoformat(),
                "days_left": (due - today).days,
                "priority": entry.get("priority", "normal"),
                "case_id": entry.get("case_id"),
                "source": "deadlines",
            }
        )

    for case in profile.get("active_cases") or []:
        if not isinstance(case, dict):
            continue
        due_raw = case.get("due_date")
        if not due_raw:
            continue
        due = _parse_date(str(due_raw))
        if not due:
            continue
        item_id = str(case.get("id") or case.get("title") or due.isoformat())
        if item_id in seen:
            continue
        seen.add(item_id)
        items.append(
            {
                "id": item_id,
                "title": case.get("title", item_id),
                "due_date": due.isoformat(),
                "days_left": (due - today).days,
                "priority": case.get("priority", "normal"),
                "case_id": case.get("id"),
                "status": case.get("status"),
                "source": "active_cases",
            }
        )

    in_window = [d for d in items if today <= _parse_date(d["due_date"]) <= horizon]
    overdue = [d for d in items if d["days_left"] < 0]
    return sorted(overdue + in_window, key=lambda d: (d["days_left"], d["title"]))


def build_job_queue(profile: dict[str, Any]) -> list[ScheduledJob]:
    identity = profile.get("identity") or {}
    operator = identity.get("name", "operator")
    jobs: list[ScheduledJob] = [
        ScheduledJob(
            id="daily_brief_morning",
            kind=JobKind.DAILY_BRIEF,
            title=f"Poranny brief dla {operator}",
            due_at="08:00",
            priority="high",
        )
    ]

    deadlines = collect_deadlines(profile)
    for idx, item in enumerate(deadlines):
        jobs.append(
            ScheduledJob(
                id=f"deadline_{item['id']}",
                kind=JobKind.DEADLINE_CHECK,
                title=item["title"],
                due_at=item["due_date"],
                priority=item.get("priority", "normal"),
                payload=item,
            )
        )

    for case in profile.get("active_cases") or []:
        if not isinstance(case, dict):
            continue
        if case.get("status") not in ("in_progress", "active", "blocked"):
            continue
        case_id = str(case.get("id") or case.get("title"))
        jobs.append(
            ScheduledJob(
                id=f"case_{case_id}",
                kind=JobKind.CASE_REMINDER,
                title=str(case.get("title", case_id)),
                priority="medium",
                payload={"status": case.get("status"), "summary": case.get("summary", "")},
            )
        )

    return jobs


def _audit_dir() -> Path:
    return Path(os.environ.get("AIONS_LOG_DIR", "/tmp")) / "control_plane"


def emit_event(event: SchedulerEvent) -> None:
    try:
        log_dir = _audit_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        log = log_dir / "scheduler_events.jsonl"
        with log.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")
    except OSError:
        pass


def run_scheduler(*, emit: bool = True, horizon_days: int = 14) -> SchedulerSummary:
    loaded = load_operator_profile()
    profile = loaded.get("profile") or {}
    identity = profile.get("identity") or {}
    operator = identity.get("name", "operator")
    jobs = build_job_queue(profile) if loaded.get("loaded") else []
    deadlines = collect_deadlines(profile, horizon_days=horizon_days) if loaded.get("loaded") else []

    urgent = [d for d in deadlines if d["days_left"] <= 3]
    active_cases = [
        c for c in (profile.get("active_cases") or [])
        if isinstance(c, dict) and c.get("status") in ("in_progress", "active", "blocked")
    ]
    summary_parts = [
        f"{len(jobs)} zadań w kolejce",
        f"{len(deadlines)} terminów w horyzoncie {horizon_days}d",
        f"{len(urgent)} pilnych terminów",
        f"{len(active_cases)} aktywnych spraw",
    ]

    events: list[SchedulerEvent] = [
        SchedulerEvent(
            event_type="scheduler_summary",
            timestamp=_now_iso(),
            summary="; ".join(summary_parts),
            jobs=[_job_to_dict(j) for j in jobs],
            deadlines=deadlines,
            meta={
                "operator": operator,
                "profile_loaded": loaded.get("loaded", False),
                "profile_path": loaded.get("path", ""),
            },
        )
    ]

    if urgent:
        events.append(
            SchedulerEvent(
                event_type="deadline_alert",
                timestamp=_now_iso(),
                summary=f"{len(urgent)} terminów wymaga uwagi w ciągu 3 dni",
                deadlines=urgent,
                meta={"operator": operator},
            )
        )

    if emit:
        for event in events:
            emit_event(event)

    return SchedulerSummary(
        generated_at=_now_iso(),
        operator=operator,
        jobs=jobs,
        events=events,
        profile_path=str(loaded.get("path", "")),
        profile_loaded=bool(loaded.get("loaded")),
    )


def _job_to_dict(job: ScheduledJob) -> dict[str, Any]:
    return {
        "id": job.id,
        "kind": job.kind.value,
        "title": job.title,
        "due_at": job.due_at,
        "payload": job.payload,
        "priority": job.priority,
    }


def summary_to_dict(summary: SchedulerSummary) -> dict[str, Any]:
    return {
        "generated_at": summary.generated_at,
        "operator": summary.operator,
        "profile_loaded": summary.profile_loaded,
        "profile_path": summary.profile_path,
        "jobs": [_job_to_dict(j) for j in summary.jobs],
        "events": [asdict(e) for e in summary.events],
    }
