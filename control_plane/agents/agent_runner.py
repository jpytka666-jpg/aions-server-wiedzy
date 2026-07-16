"""AIONS Agent Engine -- agent runner.

Agents are role blocks in the same plug-and-play mechanic as skills
(agent_registry.AgentRegistry.discover() mirrors
control_plane.skills.registry.SkillRegistry.discover()). An agent owns no
execution path of its own: run_agent() is a filtered, risk-capped VIEW onto
the existing skill registry/executor/gate.

Pipeline:
  1. FilteredRegistry(registry_skills, agent.allowed_skills) -- fnmatch
     patterns restrict what the agent's planner can even SEE. Out-of-role
     skills never appear as candidates (test: linux-admin's candidate list
     contains only linux.* ids, nothing from file.*/app.*/test.gate.*/...).
  2. Planning: model_tier == "small" tries
     control_plane.skills.goal_planner.plan_goal() against the FILTERED
     registry (small LLM, constrained choice over the role's own
     candidates); on any failure (import error, exception, escalate,
     empty plan) it falls back to a deterministic
     filtered_registry.search() top-1 plan. model_tier == "none" always
     uses that same deterministic top-1 planner -- no LLM call at all.
  3. Per-step risk ceiling: BEFORE a step may execute, its skill's risk
     class is computed via control_plane.skills.gate.classify() and
     compared against the agent's risk_ceiling. A class above the ceiling
     rejects the step with status "above_risk_ceiling" and the step is
     NEVER handed to executor.run_skill() -- so it is never audited either.
     This check runs for every step the runner is asked to execute
     (including steps passed in via the `forced_steps` escape hatch used
     by tests to exercise the ceiling in isolation from the planner), and
     it is strictly tighter than or equal to the global gate: something the
     global gate.check() would allow can still be rejected here because the
     role's ceiling is narrower.
  4. Steps that pass the ceiling AND are within allowed_skills execute via
     control_plane.skills.executor.run_skill() against the REAL
     (unfiltered) registry -- so the global risk gate in executor.py/gate.py
     still runs underneath. Double protection: role ceiling first, global
     gate always.

CLI:
    python -m control_plane.agents.agent_runner <agent_id> "<cel>"
"""
from __future__ import annotations

import fnmatch
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from control_plane.skills import executor, gate  # noqa: E402
# v1.1 (backlog): re-uzywamy TEGO SAMEGO stemmera co SkillRegistry.search()
# (control_plane/skills/registry.py), zeby FilteredRegistry.search() -- ktora
# jest osobna, historycznie zduplikowana implementacja lexical retrieval --
# nie rozjezdzala sie z bazowym rejestrem (inaczej np. "services" trafialoby
# w tag "service" tylko poza rola agenta, a przez FilteredRegistry -- nie).
from control_plane.skills.registry import _stem_set  # noqa: E402

RISK_ORDER = {"read": 0, "mutate": 1, "destructive": 2}


class FilteredRegistry:
    """Read-only view of a real SkillRegistry restricted to skill ids that
    match at least one fnmatch pattern in `patterns` (e.g. "linux.*"). This
    is what gets handed to goal_planner.plan_goal()/registry.search() so an
    agent's planner never even sees skills outside its role.

    get()/handler() only resolve ids that are actually in scope; anything
    else returns None, so out-of-role ids can't leak through this view even
    if a caller guesses an id.
    """

    def __init__(self, base_registry, patterns):
        self._base = base_registry
        self._patterns = list(patterns or [])
        self.objects = {
            oid: o for oid, o in base_registry.objects.items() if self._matches(oid)
        }

    def _matches(self, skill_id: str) -> bool:
        return any(fnmatch.fnmatch(skill_id, p) for p in self._patterns)

    def get(self, oid):
        return self.objects.get(oid)

    def handler(self, oid):
        if oid not in self.objects:
            return None
        return self._base.handler(oid)

    def list_ids(self):
        return list(self.objects.keys())

    def search(self, query, top_k=5, types=None):
        """Same lexical retrieval as SkillRegistry.search(), scoped to
        self.objects (the filtered set). v1.1 (backlog): tokens go through
        the shared _stem_set() normalizer -- identical rule as the base
        registry -- so this filtered view matches the same queries."""
        q = _stem_set(query.lower().replace(",", " ").replace(".", " ").split())
        scored = []
        for o in self.objects.values():
            if types and o.type not in types:
                continue
            blob = _stem_set(o.blob().replace(".", " ").split())
            overlap = len(q & blob)
            taghit = len(q & _stem_set(" ".join(o.tags).lower().split()))
            score = overlap + 0.5 * taghit
            if score > 0:
                scored.append((round(score, 2), o.id, o.type))
        scored.sort(reverse=True)
        return [{"id": i, "type": t, "score": s} for s, i, t in scored[:top_k]]


def _deterministic_plan(filtered_registry, goal: str) -> dict:
    """model_tier == 'none' planner, and the fallback used whenever
    model_tier == 'small' can't get a usable plan from goal_planner:
    registry.search() top-1 over the FILTERED candidates. No LLM call."""
    hits = filtered_registry.search(goal, top_k=1, types=("skill",))
    if not hits:
        return {
            "status": "escalate", "reason": "no_candidates", "steps": [],
            "source": "deterministic_top1",
        }
    return {
        "status": "planned",
        "steps": [{"skill": hits[0]["id"], "inputs": {}}],
        "source": "deterministic_top1",
        "why": "deterministic fallback: top-1 lexical match over allowed_skills",
    }


