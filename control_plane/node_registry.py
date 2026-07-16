"""In-memory node registry with optional JSON persistence (Faza 6 MVP).

Nodes are abstract worker resources — capabilities, health, load, permissions.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

_DEFAULT_STATE_DIR = Path(__file__).resolve().parents[1] / "runtime" / "state"
STATE_DIR = Path(os.environ.get("AIONS_STATE_DIR", str(_DEFAULT_STATE_DIR)))
REGISTRY_FILE = STATE_DIR / "node_registry.json"

HEARTBEAT_STALE_SEC = int(os.environ.get("AIONS_NODE_STALE_SEC", "300"))


@dataclass
class NodeRecord:
    node_id: str
    host: str
    capabilities: list[str] = field(default_factory=list)
    memory_mb: int = 0
    tools: list[str] = field(default_factory=list)
    health: str = "unknown"
    load: float = 0.0
    permissions: list[str] = field(default_factory=list)
    registered_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NodeRecord:
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in known})


_REGISTRY: dict[str, NodeRecord] = {}
_loaded = False


def _ensure_loaded() -> None:
    global _loaded
    if _loaded:
        return
    _load_from_disk()
    if not _REGISTRY:
        _seed_default_local_node()
    _loaded = True


def _load_from_disk() -> None:
    if not REGISTRY_FILE.is_file():
        return
    try:
        raw = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
        nodes = raw.get("nodes") if isinstance(raw, dict) else raw
        if not isinstance(nodes, list):
            return
        for item in nodes:
            if isinstance(item, dict) and item.get("node_id"):
                rec = NodeRecord.from_dict(item)
                _REGISTRY[rec.node_id] = rec
    except (OSError, json.JSONDecodeError, TypeError):
        pass


def _save_to_disk() -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "updated_at": time.time(),
            "nodes": [n.to_dict() for n in _REGISTRY.values()],
        }
        REGISTRY_FILE.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError:
        pass


def _seed_default_local_node() -> None:
    """Register local dev node when registry is empty."""
    import platform

    host = platform.node() or "localhost"
    is_win = platform.system().lower() == "windows"
    node_id = "windows-primary" if is_win else "linux-primary"
    caps = ["mcp", "cbms", "chroma", "desktop"] if is_win else ["mcp", "cbms", "chroma", "shell"]
    tools = [
        "system_health",
        "fast_search",
        "memory_recall",
        "cbms_search",
        "aions_plan",
        "aions_execute_step",
    ]
    rec = NodeRecord(
        node_id=node_id,
        host=host,
        capabilities=caps,
        memory_mb=8192,
        tools=tools,
        health="ok",
        load=0.0,
        permissions=["local", "read", "execute"],
    )
    _REGISTRY[node_id] = rec
    _save_to_disk()


def register_node(
    *,
    node_id: str | None = None,
    host: str,
    capabilities: list[str] | None = None,
    memory_mb: int = 0,
    tools: list[str] | None = None,
    health: str = "ok",
    load: float = 0.0,
    permissions: list[str] | None = None,
    persist: bool = True,
) -> NodeRecord:
    _ensure_loaded()
    nid = node_id or f"node_{uuid.uuid4().hex[:12]}"
    now = time.time()
    existing = _REGISTRY.get(nid)
    rec = NodeRecord(
        node_id=nid,
        host=host,
        capabilities=list(capabilities or []),
        memory_mb=memory_mb,
        tools=list(tools or []),
        health=health,
        load=max(0.0, min(1.0, load)),
        permissions=list(permissions or ["execute"]),
        registered_at=existing.registered_at if existing else now,
        last_heartbeat=now,
    )
    _REGISTRY[nid] = rec
    if persist:
        _save_to_disk()
    return rec


def list_nodes(*, healthy_only: bool = False) -> list[NodeRecord]:
    _ensure_loaded()
    nodes = list(_REGISTRY.values())
    if healthy_only:
        nodes = [n for n in nodes if n.health == "ok" and not _is_stale(n)]
    return sorted(nodes, key=lambda n: n.node_id)


def get_node(node_id: str) -> NodeRecord | None:
    _ensure_loaded()
    return _REGISTRY.get(node_id)


def heartbeat(
    node_id: str,
    *,
    health: str | None = None,
    load: float | None = None,
    persist: bool = True,
) -> NodeRecord:
    _ensure_loaded()
    rec = _REGISTRY.get(node_id)
    if not rec:
        raise KeyError(f"unknown node: {node_id}")
    rec.last_heartbeat = time.time()
    if health is not None:
        rec.health = health
    if load is not None:
        rec.load = max(0.0, min(1.0, load))
    if persist:
        _save_to_disk()
    return rec


def _is_stale(rec: NodeRecord) -> bool:
    return (time.time() - rec.last_heartbeat) > HEARTBEAT_STALE_SEC


def pick_node_for_intent(intent: str, required_tool: str | None = None) -> NodeRecord | None:
    """Best-effort node selection for planner/executor."""
    _ensure_loaded()
    candidates = list_nodes(healthy_only=True)
    if not candidates:
        candidates = list_nodes()
    if not candidates:
        return None
    if required_tool:
        with_tool = [n for n in candidates if required_tool in n.tools]
        if with_tool:
            candidates = with_tool
    intent_l = intent.lower()
    if any(k in intent_l for k in ("desktop", "gui", "windows")):
        desktop = [n for n in candidates if "desktop" in n.capabilities]
        if desktop:
            candidates = desktop
    return min(candidates, key=lambda n: n.load)


def registry_summary() -> dict[str, Any]:
    _ensure_loaded()
    nodes = list_nodes()
    return {
        "count": len(nodes),
        "healthy": sum(1 for n in nodes if n.health == "ok" and not _is_stale(n)),
        "state_file": str(REGISTRY_FILE),
        "nodes": [n.to_dict() for n in nodes],
    }
