"""Live demo: skill blocks that OPEN real apps (Notepad, Calculator).

Shows: plug-and-play (2 new blocks, no core-loop change), real launch, and
world-state awareness (second open of Notepad is SKIPPED, not repeated).
Run: E:\\server wiedzy\\venv\\Scripts\\python.exe scripts\\test_skill_open_apps.py
"""
import sys
import time

sys.path.insert(0, r"E:\server wiedzy")

from control_plane.skills.registry import SkillRegistry
from control_plane.skills import executor, world_state
from control_plane.skills.context import build_context

# clean slate for the demo
world_state.set("notepad", "closed")
world_state.set("calc", "closed")

reg = SkillRegistry()
print("discover:", reg.discover())
print("ids:", reg.list_ids())

ctx = build_context()

print("\n-- 1) Otwieram Notatnik --")
r1 = executor.run_skill(reg, "app.open_notepad", {}, ctx)
print("status:", r1["status"], "| outputs:", r1["outputs"], "| err:", r1["error"] or "-")
print("world.notepad =", world_state.get("notepad"))

time.sleep(2)

print("\n-- 2) Probuje otworzyc Notatnik DRUGI raz (ma pominac) --")
r2 = executor.run_skill(reg, "app.open_notepad", {}, ctx)
print("status:", r2["status"], "| powod:", r2["error"] or "-")

time.sleep(1)

print("\n-- 3) Otwieram Kalkulator (inny, nowy blok) --")
r3 = executor.run_skill(reg, "app.open_calc", {}, ctx)
print("status:", r3["status"], "| outputs:", r3["outputs"], "| err:", r3["error"] or "-")
print("world.calc =", world_state.get("calc"))

ok = (r1["status"] == "ok" and r2["status"] == "skipped" and r3["status"] == "ok")
print("\nRESULT:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
