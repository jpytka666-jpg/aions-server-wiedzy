"""AIONS Agent Engine -- plug-and-play agent (role) registry.

Same mechanic as control_plane.skills.registry.SkillRegistry.discover():
drop a folder into agents_lib/ with an agent.json and it is discovered
automatically. No core code changes required to add a new role -- see
agent_schema.py for the required fields and fail-closed validation.
"""
from __future__ import annotations
from pathlib import Path

from . import agent_schema as schema

REPO = Path(__file__).resolve().parents[2]
AGENTS_DIR = REPO / "agents_lib"


class AgentRegistry:
    def __init__(self, agents_dir=AGENTS_DIR):
        self.agents_dir = Path(agents_dir)
        self.objects = {}
        self.errors = []

    def discover(self):
        self.objects.clear()
        self.errors.clear()
        if not self.agents_dir.exists():
            return {"loaded": 0, "errors": ["agents_lib not found"]}
        for d in sorted(self.agents_dir.iterdir()):
            if not d.is_dir():
                continue
            aj = d / "agent.json"
            if not aj.exists():
                continue
            try:
                o = schema.load(str(aj))
                errs = schema.validate(o)
                if errs:
                    self.errors.append(f"{d.name}: {errs}")
                    continue
                self.objects[o.id] = o
            except Exception as e:
                self.errors.append(f"{d.name}: {e}")
        return {"loaded": len(self.objects), "errors": self.errors}

    def get(self, aid):
        return self.objects.get(aid)

    def list_ids(self):
        return list(self.objects.keys())
