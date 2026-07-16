"""AIONS Skill Engine — sesja na drugiej partii blokow (monitorowana)."""
import os
import sys

sys.path.insert(0, r"E:\server wiedzy")

from control_plane.skills.registry import SkillRegistry
from control_plane.skills import executor, planner, recipes, stats, world_state
from control_plane.skills.context import build_context

reg = SkillRegistry()
info = reg.discover()
print("=== BIBLIOTEKA:", info["loaded"], "blokow | bledy:", info["errors"], "===")
print("   ", reg.list_ids())

ctx = build_context()
DESK = os.path.join(os.path.expanduser("~"), "Desktop")
WORK = os.path.join(DESK, "AIONS_test")


def think(q):
    c = reg.search(q, top_k=3)
    print(f"  MYSLENIE '{q}':", c)
    return c


print("\n########## ZADANIE A: folder + plik + lista (lancuch 3 klockow, UCZENIE) ##########")
intentA = "utworz folder i zapisz w nim plik i pokaz zawartosc"
print("plan#1:", planner.plan(reg, intentA)["source"])
ctxA = build_context()
steps = [
    {"skill": "folder.create", "inputs": {"path": WORK}},
    {"skill": "file.write_text", "inputs": {"path": os.path.join(WORK, "witaj.txt"), "text": "AIONS tu byl."}},
    {"skill": "folder.list", "inputs": {"path": WORK}},
]
runA = executor.run_chain(reg, steps, ctxA,
                          verify=lambda c: os.path.exists(os.path.join(WORK, "witaj.txt")))
for s in runA["steps"]:
    print("  -", s["skill"], s["status"], s["ms"], "ms", s["error"] or "")
print("  zawartosc folderu:", ctxA["bag"].get("items"))
if runA["verified"]:
    print("  NAUCZYL SIE PRZEPISU:", recipes.save_recipe(intentA, steps, why=["lokalny folder"]))
print("plan#2:", planner.plan(reg, intentA)["source"], "(recipe = pamieta)")

print("\n########## ZADANIE B: schowek tam i z powrotem ##########")
executor.run_skill(reg, "clip.set_text", {"text": "AIONS w schowku 123"}, ctx)
print("  odczyt schowka:", executor.run_skill(reg, "clip.get_text", {}, ctx)["outputs"])

print("\n########## ZADANIE C: info o systemie ##########")
print("  IP:", executor.run_skill(reg, "net.my_ip", {}, ctx)["outputs"])
print("  ping 8.8.8.8:", executor.run_skill(reg, "net.ping", {"host": "8.8.8.8"}, ctx)["outputs"])
print("  data:", executor.run_skill(reg, "sys.datetime", {}, ctx)["outputs"])

print("\n########## ZADANIE D: zrzut ekranu ##########")
think("zrob zrzut ekranu")
print("  screenshot:", executor.run_skill(reg, "sys.screenshot", {}, ctx)["outputs"])

print("\n########## ZADANIE E: otworz strone w przegladarce (spojrz na ekran) ##########")
think("otworz strone internetowa")
print("  web:", executor.run_skill(reg, "web.open_url", {"url": "https://www.google.com"}, ctx)["outputs"])
print("  world.browser:", world_state.get("browser"))

print("\n----- MONITOR: staty (uczy sie skutecznosci) -----")
for sid in sorted(reg.list_ids()):
    e = stats.get(sid)
    if e.get("success", 0) or e.get("failed", 0):
        print(f"  {sid}: ok={e.get('success',0)} fail={e.get('failed',0)} "
              f"conf={e.get('confidence',0)} avg_ms={e.get('avg_ms',0)}")
print("\n=== KONIEC ===")
