"""AIONS Skill Engine — unified object model.

Everything in AIONS is one Object with a `type`. The retriever does not care
about the type; it just finds the best-matching objects. Executable types own a
handler; composite types own steps.
"""
from __future__ import annotations
import json
import os
from dataclasses import dataclass, field

VALID_TYPES = {
    "knowledge", "skill", "recipe", "workflow",
    "decision", "thinking_pattern", "failure", "success",
}
VALID_RISK = {"low", "medium", "high"}
EXECUTABLE = {"skill"}
COMPOSITE = {"recipe", "workflow"}


@dataclass
class AObject:
    id: str
    type: str = "skill"
    name: str = ""
    description: str = ""
    tags: list = field(default_factory=list)
    inputs: list = field(default_factory=list)
    outputs: list = field(default_factory=list)
    requires: list = field(default_factory=list)     # positive preconditions (world_state)
    avoid_when: list = field(default_factory=list)   # negative conditions: skip if they hold
    risk: str = "low"
    handler: str = ""                                # "module:function" (relative to source_dir)
    steps: list = field(default_factory=list)        # for recipe/workflow
    version: str = "1.0"
    source_dir: str = ""

    def blob(self) -> str:
        return " ".join([self.id, self.name, self.description, " ".join(self.tags)]).lower()


def validate(o: "AObject") -> list:
    errs = []
    if not o.id:
        errs.append("missing id")
    if o.type not in VALID_TYPES:
        errs.append(f"bad type: {o.type}")
    if o.risk not in VALID_RISK:
        errs.append(f"bad risk: {o.risk}")
    if o.type in EXECUTABLE and not o.handler:
        errs.append("skill needs handler")
    if o.type in COMPOSITE and not o.steps:
        errs.append(f"{o.type} needs steps")
    return errs


def load(path: str) -> "AObject":
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    return AObject(
        id=d.get("id", ""),
        type=d.get("type", d.get("kind", "skill")),   # accept legacy 'kind'
        name=d.get("name", ""),
        description=d.get("description", ""),
        tags=d.get("tags", []),
        inputs=d.get("inputs", []),
        outputs=d.get("outputs", []),
        requires=d.get("requires", []),
        avoid_when=d.get("avoid_when", []),
        risk=d.get("risk", "low"),
        handler=d.get("handler", ""),
        steps=d.get("steps", []),
        version=d.get("version", "1.0"),
        source_dir=os.path.dirname(path),
    )
