"""AIONS Skill Engine — planner.

recipe-first: if a verified recipe exists for this intent, replay it cheaply.
else compose: retrieve candidate skills, drop ones blocked by world state, and
hand them to the caller (a strong model composes the order on first solve).
"""
from __future__ import annotations

from . import recipes, world_state


def plan(registry, intent):
    r = recipes.find_recipe(intent)
    if r:
        return {"source": "recipe", "recipe_id": r["id"], "steps": r["steps"]}
    hits = registry.search(intent, top_k=5, types=("skill",))
    for h in hits:
        o = registry.get(h["id"])
        blocked = None
        for cond in getattr(o, "avoid_when", []) or []:
            if world_state.matches(cond):
                blocked = cond
                break
        h["blocked_by"] = blocked
    return {"source": "compose", "candidates": hits, "steps": []}
