from __future__ import annotations

from typing import Any, Callable, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .executor import execute_step, get_execution, get_plan, store_plan
from .node_dispatch import dispatch_step_to_node
from .node_registry import heartbeat, list_nodes, register_node, registry_summary, get_node
from .planner import create_plan
from .scheduler import run_scheduler, summary_to_dict

router = APIRouter(tags=["control-plane"])


class PlanRequest(BaseModel):
    intent: str = Field(..., min_length=1)


class ExecuteRequest(BaseModel):
    plan_id: str
    step_id: str


class NodeRegisterRequest(BaseModel):
    node_id: str | None = None
    host: str = Field(..., min_length=1)
    capabilities: list[str] = Field(default_factory=list)
    memory_mb: int = Field(default=0, ge=0)
    tools: list[str] = Field(default_factory=list)
    health: str = Field(default="ok")
    load: float = Field(default=0.0, ge=0.0, le=1.0)
    permissions: list[str] = Field(default_factory=list)


class NodeHeartbeatRequest(BaseModel):
    health: str | None = None
    load: float | None = Field(default=None, ge=0.0, le=1.0)


class NodeDispatchRequest(BaseModel):
    tool: str = Field(..., min_length=1)
    args: dict[str, Any] = Field(default_factory=dict)


def _default_tool_runner(tool: str, args: dict[str, Any]) -> Any:
    """In-process runner for API-only smoke; MCP path uses server tools."""
    if tool == "system_health":
        return {"status": "ok", "note": "use MCP aions_execute_step for full health"}
    return {"tool": tool, "args": args, "status": "delegated"}


_tool_runner: Optional[Callable[[str, dict[str, Any]], Any]] = None


def set_tool_runner(runner: Callable[[str, dict[str, Any]], Any]) -> None:
    global _tool_runner
    _tool_runner = runner


@router.post("/plan")
def post_plan(req: PlanRequest):
    try:
        plan = store_plan(create_plan(req.intent))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "plan_id": plan.id,
        "intent": plan.intent,
        "node_id": plan.node_id,
        "steps": [
            {"id": s.id, "description": s.description, "tool": s.tool, "args": s.args}
            for s in plan.steps
        ],
        "cbms_context": plan.cbms_context,
    }


@router.post("/execute")
def post_execute(req: ExecuteRequest):
    runner = _tool_runner or _default_tool_runner
    try:
        result = execute_step(req.plan_id, req.step_id, runner)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "step_id": result.step_id,
        "status": result.status,
        "output": result.output,
        "error": result.error,
        "duration_ms": result.duration_ms,
    }


@router.get("/scheduler/summary")
def get_scheduler_summary(horizon_days: int = 14, emit: bool = False):
    """Proactive scheduler tick — reads operator_profile deadlines, returns job queue + events."""
    summary = run_scheduler(emit=emit, horizon_days=horizon_days)
    return summary_to_dict(summary)


@router.post("/scheduler/tick")
def post_scheduler_tick(horizon_days: int = 14):
    """Run scheduler and persist summary events to AIONS_LOG_DIR/control_plane/scheduler_events.jsonl."""
    summary = run_scheduler(emit=True, horizon_days=horizon_days)
    return summary_to_dict(summary)


@router.get("/execution/{plan_id}")
def get_execution_status(plan_id: str):
    state = get_execution(plan_id)
    plan = get_plan(plan_id)
    if not state or not plan:
        raise HTTPException(status_code=404, detail="plan not found")
    return {
        "plan_id": plan_id,
        "node_id": plan.node_id,
        "status": state.status,
        "current_step": state.current_step,
        "total_steps": len(plan.steps),
        "results": [
            {
                "step_id": r.step_id,
                "status": r.status,
                "error": r.error,
                "duration_ms": r.duration_ms,
            }
            for r in state.results
        ],
    }


@router.post("/nodes/register")
def post_node_register(req: NodeRegisterRequest):
    try:
        rec = register_node(
            node_id=req.node_id,
            host=req.host,
            capabilities=req.capabilities,
            memory_mb=req.memory_mb,
            tools=req.tools,
            health=req.health,
            load=req.load,
            permissions=req.permissions or ["execute"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "registered", "node": rec.to_dict()}


@router.get("/nodes")
def get_nodes(healthy_only: bool = False):
    nodes = list_nodes(healthy_only=healthy_only)
    return {"count": len(nodes), "nodes": [n.to_dict() for n in nodes]}


@router.get("/nodes/summary")
def get_nodes_summary():
    return registry_summary()


@router.get("/nodes/{node_id}")
def get_node_detail(node_id: str):
    rec = get_node(node_id)
    if not rec:
        raise HTTPException(status_code=404, detail="node not found")
    return rec.to_dict()


@router.post("/nodes/{node_id}/heartbeat")
def post_node_heartbeat(node_id: str, req: NodeHeartbeatRequest):
    try:
        rec = heartbeat(node_id, health=req.health, load=req.load)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "ok", "node": rec.to_dict()}


@router.post("/nodes/{node_id}/dispatch")
def post_node_dispatch(node_id: str, req: NodeDispatchRequest):
    """Send one tool step to node_id (local in-process or remote stub)."""
    runner = _tool_runner or _default_tool_runner
    try:
        return dispatch_step_to_node(node_id, req.tool, req.args, local_runner=runner)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
