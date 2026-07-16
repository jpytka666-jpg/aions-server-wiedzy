from __future__ import annotations

import os
import re
from typing import Any

from .models import Plan, PlanStep, new_plan_id, new_step_id
from .node_registry import get_node, pick_node_for_intent
from .policy import check_intent


def _cbms_lookup(intent: str) -> list[dict[str, Any]]:
    """Best-effort CBMS context via aions_core if available."""
    aions_path = os.environ.get("AIONS_PATH")
    if not aions_path:
        return []
    try:
        import sys
        core_server = os.path.join(aions_path, "server")
        if core_server not in sys.path:
            sys.path.insert(0, core_server)
        from cbms_memory import search_chunks  # type: ignore

        hits = search_chunks(intent, top_k=3)
        return [{"chunk_id": h.get("id"), "title": h.get("title")} for h in hits[:3]]
    except Exception:
        return []


def create_plan(intent: str, node_id: str | None = None) -> Plan:
    ok, msg = check_intent(intent)
    if not ok:
        raise ValueError(msg)

    intent_l = intent.lower()
    steps: list[PlanStep] = []
    target_tool: str | None = None

    if re.search(r"health|status|sprawdz|check", intent_l):
        target_tool = "system_health"
        steps.append(
            PlanStep(new_step_id(), "Run system health check", "system_health", {})
        )
    elif re.search(r"search|szukaj|find|plik", intent_l):
        target_tool = "fast_search"
        steps.append(
            PlanStep(new_step_id(), "Fast file search", "fast_search", {"query": intent})
        )
    elif re.search(r"memory|pamiec|recall", intent_l):
        target_tool = "memory_recall"
        steps.append(
            PlanStep(new_step_id(), "Memory recall", "memory_recall", {"query": intent, "top_k": 3})
        )
    elif re.search(r"cbms|chunk|wiedza", intent_l):
        target_tool = "cbms_search"
        steps.append(
            PlanStep(new_step_id(), "CBMS search", "cbms_search", {"query": intent, "top_k": 3})
        )
    else:
        target_tool = "system_health"
        steps.append(
            PlanStep(new_step_id(), "Default health probe", "system_health", {})
        )

    chosen = get_node(node_id) if node_id else pick_node_for_intent(intent, target_tool)
    chosen_id = chosen.node_id if chosen else None

    return Plan(
        id=new_plan_id(),
        intent=intent,
        steps=steps,
        cbms_context=_cbms_lookup(intent),
        node_id=chosen_id,
    )
