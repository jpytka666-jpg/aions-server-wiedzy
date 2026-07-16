"""Skill paper.find — search admin items by keyword."""
import sys

if r"E:\server wiedzy" not in sys.path:
    sys.path.insert(0, r"E:\server wiedzy")
from control_plane.skills import papiery


def run(inputs, ctx):
    items = papiery.find(inputs["query"])
    return {"ok": True, "count": len(items),
            "found": [{"id": p["id"], "title": p["title"], "deadline": p.get("deadline", "")} for p in items]}