def _plan(agent, filtered_registry, goal: str) -> dict:
    if agent.model_tier == "small":
        try:
            from control_plane.skills import goal_planner
            result = goal_planner.plan_goal(goal, filtered_registry, max_steps=5)
            if isinstance(result, dict) and result.get("status") == "planned" and result.get("steps"):
                return result
        except Exception:
            pass  # any failure (import, LLM unavailable, exception) -> deterministic fallback
        return _deterministic_plan(filtered_registry, goal)
    # model_tier == "none" (or anything unrecognized) -> deterministic only
    return _deterministic_plan(filtered_registry, goal)


def _build_skill_registry():
    from control_plane.skills import registry as registry_mod
    reg = registry_mod.SkillRegistry()
    reg.discover()
    return reg


def run_agent(agent_id: str, goal: str, registry_skills, ctx: dict, forced_steps=None) -> dict:
    """Run `goal` as `agent_id`.

    registry_skills: a real, already-discover()'d
        control_plane.skills.registry.SkillRegistry (the FULL catalog).
        run_agent() only reads it; it never mutates it.
    ctx: executor context dict, e.g. {"bag": {}}.
    forced_steps: optional list of {"skill": id, "inputs": {...}} that
        skips planning and is fed straight into the risk-ceiling/scope/
        execution pipeline. Exists so tests (and callers building their own
        plans) can exercise the risk-ceiling gate directly, independent of
        whatever the planner would have chosen.

    Returns {"agent_id", "goal", "steps_results", "status", "risk_rejections"}.
    """
    from control_plane.agents import agent_registry as agent_registry_mod

    agents_reg = agent_registry_mod.AgentRegistry()
    agents_reg.discover()
    agent = agents_reg.get(agent_id)
    if agent is None:
        return {
            "agent_id": agent_id, "goal": goal, "steps_results": [],
            "status": "unknown_agent", "risk_rejections": [],
        }

    filtered = FilteredRegistry(registry_skills, agent.allowed_skills)

    if forced_steps is not None:
        plan_result = {"status": "planned", "steps": list(forced_steps), "source": "forced"}
    else:
        plan_result = _plan(agent, filtered, goal)

    if plan_result.get("status") != "planned" or not plan_result.get("steps"):
        return {
            "agent_id": agent_id, "goal": goal, "steps_results": [],
            "status": plan_result.get("status", "escalate"),
            "risk_rejections": [], "plan": plan_result,
        }

    ceiling = agent.risk_ceiling
    ceiling_rank = RISK_ORDER.get(ceiling, -1)

    steps_results = []
    risk_rejections = []
    any_executed_ok = False

    for step in plan_result["steps"]:
        skill_id = step.get("skill")
        # Look the skill up in the REAL registry so we can classify its risk
        # even for a forced/out-of-scope id -- the ceiling check must not
        # depend on the skill being visible to this agent's planner.
        obj = registry_skills.get(skill_id)
        if obj is None:
            steps_results.append({
                "skill": skill_id, "status": "error",
                "error": "unknown skill", "outputs": {},
            })
            continue

        skill_meta = {"id": obj.id, "risk": getattr(obj, "risk", None)}
        risk_class = gate.classify(skill_meta)
        if RISK_ORDER.get(risk_class, 99) > ceiling_rank:
            risk_rejections.append({
                "skill": skill_id, "risk_class": risk_class, "risk_ceiling": ceiling,
            })
            steps_results.append({
                "skill": skill_id, "status": "above_risk_ceiling",
                "error": f"risk_class={risk_class} exceeds agent risk_ceiling={ceiling}",
                "outputs": {},
            })
            continue  # NEVER reaches executor.run_skill -> never audited

        if skill_id not in filtered.objects:
            steps_results.append({
                "skill": skill_id, "status": "not_allowed",
                "error": "outside allowed_skills for this agent role", "outputs": {},
            })
            continue

        inputs = step.get("inputs", {}) or {}
        # Executes against the REAL registry: the global gate in
        # executor.py/gate.py still runs underneath this role-level check.
        res = executor.run_skill(registry_skills, skill_id, inputs, ctx)
        steps_results.append(res)
        if res.get("status") == "ok":
            any_executed_ok = True

    if any_executed_ok:
        status = "done"
    elif any(r.get("status") == "approval_required" for r in steps_results):
        status = "approval_required"
    elif any(r.get("status") == "above_risk_ceiling" for r in steps_results):
        status = "above_risk_ceiling"
    elif any(r.get("status") == "not_allowed" for r in steps_results):
        status = "not_allowed"
    else:
        status = "failed"

    return {
        "agent_id": agent_id, "goal": goal,
        "steps_results": steps_results, "status": status,
        "risk_rejections": risk_rejections, "plan": plan_result,
    }


def main() -> int:
    if len(sys.argv) < 3:
        print('usage: python -m control_plane.agents.agent_runner <agent_id> "<cel>"')
        return 2
    agent_id = sys.argv[1]
    goal = sys.argv[2]

    reg = _build_skill_registry()
    ctx = {"bag": {}}
    result = run_agent(agent_id, goal, reg, ctx)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if result.get("status") == "done" else 1


if __name__ == "__main__":
    sys.exit(main())
