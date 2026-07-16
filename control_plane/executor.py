from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Callable

from .models import ExecutionResult, ExecutionState, Plan
from .node_dispatch import dispatch_step_to_node
from .node_registry import get_node
from .policy import evaluate_tool

_PLANS: dict[str, Plan] = {}
_EXECUTIONS: dict[str, ExecutionState] = {}
_AUDIT_DIR = Path(os.environ.get("AIONS_LOG_DIR", "/tmp")) / "control_plane"


def _audit(event: dict[str, Any]) -> None:
    try:
        _AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        log = _AUDIT_DIR / "execution_audit.jsonl"
        with log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError:
        pass


def store_plan(plan: Plan) -> Plan:
    _PLANS[plan.id] = plan
    _EXECUTIONS[plan.id] = ExecutionState(plan_id=plan.id, status="pending")
    return plan


def get_plan(plan_id: str) -> Plan | None:
    return _PLANS.get(plan_id)


def get_execution(plan_id: str) -> ExecutionState | None:
    return _EXECUTIONS.get(plan_id)


def execute_step(
    plan_id: str,
    step_id: str,
    tool_runner: Callable[[str, dict[str, Any]], Any],
) -> ExecutionResult:
    plan = _PLANS.get(plan_id)
    state = _EXECUTIONS.get(plan_id)
    if not plan or not state:
        raise KeyError(f"unknown plan: {plan_id}")

    step = next((s for s in plan.steps if s.id == step_id), None)
    if not step:
        raise KeyError(f"unknown step: {step_id}")

    allowed, reason = evaluate_tool(step.tool)
    if not allowed:
        result = ExecutionResult(step_id=step_id, status="denied", error=reason)
        state.results.append(result)
        state.status = "failed"
        return result

    node_id = plan.node_id
    if node_id:
        node = get_node(node_id)
        if node and node.health not in ("ok", "degraded"):
            result = ExecutionResult(
                step_id=step_id,
                status="denied",
                error=f"node unhealthy: {node_id} ({node.health})",
            )
            state.results.append(result)
            state.status = "failed"
            return result
        if node and step.tool not in node.tools and step.tool not in ("aions_plan", "aions_execute_step"):
            result = ExecutionResult(
                step_id=step_id,
                status="denied",
                error=f"tool {step.tool!r} not on node {node_id}",
            )
            state.results.append(result)
            state.status = "failed"
            return result

    t0 = time.time()
    try:
        if node_id:
            disp = dispatch_step_to_node(
                node_id,
                step.tool,
                step.args,
                local_runner=tool_runner,
            )
            if disp.get("mode") == "remote" and disp.get("status") == "stub":
                ms = int((time.time() - t0) * 1000)
                result = ExecutionResult(
                    step_id=step_id,
                    status="stub",
                    output=disp,
                    duration_ms=ms,
                )
                state.results.append(result)
                state.status = "failed"
                _audit(
                    {
                        "plan_id": plan_id,
                        "step_id": step_id,
                        "node_id": node_id,
                        "tool": step.tool,
                        "status": "stub",
                        "target": disp.get("target_url"),
                    }
                )
                return result
            output = disp.get("output")
        else:
            output = tool_runner(step.tool, step.args)
        ms = int((time.time() - t0) * 1000)
        result = ExecutionResult(step_id=step_id, status="ok", output=output, duration_ms=ms)
        state.results.append(result)
        state.current_step += 1
        state.status = "completed" if state.current_step >= len(plan.steps) else "running"
        _audit({"plan_id": plan_id, "step_id": step_id, "node_id": node_id, "tool": step.tool, "status": "ok", "ms": ms})
        return result
    except Exception as exc:
        ms = int((time.time() - t0) * 1000)
        result = ExecutionResult(step_id=step_id, status="error", error=str(exc), duration_ms=ms)
        state.results.append(result)
        state.status = "failed"
        _audit({"plan_id": plan_id, "step_id": step_id, "node_id": node_id, "tool": step.tool, "status": "error", "error": str(exc)})
        return result
