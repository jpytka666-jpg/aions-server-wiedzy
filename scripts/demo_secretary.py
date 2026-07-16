"""AIONS Skill Engine — scenariusz 'sekretarka' (nowe bloki + nauka + monitoring)."""
import os
import sys

sys.path.insert(0, r"E:\server wiedzy")

from control_plane.skills.registry import SkillRegistry
from control_plane.skills import executor, planner, recipes, stats
from control_plane.skills.context import build_context

WS = r"E:\AI_WORKSPACE\AIONS_workspace"
os.makedirs(WS, exist_ok=True)

reg = SkillRegistry()
info = reg.discover()
print("BIBLIOTEKA:", info["loaded"], "blokow | bledy:", info["errors"])
ctx = build_context()

print("\n=== SEKRETARKA: poranny rzut oka ===")
print("  data:", executor.run_skill(reg, "sys.now_pretty", {}, ctx)["outputs"].get("pretty"))
who = executor.run_skill(reg, "sys.who_am_i", {}, ctx)["outputs"]
print("  user:", who.get("user"), "| host:", who.get("host"))
w = executor.run_skill(reg, "app.list_windows", {}, ctx)["outputs"]
print("  otwarte okna:", w.get("count"), "->", w.get("windows", [])[:6])
r = executor.run_skill(reg, "file.recent", {"folder": WS, "top": 5}, ctx)["outputs"]
print("  ostatnie pliki w workspace:", r.get("recent"))
print("  RAM:", executor.run_skill(reg, "sys.resources", {}, ctx)["outputs"])

print("\n=== SEKRETARKA: przypomnienie (dymek na ekranie) ===")
print("  ", executor.run_skill(reg, "sys.notify",
      {"title": "AIONS", "message": "Marcin, mam 56 umiejetnosci. Robmy robote!"}, ctx)["outputs"])

print("\n=== SEKRETARKA: uczy sie 'przygotuj notatke z data' ===")
intent = "przygotuj notatke z data i policz slowa"
p1 = planner.plan(reg, intent)["source"]
ctx2 = build_context()
note = os.path.join(WS, "notatka.txt")
steps = [
    {"skill": "sys.now_pretty", "inputs": {}},
    {"skill": "file.write_text", "inputs": {"path": note, "text": "Notatka z ${bag.pretty}\n- zadanie 1\n- zadanie 2"}},
    {"skill": "file.word_count", "inputs": {"path": note}},
]
run = executor.run_chain(reg, steps, ctx2, verify=lambda c: os.path.exists(note))
for s in run["steps"]:
    print("  -", s["skill"], s["status"], s["ms"], "ms", s["error"] or "")
print("  slowa:", ctx2["bag"].get("words"), "| verified:", run["verified"], "| plan1:", p1)
if run["verified"]:
    print("  NAUCZYL SIE:", recipes.save_recipe(intent, steps))
print("  plan2:", planner.plan(reg, intent)["source"])

print("\n=== SEKRETARKA: otwiera Gmail (ekran) ===")
print("  ", executor.run_skill(reg, "web.open_gmail", {}, ctx)["outputs"])

print("\n=== MYSLENIE: dobor bloku ===")
for q in ["co mam otwarte", "sprawdz poczte", "ktora godzina", "przypomnij mi cos", "nad czym ostatnio pracowalem", "gdzie jest ta ulica"]:
    print(f"  '{q}' ->", reg.search(q, top_k=1))

print("\n=== MONITOR ===")
nok = sum(1 for s in reg.list_ids() if stats.get(s).get("success", 0))
print(f"  uzytych z sukcesem: {nok}/{info['loaded']} | przepisy: {len(recipes._load())}")
print("=== KONIEC ===")
