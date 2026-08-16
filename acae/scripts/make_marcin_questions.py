"""
Zestaw pytan MARCINA — sprawdzian uzytecznosci, NIE egzamin.

Pytania napisal Marcin swoimi slowami (2026-08-16), reagujac na to, ze przez tydzien
mierzylem narzedzie na zbiorze wygenerowanym przez agenta z instrukcja „opisuj
zachowanie, NIE nazywaj symboli" — czyli zrobionym specjalnie tak, zeby bylo trudno.
Jego zdanie: tak nikt nie pyta.

CZYM TEN ZBIOR SIE ROZNI OD ZAMROZONEGO — trzy rzeczy, wszystkie na niekorzysc dowodu
--------------------------------------------------------------------------------------
1. **To nie jest slepa proba.** Klucz odpowiedzi ustalilem ja, znajac korpus. Zamrozony
   zbior pisal agent, ktory kodu nie widzial. Wynik stad NIE jest porownywalny
   z dwudziestoma trzema pomiarami i nie wolno go wstawiac do tamtej tabeli.
2. **Trafienie liczone na poziomie PLIKU, nie symbolu.** `answer_symbols` to WSZYSTKIE
   symbole wlasciwego pliku, wiec wystarczy, ze ranker wskaze cokolwiek z tego pliku.
   Zamrozony zbior wymaga konkretnego symbolu. Ten prog jest znacznie lagodniejszy
   i tak trzeba go czytac.
3. **Zbior jest maly** — 10 pozytywow i 3 negatywy. Jedno pytanie to 10 punktow
   procentowych, wiec pojedyncze trafienie przesuwa wynik mocno.

PO CO WIEC W OGOLE
------------------
Zeby odpowiedziec na pytanie, ktorego nie zadalismy ani razu: **czy to narzedzie jest
uzyteczne dla Marcina TERAZ**, niezaleznie od tego, ze nie przechodzi kryterium
na zbiorze zbudowanym po to, zeby bylo trudno.

DWIE WERSJE JEZYKOWE — to jest drugi, moze wazniejszy powod
------------------------------------------------------------
Marcin pyta PO POLSKU. Opisy plikow, model wektorowy i przesiewacz sa PO ANGIELSKU.
Ta sama tresc jest wiec zapisana w dwoch wersjach: jego wlasnej i angielskim
odpowiedniku o tym samym znaczeniu.

Jesli wersja angielska dziala, a polska nie — to nie jest problem wyszukiwania,
tylko jezyka. I wtedy caly tydzien mierzylem nie ten problem.
"""

import json
import pathlib
import tomllib

from acae.core import collect_entries
from acae.pack import FsLocator, FsReader

ACAE = pathlib.Path("acae")

# (id, pytanie Marcina, angielski odpowiednik o tym samym znaczeniu, plik z odpowiedzia)
POZYTYWNE = [
    ("m01", "gdzie jest mapa lasu",
     "where is the map of what projects exist on the drives",
     "scripts/full_system_scan.py"),
    ("m02", "co jest kurwa zawiecha",
     "what detects and fixes system problems automatically",
     "control_plane/operator/loop.py"),
    ("m03", "czym sprawdze co mam na dyskach",
     "what makes an inventory of knowledge data across drives",
     "scripts/catalog_e_treasures.py"),
    ("m04", "sprawdz czy aions dziala",
     "how do I check the system is alive and see recorded errors",
     "aions_core/tools/check_status.py"),
    ("m05", "czy jestes podlonczony",
     "how do I test that the tool server responds over http",
     "scripts/smoke_http_mcp.py"),
    ("m06", "czemu mi nie pamieta rozmowy",
     "what records and recalls conversations for later context",
     "aions_core/server/conversation_memory.py"),
    ("m07", "gdzie sie kurwa zapisuja te chunki",
     "where are knowledge chunks saved to disk",
     "aions_core/server/cbms_memory.py"),
    ("m08", "co robi to esperanto",
     "what normalizes polish and english text into a neutral form",
     "aions_core/server/esperanto_bridge.py"),
    ("m09", "czemu mi mowi ze nie wie",
     "what decides to refuse instead of answering",
     "aions_core/server/crla_core.py"),
    ("m10", "gdzie sie sprawdza czy odpowiedz jest dobra",
     "what checks answer quality before it is accepted",
     "aions_core/server/pocket_qc.py"),
]

# Kontrola negatywna — rzeczy, ktorych w tym repo NIE MA.
NEGATYWNE = [
    ("m91", "gdzie jest ten moj sklep internetowy",
     "where is the online shop checkout and product catalogue"),
    ("m92", "jak sie loguje przez fejsbuka",
     "how does facebook social login work here"),
    ("m93", "gdzie sa faktury z ksiegowosci",
     "where is the accounting invoice ledger"),
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

    brak = [f for _, _, _, f in POZYTYWNE if f not in symbole]
    if brak:
        raise SystemExit(f"pliki spoza packa: {brak}")
    puste = [f for _, _, _, f in POZYTYWNE if not symbole[f]]
    if puste:
        raise SystemExit(f"pliki bez symboli, nie da sie na nie trafic: {puste}")

    for nazwa, polski in (("marcin_pl", True), ("marcin_en", False)):
        queries = []
        for qid, pl, en, plik in POZYTYWNE:
            queries.append({
                "id": qid,
                "kind": "positive",
                "question": pl if polski else en,
                "answer_files": [plik],
                # WSZYSTKIE symbole pliku — trafienie liczone na poziomie pliku.
                "answer_symbols": symbole[plik],
            })
        for qid, pl, en in NEGATYWNE:
            queries.append({
                "id": qid,
                "kind": "negative",
                "question": pl if polski else en,
                "answer_files": [],
                "answer_symbols": [],
            })
        cel = ACAE / "tests" / f"{nazwa}_questions.json"
        cel.write_text(
            json.dumps({"queries": queries}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8", newline="\n",
        )
        poz = sum(1 for q in queries if q["kind"] == "positive")
        neg = sum(1 for q in queries if q["kind"] == "negative")
        print(f"{cel}  ->  {poz}+ / {neg}-")


if __name__ == "__main__":
    main()
