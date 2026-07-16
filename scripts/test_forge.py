"""E2E test forge: request -> (symulacja budowy) -> promote (verify) -> uzycie -> gap."""
import json
import os
import shutil
import sys

sys.path.insert(0, r"E:\server wiedzy")

from control_plane.skills import forge, executor
from control_plane.skills.registry import SkillRegistry
from control_plane.skills.context import build_context

print("1) request:", forge.request_skill("demo.hello", "Mowi czesc")["name"])
print("   pending:", [r["name"] for r in forge.list_requests("requested")])

built = r"E:\server wiedzy\skills_requests\built\demo.hello"
os.makedirs(built, exist_ok=True)
with open(os.path.join(built, "skill.json"), "w", encoding="utf-8") as f:
    json.dump({"id": "demo.hello", "type": "skill", "name": "Demo hello",
               "description": "Mowi czesc", "tags": ["demo", "hello"], "inputs": [],
               "outputs": [{"name": "msg", "type": "str"}], "requires": [], "avoid_when": [],
               "risk": "low", "handler": "handler:run", "version": "1.0"}, f, ensure_ascii=False, indent=2)
with open(os.path.join(built, "handler.py"), "w", encoding="utf-8") as f:
    f.write("def run(inputs, ctx):\n    return {'ok': True, 'msg': 'czesc'}\n")

print("2) promote (verify-before-trust):", forge.promote("demo.hello"))

reg = SkillRegistry()
reg.discover()
print("3) w rejestrze:", "demo.hello" in reg.list_ids())
print("   uruchom:", executor.run_skill(reg, "demo.hello", {}, build_context())["outputs"])

print("4) gap_detect 'wyslij smsa do mamy':", forge.gap_detect(reg, "wyslij smsa do mamy"))

shutil.rmtree(r"E:\server wiedzy\skills_lib\demo.hello", ignore_errors=True)
for sub in ["done", "failed", "pending"]:
    p = os.path.join(r"E:\server wiedzy\skills_requests", sub, "demo.hello.json")
    if os.path.exists(p):
        os.remove(p)
print("5) sprzatniete demo.hello")
print("DONE")
