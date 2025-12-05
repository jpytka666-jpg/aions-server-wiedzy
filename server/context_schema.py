from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

DEFAULT_TTL_DAYS = 30


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt.astimezone(timezone.utc)
        except ValueError:
            pass
    return _now_utc()


@dataclass
class ContextMetadata:
    agent: str = "unknown"
    role: str = "assistant"
    source: str | None = "mcp"
    turn: int | None = None
    tags: List[str] = field(default_factory=list)
    ttl_days: int = DEFAULT_TTL_DAYS
    timestamp: datetime = field(default_factory=_now_utc)
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        expires_at = self.timestamp + timedelta(days=max(1, self.ttl_days))
        payload: Dict[str, Any] = {
            "agent": self.agent,
            "role": self.role,
            "tags": self.tags,
            "ttl_days": self.ttl_days,
            "timestamp": self.timestamp.isoformat().replace("+00:00", "Z"),
            "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
        }
        if self.source is not None:
            payload["source"] = self.source
        if self.turn is not None:
            payload["turn"] = self.turn
        payload.update(self.extra)
        payload = {k: v for k, v in payload.items() if v is not None}
        return payload


def normalize_metadata(raw_meta: Dict[str, Any] | None) -> Dict[str, Any]:
    meta = raw_meta.copy() if raw_meta else {}
    agent = str(meta.pop("agent", None) or "unknown")
    role = str(meta.pop("role", None) or "assistant")
    source = meta.pop("source", None)
    turn = meta.pop("turn", None)
    tags = meta.pop("tags", None) or []
    ttl_days_raw = meta.pop("ttl_days", DEFAULT_TTL_DAYS)
    try:
        ttl_days = int(ttl_days_raw)
    except (TypeError, ValueError):
        ttl_days = DEFAULT_TTL_DAYS
    timestamp = _parse_timestamp(meta.pop("timestamp", None))

    normalized_tags = [str(tag) for tag in tags] if tags else []

    context_meta = ContextMetadata(
        agent=agent,
        role=role,
        source=source,
        turn=turn,
        tags=normalized_tags,
        ttl_days=ttl_days,
        timestamp=timestamp,
        extra=meta,
    )
    payload = context_meta.to_dict()
    if normalized_tags:
        payload["tags"] = ",".join(normalized_tags)
    for key, value in list(payload.items()):
        if isinstance(value, (str, int, float, bool)):
            continue
        if value is None:
            payload.pop(key, None)
        else:
            payload[key] = json.dumps(value, ensure_ascii=False)
    return payload
