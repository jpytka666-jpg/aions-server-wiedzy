"""AIONS Agent Engine -- agent object schema (role blocks).

Mirrors control_plane.skills.schema, but for agent.json instead of
skill.json. Agents are a DIFFERENT object type in the same plug-and-play
mechanic: same discover-a-folder pattern, same load()/validate() split, but
fail-closed on every required field instead of schema.py's soft defaults.

Required fields (agent.json):
    id               "agent.<rola>"
    type             must be exactly "agent"
    name             str
    description      str
    allowed_skills   list[str] of fnmatch patterns, e.g. ["linux.*"]
    risk_ceiling     "read" | "mutate" | "destructive"  (same vocabulary as
                     control_plane.skills.gate access classes)
    model_tier       "none" | "small" | "large"
    prompt_template  str (system prompt template for the role)
    version          str

Fail-closed: a missing/empty/wrong-typed required field is a validation
error, not a default. agent_registry.AgentRegistry.discover() drops any
agent.json that fails validate(), exactly like SkillRegistry.discover()
drops invalid skill.json.
"""
from __future__ import annotations
import json
import os
from dataclasses import dataclass, field

VALID_TYPE = "agent"
VALID_RISK_CEILING = {"read", "mutate", "destructive"}
VALID_MODEL_TIER = {"none", "small", "large"}

REQUIRED_FIELDS = (
    "id", "type", "name", "description", "allowed_skills",
    "risk_ceiling", "model_tier", "prompt_template", "version",
)


@dataclass
class AgentObject:
    id: str = None
    type: str = None
    name: str = None
    description: str = None
    allowed_skills: list = field(default_factory=list)
    risk_ceiling: str = None
    model_tier: str = None
    prompt_template: str = None
    version: str = None
    source_dir: str = ""

    def blob(self) -> str:
        return " ".join([self.id or "", self.name or "", self.description or ""]).lower()


def load(path: str) -> "AgentObject":
    """Reads agent.json verbatim -- no field is defaulted here. A field
    absent from the JSON stays None (or [] only for allowed_skills when the
    JSON value itself isn't a list), so validate() can catch it below.
    """
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    raw_allowed = d.get("allowed_skills")
    return AgentObject(
        id=d.get("id"),
        type=d.get("type"),
        name=d.get("name"),
        description=d.get("description"),
        allowed_skills=raw_allowed if isinstance(raw_allowed, list) else raw_allowed,
        risk_ceiling=d.get("risk_ceiling"),
        model_tier=d.get("model_tier"),
        prompt_template=d.get("prompt_template"),
        version=d.get("version"),
        source_dir=os.path.dirname(path),
    )


def validate(o: "AgentObject") -> list:
    """Fail-closed validation. Any required field that is missing, empty,
    or the wrong shape/value rejects the whole agent.json (caller drops it
    from the registry -- it never becomes a runnable role).
    """
    errs = []

    for fname in REQUIRED_FIELDS:
        val = getattr(o, fname, None)
        if val is None or val == "" or val == []:
            errs.append(f"missing field: {fname}")

    if o.id is not None:
        if not isinstance(o.id, str) or not o.id.startswith("agent."):
            errs.append(f"bad id (must be a string starting with 'agent.'): {o.id!r}")

    if o.type is not None and o.type != VALID_TYPE:
        errs.append(f"bad type: {o.type!r} (expected {VALID_TYPE!r})")

    if o.allowed_skills is not None:
        if not isinstance(o.allowed_skills, list) or not all(
            isinstance(x, str) and x for x in o.allowed_skills
        ):
            errs.append("allowed_skills must be a non-empty list of pattern strings")

    if o.risk_ceiling is not None and o.risk_ceiling not in VALID_RISK_CEILING:
        errs.append(
            f"bad risk_ceiling: {o.risk_ceiling!r} (expected one of {sorted(VALID_RISK_CEILING)})"
        )

    if o.model_tier is not None and o.model_tier not in VALID_MODEL_TIER:
        errs.append(
            f"bad model_tier: {o.model_tier!r} (expected one of {sorted(VALID_MODEL_TIER)})"
        )

    for fname in ("name", "description", "prompt_template", "version"):
        val = getattr(o, fname, None)
        if val is not None and not isinstance(val, str):
            errs.append(f"{fname} must be a string")

    return errs
