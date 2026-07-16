"""Thin bridge exposing the Skill Engine to MCP tools (used by server.py).

Each call re-discovers the registry so freshly dropped skills_lib/ blocks are
picked up without restarting anything (true plug-and-play).
"""
from __future__ import annotations

from . import executor, planner, recipes, stats
from .context import build_context
from .registry import SkillRegistry


def _reg():
    r = SkillRegistry()
    r.discover()
    return r


def list_skills():
    r = _reg()
    return {"count": len(r.list_ids()), "skills": r.list_ids(), "errors": r.errors}


def search_skills(query, top_k=5):
    r = _reg()
    return {"query": query, "hits": r.search(query, top_k=top_k)}


def run_skill(skill_id, inputs=None):
    r = _reg()
    ctx = build_context()
    return executor.run_skill(r, skill_id, inputs or {}, ctx)


def run_task(intent):
    r = _reg()
    p = planner.plan(r, intent)
    if p["source"] == "recipe":
        ctx = build_context()
        run = executor.run_chain(r, p["steps"], ctx)
        recipes.mark_used(p["recipe_id"])
        return {"source": "recipe", "recipe_id": p["recipe_id"],
                "ok": run["ok"], "verified": run["verified"], "bag": ctx["bag"]}
    return {"source": "compose", "candidates": p["candidates"],
            "note": "Brak zapisanego przepisu — kroki musi ulozyc model (duzy mozg planuje raz)."}


def list_recipes():
    d = recipes._load()
    return {"count": len(d),
            "recipes": [{"id": k, "intent": v.get("intent"), "uses": v.get("uses", 0),
                         "steps": len(v.get("steps", []))} for k, v in d.items()]}
