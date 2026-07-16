"""AIONS Skill Engine — monitorowana sesja na Windows.

Zadania: otworz notatnik -> zapisz wierszyk do pliku i pokaz w notatniku ->
zamknij notatnik -> info systemowe. Przy kazdym kroku widac MYSLENIE (dopasowanie
blokow) oraz UCZENIE (zapis przepisu, staty skutecznosci).
Run: E:\\server wiedzy\\venv\\Scripts\\python.exe scripts\\demo_windows_session.py
"""
import os
import sys
import time

sys.path.insert(0, r"E:\server wiedzy")

from control_plane.skills.registry import SkillRegistry
from control_plane.skills import executor, planner, recipes, stats, world_state
from control_plane.skills.context import build_context


def snapshot(reg, label):
    print(f"\n----- MONITOR: {label} -----")
    for sid in sorted(reg.list_ids()):
        e = stats.get(sid)
        if e.get("success", 0) or e.get("failed", 0):
            print(f"  {sid}: ok={e.get('success',0)} fail={e.get('failed',0)} "
                  f"conf={e.get('confidence',0)} avg_ms={e.get('avg_ms',0)}")
    print("  world:", {k: v for k, v in world_state.load().items() if v != "unknown"})


world_state.set("notepad", "closed")
reg = SkillRegistry()
info = reg.discover()
print("=== BIBLIOTEKA:", info["loaded"], "blokow | bledy:", info["errors"], "===")
print("   ", reg.list_ids())

ctx = build_context()
DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
poem = open(r"E:\server wiedzy\runtime\state\poem.txt", encoding="utf-8").read().strip()

print("\n########## ZADANIE 1: 'otworz notatnik' ##########")
cand = reg.search("otworz notatnik do pisania", top_k=3)
print("MYSLENIE (dopasowanie blokow):", cand)
chosen = cand[0]["id"]
print("WYBRAL ->", chosen)
r = executor.run_skill(reg, chosen, {}, ctx)
print("WYNIK:", r["status"], r["outputs"], r["error"] or "")
time.sleep(2)

print("\n########## ZADANIE 2: zapisz wierszyk i pokaz w notatniku (LACZENIE + UCZENIE) ##########")
intent2 = "zapisz wierszyk do pliku i pokaz go w notatniku"
print("plan#1 zrodlo:", planner.plan(reg, intent2)["source"], "(brak przepisu)")
path = os.path.join(DESKTOP, "AIONS_wierszyk.txt")
ctx2 = build_context()
steps = [
    {"skill": "file.write_text", "inputs": {"path": path, "text": poem}},
    {"skill": "file.open", "inputs": {"path": path}},
]


def verify(c):
    return os.path.exists(path)


run = executor.run_chain(reg, steps, ctx2, verify=verify)
for s in run["steps"]:
    print("  -", s["skill"], s["status"], s["ms"], "ms", s["error"] or "")
print("plik:", path, "| verified:", run["verified"])
if run["verified"]:
    rid = recipes.save_recipe(intent2, steps, why=["plik lokalny", "notatnik dziala"])
    print("NAUCZYL SIE PRZEPISU ->", rid)
print("plan#2 zrodlo:", planner.plan(reg, intent2)["source"], "(recipe = pamieta jak to zrobic)")
print(">> Popatrz na ekran: wierszyk jest w Notatniku. Za 6 s zamykam.")
time.sleep(6)

print("\n########## ZADANIE 3: 'zamknij notatnik' ##########")
cand = reg.search("zamknij program notatnik", top_k=3)
print("MYSLENIE:", cand)
r = executor.run_skill(reg, "app.close", {"image": "notepad.exe"}, ctx2)
print("WYNIK:", r["status"], r["outputs"], r["error"] or "")
print("plik z wierszykiem nadal zapisany na dysku:", os.path.exists(path))

print("\n########## ZADANIE 4: data + wolne miejsce (nowe bloki) ##########")
print("  data:", executor.run_skill(reg, "sys.datetime", {}, ctx2)["outputs"])
print("  dysk E:", executor.run_skill(reg, "sys.free_space", {"drive": "E:\\"}, ctx2)["outputs"])

snapshot(reg, "PO CALEJ SESJI")
print("\n=== KONIEC SESJI ===")
