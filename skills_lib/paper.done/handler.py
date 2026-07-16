"""Skill paper.done — mark an admin item as done."""
import sys

if r"E:\server wiedzy" not in sys.path:
    sys.path.insert(0, r"E:\server wiedzy")
from control_plane.skills import papiery


def run(inputs, ctx):
    o = papiery.done(inputs["id"])
    return {"ok": bool(o), "id": inputs["id"], "title": (o or {}).get("title")}
