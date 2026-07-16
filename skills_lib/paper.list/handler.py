"""Skill paper.list — list all open admin items."""
import sys

if r"E:\server wiedzy" not in sys.path:
    sys.path.insert(0, r"E:\server wiedzy")
from control_plane.skills import papiery


def run(inputs, ctx):
    items = papiery.list_open()
    return {"ok": True, "count": len(items),
            "papers": [{"id": p["id"], "title": p["title"],
                        "deadline": p.get("deadline", ""), "priority": p.get("priority")}
                       for p in items]}
