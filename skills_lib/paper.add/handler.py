"""Skill paper.add — store an admin item as a CBMS-style block."""
import sys

if r"E:\server wiedzy" not in sys.path:
    sys.path.insert(0, r"E:\server wiedzy")
from control_plane.skills import papiery


def run(inputs, ctx):
    o = papiery.add(inputs["title"], inputs.get("deadline", ""),
                    inputs.get("note", ""), inputs.get("priority", "normal"),
                    inputs.get("tags"))
    return {"ok": True, "id": o["id"], "title": o["title"], "deadline": o["deadline"]}
