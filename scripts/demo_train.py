"""AIONS Skill Engine — sesja TRENINGOWA (nauka + powtarzanie + monitoring).

Wszystkie wyniki na E:\\AI_WORKSPACE\\AIONS_workspace (nic na C:).
"""
import os
import sys
import time

sys.path.insert(0, r"E:\server wiedzy")

from control_plane.skills.registry import SkillRegistry
from control_plane.skills import executor, planner, recipes, stats
from control_plane.skills.context import build_context

WS = r"E:\AI_WORKSPACE\AIONS_workspace"
os.makedirs(WS, exist_ok=True)

reg = SkillRegistry()
info = reg.discover()
print("BIBLIOTEKA:", info["loaded"], "blokow | bledy:", info["errors"])


def learn(intent, steps, verify):
    p1 = planner.plan(reg, intent)["source"]
    ctx = build_context()
    run = executor.run_chain(reg, steps, ctx, verify=verify)
    oks = sum(1 for s in run["steps"] if s["status"] == "ok")
    saved = ""
    if run["verified"]:
        saved = recipes.save_recipe(intent, steps)
    p2 = planner.plan(reg, intent)["source"]
    print(f"  [{intent[:36]:36}] {oks}/{len(steps)} ok | plan1={p1}->plan2={p2} {saved}")


print("\n=== TRENING 1: nauka przepisow (compose -> verify -> recipe) ===")
learn("zapisz log z data do pliku",
      [{"skill": "sys.datetime", "inputs": {}},
       {"skill": "file.write_text", "inputs": {"path": os.path.join(WS, "log.txt"), "text": "log ${bag.now}"}}],
      lambda c: os.path.exists(os.path.join(WS, "log.txt")))
learn("utworz folder spakuj i policz zawartosc",
      [{"skill": "folder.create", "inputs": {"path": os.path.join(WS, "paczka")}},
       {"skill": "file.write_text", "inputs": {"path": os.path.join(WS, "paczka", "a.txt"), "text": "x"}},
       {"skill": "folder.zip", "inputs": {"folder": os.path.join(WS, "paczka"), "out": os.path.join(WS, "paczka.zip")}},
       {"skill": "folder.list", "inputs": {"path": os.path.join(WS, "paczka")}}],
      lambda c: os.path.exists(os.path.join(WS, "paczka.zip")))
learn("zrob skrot do notatnika",
      [{"skill": "shortcut.create", "inputs": {"target": "notepad.exe", "link": os.path.join(WS, "Notatnik.lnk")}}],
      lambda c: os.path.exists(os.path.join(WS, "Notatnik.lnk")))

print("\n=== TRENING 2: powtarzanie (buduje statystyki i pewnosc) ===")
ctx = build_context()
for _ in range(4):
    executor.run_skill(reg, "sys.datetime", {}, ctx)
    executor.run_skill(reg, "sys.free_space", {"drive": "E:\\"}, ctx)
    executor.run_skill(reg, "net.my_ip", {}, ctx)
print("  4x: sys.datetime, sys.free_space, net.my_ip")

print("\n=== TRENING 3: nowe bloki na zywo ===")
print("  uptime:", executor.run_skill(reg, "sys.uptime", {}, ctx)["outputs"])
print("  bateria:", executor.run_skill(reg, "sys.battery", {}, ctx)["outputs"])
print("  minimalizuj okna:", executor.run_skill(reg, "window.minimize_all", {}, ctx)["status"])
time.sleep(1.5)
print("  przywroc okna:", executor.run_skill(reg, "window.restore_all", {}, ctx)["status"])
print("  otworz ustawienia:", executor.run_skill(reg, "sys.open_settings", {"page": "display"}, ctx)["outputs"])
print("  jasnosc 80%:", executor.run_skill(reg, "sys.brightness", {"level": 80}, ctx)["outputs"])

print("\n=== MYSLENIE: dobor bloku dla roznych polecen ===")
for q in ["pokaz pulpit", "zrob skrot", "ile wolnego miejsca", "sprawdz baterie", "otworz ustawienia dzwieku", "wyczysc miejsce na dysku"]:
    print(f"  '{q}' ->", reg.search(q, top_k=2))

print("\n=== MONITOR KONCOWY ===")
n_ok = sum(1 for sid in reg.list_ids() if stats.get(sid).get("success", 0))
print(f"  blokow uzytych z sukcesem: {n_ok}/{info['loaded']}")
print("  przepisy nauczone:", len(recipes._load()))
top = sorted(((stats.get(s).get("confidence", 0), s) for s in reg.list_ids() if stats.get(s).get("success", 0)), reverse=True)[:8]
print("  najlepsze bloki (conf):", [(s, c) for c, s in top])
print("  przepisy (intent, uzycia):", [(v["intent"][:28], v.get("uses", 0)) for v in recipes._load().values()])
print("\n=== KONIEC TRENINGU ===")
