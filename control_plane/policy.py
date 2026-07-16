from __future__ import annotations

from typing import Any

ALLOWED_TOOLS = frozenset({
    "system_health",
    "cbms_search",
    "memory_recall",
    "fast_search",
    "aions_plan",
    "aions_execute_step",
    "aions_execution_status",
})


def evaluate_tool(tool: str, context: dict[str, Any] | None = None) -> tuple[bool, str]:
    """Policy gate before execution."""
    if tool not in ALLOWED_TOOLS:
        return False, f"tool not allowed: {tool}"
    return True, "ok"


def check_intent(intent: str) -> tuple[bool, str]:
    blocked = ("rm -rf /", "format c:", "delete all")
    lower = intent.lower()
    for b in blocked:
        if b in lower:
            return False, "blocked intent pattern"
    return True, "ok"
