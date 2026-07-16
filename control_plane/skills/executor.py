"""AIONS Skill Engine — executor with world-state awareness + verify-before-learn.

Runs single skills or chains. Outputs of each step flow into ctx['bag'] and can be
referenced by later steps via "$bag.key" (whole value) or "${bag.key}" (inline).
Skills whose `avoid_when` conditions currently hold are skipped, not run.
"""
from __future__ import annotations
import re
import time

from . import gate, stats, world_state


def _resolve(v, bag):
    if isinstance(v, str):
        if v.startswith("$bag."):
            return bag.get(v[5:])
        return re.sub(r"\$\{bag\.([A-Za-z0-9_]+)\}",
                      lambda m: str(bag.get(m.group(1), "")), v)
    return v


def _blocked_by_state(obj):
    for cond in getattr(obj, "avoid_when", []) or []:
        if world_state.matches(cond):
            return cond
    return None


def run_skill(registry, skill_id, inputs, ctx, respect_state=True, node_id="windows-primary"):
    obj = registry.get(skill_id)
    fn = registry.handler(skill_id)
    if obj is None or fn is None:
        return {"skill": skill_id, "status": "error", "error": "unknown skill",
                "ms": 0, "outputs": {}}
    if respect_state:
        blocked = _blocked_by_state(obj)
        if blocked:
            return {"skill": skill_id, "status": "skipped",
                    "error": f"avoid_when: {blocked}", "ms": 0, "outputs": {}}

    # Security gate: classify the skill's risk and decide if the run may
    # proceed. Every outcome from this point on is audited.
    skill_meta = {"id": obj.id, "risk": getattr(obj, "risk", None)}
    decision = gate.check(skill_meta, inputs, node_id=node_id)

    if not decision["allowed"]:
        gate.audit({
            "skill_id": skill_id,
            "risk_class": decision["risk_class"],
            "decision": decision["decision"],
            "inputs": inputs,
            "rc": None,
            "duration_ms": 0,
        }, node_id)
        return {"skill": skill_id, "status": "approval_required",
                "error": "approval_required", "ms": 0, "outputs": {}}

    t0 = time.perf_counter()
    try:
        outputs = fn(inputs, ctx) or {}
        ms = int((time.perf_counter() - t0) * 1000)
        stats.record(skill_id, True, ms, getattr(obj, "risk", "low"))
        gate.audit({
            "skill_id": skill_id,
            "risk_class": decision["risk_class"],
            "decision": decision["decision"],
            "inputs": inputs,
            "rc": 0,
            "duration_ms": ms,
        }, node_id)
        return {"skill": skill_id, "status": "ok", "outputs": outputs, "ms": ms, "error": None}
    except Exception as e:
        ms = int((time.perf_counter() - t0) * 1000)
        stats.record(skill_id, False, ms, getattr(obj, "risk", "low"))
        gate.audit({
            "skill_id": skill_id,
            "risk_class": decision["risk_class"],
            "decision": decision["decision"],
            "inputs": inputs,
            "rc": 1,
            "duration_ms": ms,
        }, node_id)
        return {"skill": skill_id, "status": "error", "outputs": {}, "ms": ms, "error": str(e)}


def run_chain(registry, steps, ctx, verify=None):
    """Execute steps in order. `verify(ctx) -> bool` gates learning."""
    results = []
    ok = True
    for step in steps:
        inputs = {k: _resolve(v, ctx["bag"]) for k, v in dict(step.get("inputs", {})).items()}
        res = run_skill(registry, step["skill"], inputs, ctx)
        results.append(res)
        if res["status"] == "ok":
            for k, v in res["outputs"].items():
                ctx["bag"][k] = v
        else:
            ok = False
            break
    verified = bool(ok and (verify is None or verify(ctx)))
    return {"ok": ok, "verified": verified, "steps": results}
