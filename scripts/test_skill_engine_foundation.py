"""E2E foundation test for the AIONS Skill Engine.

Proves: plug-and-play discovery, type-agnostic retrieval, chaining 2 skills into a
task, verify-before-learn, recipe save + replay, multi-dim stats, world-state.
Run: E:\\server wiedzy\\venv\\Scripts\\python.exe scripts\\test_skill_engine_foundation.py
"""
import sys

sys.path.insert(0, r"E:\server wiedzy")

from control_plane.skills.registry import SkillRegistry
from control_plane.skills import executor, planner, recipes, stats, world_state
from control_plane.skills.context import build_context

print("=== DISCOVER (plug-and-play) ===")
reg = SkillRegistry()
print(reg.discover())
print("ids:", reg.list_ids())

print("\n=== SEARCH (retriever type-agnostic) ===")
print("find file ->", reg.search("znajdz plik na dysku"))
print("remember  ->", reg.search("zapamietaj wniosek do pamieci"))

intent = "znajdz plik planner.py i zapamietaj gdzie jest"
print("\n=== PLAN #1 ===")
print(planner.plan(reg, intent))

print("\n=== EXECUTE (chain of 2 skills) ===")
ctx = build_context()
steps = [
    {"skill": "fs.find_file", "inputs": {"query": "planner.py", "folder": r"E:\server wiedzy\control_plane"}},
    {"skill": "note.save", "inputs": {"text": "planner.py = ${bag.first}"}},
]


def verify(ctx):
    # verify-before-learn: only learn if we actually found the file
    return bool(ctx["bag"].get("first"))


run = executor.run_chain(reg, steps, ctx, verify=verify)
for s in run["steps"]:
    print(" ", s["skill"], s["status"], s["ms"], "ms", s["error"] or "")
print("found:", ctx["bag"].get("first"))
print("verified:", run["verified"])

if run["verified"]:
    rid = recipes.save_recipe(intent, steps, why=["pliki lokalne", "brak logowania"])
    print("recipe saved:", rid)

print("\n=== PLAN #2 (should hit recipe) ===")
p2 = planner.plan(reg, intent)
print("source:", p2["source"], "| recipe:", p2.get("recipe_id"))

print("\n=== STATS (multi-dim) ===")
print("fs.find_file:", stats.get("fs.find_file"))
print("note.save   :", stats.get("note.save"))
print("world_state :", world_state.load())

ok = (run["verified"] and p2["source"] == "recipe"
      and stats.get("fs.find_file")["success"] >= 1)
print("\n=== RESULT:", "PASS" if ok else "FAIL", "===")
sys.exit(0 if ok else 1)
