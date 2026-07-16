"""AIONS Skill Engine — LIVE demo.

Pokazuje na zywo:
  1) otwiera Notatnik (widoczne na ekranie),
  2) drugi raz Notatnik -> POMIJA (swiadomosc stanu, avoid_when),
  3) otwiera Kalkulator (inny, drop-in blok),
  4) UCZY SIE: laczy 2 bloki (znajdz plik + zapisz wniosek), weryfikuje, zapisuje przepis,
  5) przy powtorzeniu zadania korzysta z przepisu (nie planuje od nowa).
Run: E:\\server wiedzy\\venv\\Scripts\\python.exe scripts\\demo_skill_live.py
"""
import sys
import time

sys.path.insert(0, r"E:\server wiedzy")

from control_plane.skills.registry import SkillRegistry
from control_plane.skills import executor, planner, recipes, stats, world_state
from control_plane.skills.context import build_context

world_state.set("notepad", "closed")
world_state.set("calc", "closed")

reg = SkillRegistry()
info = reg.discover()
print("=== BIBLIOTEKA UMIEJETNOSCI ===")
print("zaladowane:", info["loaded"], "| bledy:", info["errors"])
print("skille:", reg.list_ids())

ctx = build_context()

print("\n[1] OTWIERAM NOTATNIK  (spojrz na ekran)")
r = executor.run_skill(reg, "app.open_notepad", {}, ctx)
print("   ->", r["status"], r["outputs"], "| world.notepad =", world_state.get("notepad"))
time.sleep(2)

print("[2] PROBUJE DRUGI RAZ NOTATNIK  (ma pominac, bo juz otwarty)")
r = executor.run_skill(reg, "app.open_notepad", {}, ctx)
print("   ->", r["status"], "| powod:", r["error"] or "-")

print("\n[3] OTWIERAM KALKULATOR  (nowy blok, plug-and-play)")
r = executor.run_skill(reg, "app.open_calc", {}, ctx)
print("   ->", r["status"], r["outputs"], "| world.calc =", world_state.get("calc"))
time.sleep(1)

print("\n[4] UCZENIE: zadanie z 2 krokow -> ZNAJDZ PLIK + ZAPISZ WNIOSEK")
intent = "znajdz plik planner.py i zapisz wniosek gdzie jest"
print("   plan#1 zrodlo:", planner.plan(reg, intent)["source"], "(brak przepisu -> komponuje)")
ctx2 = build_context()
steps = [
    {"skill": "fs.find_file", "inputs": {"query": "planner.py", "folder": r"E:\server wiedzy\control_plane"}},
    {"skill": "note.save", "inputs": {"text": "WNIOSEK: planner.py lezy w ${bag.first}"}},
]


def verify(c):
    return bool(c["bag"].get("first"))


run = executor.run_chain(reg, steps, ctx2, verify=verify)
for s in run["steps"]:
    print("   -", s["skill"], s["status"], s["ms"], "ms")
print("   znaleziono:", ctx2["bag"].get("first"))
print("   verified (verify-before-learn):", run["verified"])
if run["verified"]:
    rid = recipes.save_recipe(intent, steps, why=["plik lokalny", "brak logowania"])
    print("   ZAPISANY PRZEPIS:", rid)

print("   plan#2 zrodlo:", planner.plan(reg, intent)["source"], "(=recipe -> NAUCZYL SIE)")

print("\n=== STATY (uczy sie skutecznosci) ===")
for sid in reg.list_ids():
    e = stats.get(sid)
    print("  ", sid, "| ok:", e.get("success", 0), "| conf:", e.get("confidence", 0), "| avg_ms:", e.get("avg_ms", 0))

ok = (info["loaded"] >= 4 and run["verified"]
      and planner.plan(reg, intent)["source"] == "recipe")
print("\nRESULT:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
