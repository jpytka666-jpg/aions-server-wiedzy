"""AIONS Skill Engine — sesja FINALNA (pelna biblioteka, monitoring)."""
import os
import sys
import time

sys.path.insert(0, r"E:\server wiedzy")

from control_plane.skills.registry import SkillRegistry
from control_plane.skills import executor, planner, recipes, stats, world_state
from control_plane.skills.context import build_context

reg = SkillRegistry()
info = reg.discover()
print("=== PELNA BIBLIOTEKA:", info["loaded"], "blokow | bledy:", info["errors"], "===")

ctx = build_context()
DESK = os.path.join(os.path.expanduser("~"), "Desktop")
WORK = os.path.join(DESK, "AIONS_test")


def think(q):
    c = reg.search(q, top_k=2)
    print(f"  MYSLENIE '{q}':", c)
    return c


print("\n########## Z1: utworz folder + plik + SPAKUJ (lancuch 3, UCZENIE) ##########")
intent = "utworz folder zapisz plik i spakuj do zip"
print("plan#1:", planner.plan(reg, intent)["source"])
ctxA = build_context()
zip_out = os.path.join(DESK, "AIONS_paczka.zip")
steps = [
    {"skill": "folder.create", "inputs": {"path": WORK}},
    {"skill": "file.write_text", "inputs": {"path": os.path.join(WORK, "dane.txt"), "text": "paczka AIONS"}},
    {"skill": "folder.zip", "inputs": {"folder": WORK, "out": zip_out}},
]
runA = executor.run_chain(reg, steps, ctxA, verify=lambda c: os.path.exists(zip_out))
for s in runA["steps"]:
    print("  -", s["skill"], s["status"], s["ms"], "ms", s["error"] or "")
print("  zip:", ctxA["bag"].get("zip"), "| verified:", runA["verified"])
if runA["verified"]:
    print("  NAUCZYL SIE:", recipes.save_recipe(intent, steps, why=["folder lokalny"]))
print("plan#2:", planner.plan(reg, intent)["source"], "(recipe)")

print("\n########## Z2: otworz folder w Eksploratorze (ekran) ##########")
print("  ", executor.run_skill(reg, "app.open_folder", {"path": WORK}, ctx)["outputs"])
time.sleep(1)

print("\n########## Z3: wyszukaj w internecie (ekran) ##########")
think("poszukaj czegos w internecie")
print("  ", executor.run_skill(reg, "web.search", {"query": "AIONS agent OS"}, ctx)["outputs"])

print("\n########## Z4: info o systemie ##########")
print("  RAM:", executor.run_skill(reg, "sys.resources", {}, ctx)["outputs"])
print("  WiFi:", executor.run_skill(reg, "net.wifi_list", {}, ctx)["outputs"])
print("  dysk C:", executor.run_skill(reg, "sys.free_space", {"drive": "C:\\"}, ctx)["outputs"])

print("\n########## Z5: glosnosc (ciszej -> glosniej) ##########")
print("  ", executor.run_skill(reg, "sys.volume_down", {}, ctx)["outputs"])
time.sleep(0.5)
print("  ", executor.run_skill(reg, "sys.volume_up", {}, ctx)["outputs"])

print("\n########## Z6: AIONS PISZE SAM do notatnika (klawiatura) ##########")
executor.run_skill(reg, "app.launch", {"name": "notepad.exe"}, ctx)
time.sleep(1.5)
print("  type:", executor.run_skill(reg, "input.type_text",
                                     {"text": "AIONS pisze to sam, blokami CBMS."}, ctx)["outputs"])
time.sleep(2)
print("  zamykam notatnik:", executor.run_skill(reg, "proc.kill", {"image": "notepad.exe"}, ctx)["outputs"])

print("\n----- MONITOR KONCOWY -----")
used = [(sid, stats.get(sid)) for sid in sorted(reg.list_ids())]
for sid, e in used:
    if e.get("success", 0) or e.get("failed", 0):
        print(f"  {sid}: ok={e.get('success',0)} fail={e.get('failed',0)} conf={e.get('confidence',0)} avg_ms={e.get('avg_ms',0)}")
print("  przepisy (nauczone):", recipes.list_recipes()["count"] if hasattr(recipes, "list_recipes") else len(recipes._load()))
print("  world:", {k: v for k, v in world_state.load().items() if v != "unknown"})
print("\n=== KONIEC SESJI FINALNEJ ===")
