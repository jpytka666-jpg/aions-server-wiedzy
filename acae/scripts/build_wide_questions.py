"""
Zlozenie SZEROKIEGO zbioru pytan z czesci `_desc/questions_*.json`.

PO CO
-----
Zbior Marcina ma 10 pytan pozytywnych. Jedno pytanie to 10 punktow procentowych, wiec
„70%" moze byc przypadkiem na malej probce. Ten zbior ma po dwa pytania na kazdy ze 169
plikow — okolo 340 pozytywow — i sluzy do ZNAJDOWANIA DZIUR, nie do chwalenia sie liczba.

CZYM SIE ROZNI OD ZAMROZONEGO ZBIORU — cztery rzeczy, wszystkie na niekorzysc dowodu
-------------------------------------------------------------------------------------
1. **Pytania powstaly Z OPISOW plikow.** Dziela z nimi czesc slownictwa, mimo instrukcji
   „pytaj tak, jakbys nie czytal opisu". Wynik bedzie **optymistycznie zawyzony**.
2. **Klucz odpowiedzi jest automatyczny**: pytanie napisane dla pliku X ma odpowiedz X.
   Nikt nie sprawdzil, czy inny plik nie odpowiada rownie dobrze.
3. **Trafienie liczone na poziomie PLIKU**, nie symbolu — `answer_symbols` to wszystkie
   symbole wlasciwego pliku. Prog lagodniejszy niz w `dev`/`heldout`.
4. **Pytania pisal ten sam model**, ktory pisal opisy (Haiku). Rodzinne podobienstwo
   slownictwa jest realnym ryzykiem i nie da sie go stad wykluczyc.

**Wynikow stad NIE WOLNO wstawiac do tabeli porownawczej z `dev` i `heldout`.**
Sluza do jednego: pokazac, GDZIE narzedzie zawodzi, na probce duzej dosc, zeby
pojedynczy przypadek nie przesadzal.

NEGATYWY
--------
Pytania o rzeczy, ktorych w tym repo nie ma — pisane recznie, bo model piszacy pytania
z opisow nie ma jak wymyslic czegos spoza korpusu. Sluza do `neg/poz`.
"""

import json
import pathlib
import tomllib

from acae.core import collect_entries
from acae.pack import FsLocator, FsReader

ACAE = pathlib.Path("acae")

# Rzeczy, ktorych w tym repo NIE MA. Dobierane tak, zeby nie ocierac sie o zaden
# z dwudziestu dzialow — zadna nie dotyczy pamieci, wyszukiwania, serwerow ani skryptow.
NEGATYWNE = [
    "where is the online shop checkout and basket",
    "how does the credit card payment flow work",
    "where is the accounting invoice ledger",
    "how do I encode a video file to mp4",
    "where is the 3d scene renderer",
    "how does the turn based combat system work",
    "where are the printer driver settings",
    "how do I sign a blockchain transaction",
    "where is the flight booking calendar widget",
    "how does the spell checker suggest corrections",
    "where is the payroll tax calculation",
    "how do I train a face recognition model",
]


def main():
    cfg = tomllib.load(open(ACAE / "config" / "acae.toml", "rb"))
    loc = FsLocator(
        root=".", roots=cfg["pack"]["roots"],
        prune_dirs=cfg.get("baseline", {}).get("prune_dirs", []),
        max_file_bytes=cfg["pack"]["max_file_bytes"],
    )
    entries, _ = collect_entries(loc, FsReader("."))
    symbole = {str(e["path"]): [str(r["name_path"]) for r in e["symbols"]] for e in entries}

    czesci = sorted((ACAE / "_desc").glob("questions_*.json"))
    if not czesci:
        raise SystemExit("brak zadnej czesci questions_*.json")

    pytania: dict[str, list[str]] = {}
    obce: list[str] = []
    for p in czesci:
        dane = json.loads(p.read_text(encoding="utf-8"))
        for sciezka, lista in dane.items():
            if sciezka not in symbole:
                obce.append(f"{sciezka} ({p.name})")
                continue
            pytania.setdefault(sciezka, []).extend(str(q) for q in lista)

    queries = []
    nr = 0
    for sciezka in sorted(pytania):
        if not symbole[sciezka]:
            # Plik bez symboli — nie da sie na niego trafic, wiec pytanie byloby
            # niemozliwe do zaliczenia niezaleznie od jakosci rankera.
            continue
        for tekst in pytania[sciezka]:
            nr += 1
            queries.append({
                "id": f"w{nr:03d}",
                "kind": "positive",
                "question": tekst,
                "answer_files": [sciezka],
                "answer_symbols": symbole[sciezka],
            })
    for i, tekst in enumerate(NEGATYWNE, 1):
        queries.append({
            "id": f"wn{i:02d}",
            "kind": "negative",
            "question": tekst,
            "answer_files": [],
            "answer_symbols": [],
        })

    cel = ACAE / "tests" / "wide_questions.json"
    cel.write_text(
        json.dumps({"queries": queries}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )
    poz = sum(1 for q in queries if q["kind"] == "positive")
    neg = sum(1 for q in queries if q["kind"] == "negative")
    print(f"czesci wczytane   : {len(czesci)} ({', '.join(p.name for p in czesci)})")
    print(f"plikow z pytaniami: {len(pytania)} ze 169")
    print(f"zapisano {cel}  ->  {poz}+ / {neg}-")
    if obce:
        print(f"UWAGA: {len(obce)} sciezek spoza packa pominietych: {obce[:5]}")


if __name__ == "__main__":
    main()
