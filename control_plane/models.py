from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
import time
import uuid


@dataclass
class PlanStep:
    id: str
    description: str
    tool: str
    args: dict[str, Any] = field(default_factory=dict)


@dataclass
class Plan:
    id: str
    intent: str
    steps: list[PlanStep]
    cbms_context: list[dict[str, Any]] = field(default_factory=list)
    node_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)


@dataclass
class ExecutionResult:
    step_id: str
    status: str
    output: Any = None
    error: Optional[str] = None
    duration_ms: int = 0


@dataclass
class ExecutionState:
    plan_id: str
    status: str
    results: list[ExecutionResult] = field(default_factory=list)
    current_step: int = 0


def new_plan_id() -> str:
    return f"plan_{uuid.uuid4().hex[:12]}"


def new_step_id() -> str:
    return f"step_{uuid.uuid4().hex[:8]}"
