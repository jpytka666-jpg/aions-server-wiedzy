"""Skill paper.due — items with a deadline within N days."""
import sys

if r"E:\server wiedzy" not in sys.path:
    sys.path.insert(0, r"E:\server wiedzy")
from control_plane.skills import papiery


def run(inputs, ctx):
    items = papiery.due(int(inputs.get("days", 7)))
    return {"ok": True, "count": len(items),
            "due": [{"id": p["id"], "title": p["title"], "deadline": p.get("deadline", "")} for p in items]}
