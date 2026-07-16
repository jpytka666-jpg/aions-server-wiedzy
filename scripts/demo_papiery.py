"""AIONS — magazyn 'papierow' jako bloki CBMS. Demo: dodaj, pokaz, pilne, przypomnij."""
import datetime
import sys

sys.path.insert(0, r"E:\server wiedzy")

from control_plane.skills.registry import SkillRegistry
from control_plane.skills import executor
from control_plane.skills.context import build_context

reg = SkillRegistry()
info = reg.discover()
print("BIBLIOTEKA:", info["loaded"], "blokow | bledy:", info["errors"])
ctx = build_context()

today = datetime.date.today()
d3 = (today + datetime.timedelta(days=3)).isoformat()
d12 = (today + datetime.timedelta(days=12)).isoformat()

print("\n=== DODAJE PRZYKLADOWE PAPIERY (zamienisz na swoje) ===")
for t, dl, pr in [
    ("[przyklad] Zaplacic rachunek za prad", d3, "high"),
    ("[przyklad] Wyslac formularz do urzedu", d12, "normal"),
    ("[przyklad] Zadzwonic do przychodni", "", "normal"),
]:
    o = executor.run_skill(reg, "paper.add", {"title": t, "deadline": dl, "priority": pr}, ctx)["outputs"]
    print("  +", o["title"], "| termin:", o.get("deadline") or "brak", "| id:", o["id"])

print("\n=== WSZYSTKIE PAPIERY (sekretarka trzyma za Ciebie) ===")
lst = executor.run_skill(reg, "paper.list", {}, ctx)["outputs"]
for p in lst["papers"]:
    print(f"  - {p['title']} | termin: {p['deadline'] or 'brak'} | {p['priority']}")

print("\n=== CO PILNE (najblizsze 7 dni) ===")
duep = executor.run_skill(reg, "paper.due", {"days": 7}, ctx)["outputs"]
print("  pilnych:", duep["count"])
for p in duep["due"]:
    print("  !", p["title"], "->", p["deadline"])

print("\n=== SEKRETARKA PRZYPOMINA (dymek na ekranie) ===")
if duep["count"]:
    msg = "PILNE: " + "; ".join(p["title"].replace("[przyklad] ", "") for p in duep["due"])
else:
    msg = "Nic pilnego. Spokojnie."
executor.run_skill(reg, "sys.notify", {"title": "AIONS - papiery", "message": msg}, ctx)
print("  ->", msg)

print("\n=== SZUKANIE 'urzad' ===")
f = executor.run_skill(reg, "paper.find", {"query": "urzad"}, ctx)["outputs"]
print("  znaleziono:", [x["title"] for x in f["found"]])

print("\n=== MYSLENIE: dobor bloku ===")
for q in ["zapisz sobie ze mam zaplacic rachunek", "co mam do zrobienia", "co pilne", "odhacz sprawe"]:
    print(f"  '{q}' ->", reg.search(q, top_k=1))

print("\n=== GDZIE TO LEZY ===")
print(r"  bloki papierow: E:\AI_WORKSPACE\AIONS_workspace\papiery\*.json (Twoj CBMS, zero zewnetrznej bazy)")
print("=== KONIEC ===")
