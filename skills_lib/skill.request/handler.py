"""Skill skill.request — file a request for a new skill block (forge queue)."""
import sys

if r"E:\server wiedzy" not in sys.path:
    sys.path.insert(0, r"E:\server wiedzy")
from control_plane.skills import forge


def run(inputs, ctx):
    o = forge.request_skill(inputs["name"], inputs.get("description", ""),
                            inputs.get("inputs"), inputs.get("why", ""), requested_by="chat")
    return {"ok": True, "request": o["name"], "status": o["status"]}
