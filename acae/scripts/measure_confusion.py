"""
DIAGNOZA: czy zle odpowiedzi biora sie z BALAGANU, czy z DZIEDZINOWOSCI?

Pytanie Marcina, postawione jego slowami: bibliotekarz nie odroznia oleju silnikowego
od slonecznikowego, wiec podaje ksiazke kucharska przy pytaniu o silnik. Czy tak jest
naprawde?

Dwie mozliwosci daja zupelnie rozne wnioski:
  A. DZIEDZINOWOSC — zle odpowiedzi sa SKUPIONE, tylko nie w tym miejscu co trzeba.
     Bibliotekarz poszedl na zla polke i konsekwentnie z niej podaje. Wtedy warstwa
     dziedzin ma sens: wystarczy skierowac go na wlasciwa polke.
  B. BALAGAN — zle odpowiedzi sa ROZRZUCONE po calej bibliotece bez wspolnego mianownika.
     Wtedy nie ma „zlej polki" do naprawienia i warstwa dziedzin nic nie da.

Ten skrypt NICZEGO NIE BUDUJE. Tylko patrzy i liczy. Wzorzec ten sam co przy
`measure_prose_ceiling.py`: zmierz sufit, zanim zbudujesz mechanizm.

CO LICZYMY, zeby nie bylo to moim osadem
----------------------------------------
Dla kazdego pytania bierzemy dziesiec pierwszych odpowiedzi obecnego najlepszego
rankera (embedding + opisy) i sprawdzamy:
  * z ilu ROZNYCH katalogow pochodza — malo katalogow znaczy „skupione",
    duzo znaczy „rozrzucone",
  * czy wsrod nich jest w ogole katalog, w ktorym lezy wlasciwa odpowiedz,
  * ile z dziesieciu pochodzi z jednego, dominujacego katalogu.
Porownujemy pytania NIEUDANE z UDANYMI — bez tego porownania liczba „3 katalogi"
nic nie znaczy.

OGRANICZENIE, ktore odnotowuje jawnie
-------------------------------------
To jest kolejne spojrzenie na zbior roboczy (siedemnaste). Wolno mi z niego postawic
DIAGNOZE, nie wolno stroic pod niego zadnego progu. Jesli powstanie warstwa dziedzin,
musi byc pisana BEZ ogladania tych pytan — tak jak powstaly opisy.

Weryfikacja hasza packa jest tu WYLACZONA swiadomie: to pomiar strukturalny,
a nie porownawczy, i dwa pliki serwera zmienily sie po naprawie echa.
"""

import json
import pathlib
import tomllib
from collections import Counter

from acae.core import collect_entries
from acae.describe import load_descriptions
from acae.embed import StaticEmbedder, symbol_text_with_description
from acae.pack import FsLocator, FsReader

ACAE = pathlib.Path("acae")
TOP = 10


def katalog(sciezka: str, poziomy: int = 2) -> str:
    """Katalog jako przyblizenie dziedziny. Dwa poziomy, np. `aions_core/server`."""
    czesci = sciezka.split("/")[:-1]
    return "/".join(czesci[:poziomy]) if czesci else "(korzen)"


def main():
    # Uruchamiane z korzenia repo, jak `measure_prose_ceiling.py`.
    root = pathlib.Path(".").resolve()
    cfg = tomllib.load(open(ACAE / "config" / "acae.toml", "rb"))
    loc = FsLocator(
        root=str(root), roots=cfg["pack"]["roots"],
        prune_dirs=cfg.get("baseline", {}).get("prune_dirs", []),
        max_file_bytes=cfg["pack"]["max_file_bytes"],
    )
    entries, _ = collect_entries(loc, FsReader(str(root)))
    opisy, _ = load_descriptions(ACAE / "_desc" / "descriptions.json")
    pytania = json.loads((ACAE / "tests" / "dev_questions.json").read_bytes())["queries"]

    import numpy as np
    embedder = StaticEmbedder(ACAE / "_model")
    items, wektory = [], []
    for e in entries:
        p = str(e["path"])
        for row in e["symbols"]:
            items.append((p, row))
            wektory.append(embedder.vector(symbol_text_with_description(p, row, opisy.get(p, ""))))
    M = np.vstack(wektory)
    normy = [int(np.dot(v, v)) for v in M]

    def ranking(tekst):
        import math
        qv = embedder.vector(tekst)
        nq = int(np.dot(qv, qv))
        if nq == 0:
            return list(range(len(items)))
        il = M @ qv
        wyniki = []
        for d, nd in zip(il, normy):
            d = int(d)
            wyniki.append(0 if d <= 0 or nd == 0 else math.isqrt((10**6 * d * d) // (nq * nd)))
        return sorted(range(len(items)), key=lambda i: (-wyniki[i], items[i][0], items[i][1]["line"]))

    def trafiony(i, q):
        p, row = items[i]
        n = str(row["name_path"])
        return any(
            n == t or (n.split("/")[-1] == t.split("/")[-1] and p in q["answer_files"])
            for t in q["answer_symbols"]
        )

    udane, nieudane = [], []
    for q in pytania:
        if q["kind"] != "positive":
            continue
        kolejnosc = ranking(q["question"])
        czolowka = kolejnosc[:TOP]
        pozycja = next((k for k, i in enumerate(kolejnosc, 1) if trafiony(i, q)), 0)

        katalogi = [katalog(items[i][0]) for i in czolowka]
        licznik = Counter(katalogi)
        wlasciwe = {katalog(f) for f in q["answer_files"]}
        wpis = {
            "id": q["id"],
            "pozycja": pozycja,
            "roznych_katalogow": len(licznik),
            "dominujacy": licznik.most_common(1)[0],
            "wlasciwy_katalog_obecny": bool(set(katalogi) & wlasciwe),
            "wlasciwe": sorted(wlasciwe),
            "czolowe_katalogi": licznik.most_common(3),
        }
        (udane if pozycja and pozycja <= TOP else nieudane).append(wpis)

    def podsumuj(nazwa, grupa):
        if not grupa:
            print(f"{nazwa}: brak")
            return
        r = sorted(w["roznych_katalogow"] for w in grupa)
        d = sorted(w["dominujacy"][1] for w in grupa)
        obecny = sum(1 for w in grupa if w["wlasciwy_katalog_obecny"])
        print(f"{nazwa} ({len(grupa)} pytan):")
        print(f"   roznych katalogow w czolowce : mediana {r[len(r)//2]} (od {r[0]} do {r[-1]})")
        print(f"   ile z {TOP} z jednego katalogu : mediana {d[len(d)//2]}")
        print(f"   wlasciwy katalog w czolowce   : {obecny} z {len(grupa)}")

    print("=" * 66)
    print("CZY ZLE ODPOWIEDZI SA SKUPIONE (dziedzina), CZY ROZRZUCONE (balagan)?")
    print("=" * 66)
    print()
    podsumuj("PYTANIA UDANE   (odpowiedz w pierwszej dziesiatce)", udane)
    print()
    podsumuj("PYTANIA NIEUDANE (odpowiedzi brak)", nieudane)
    print()
    print("-" * 66)
    print("SZCZEGOLY PYTAN NIEUDANYCH — gdzie poszedl bibliotekarz:")
    print("-" * 66)
    for w in nieudane:
        znak = "TAK" if w["wlasciwy_katalog_obecny"] else "NIE"
        print(f"\n  {w['id']}  (wlasciwa odpowiedz na pozycji {w['pozycja'] or 'poza rankingiem'})")
        print(f"     powinien szukac w : {', '.join(w['wlasciwe'])}")
        print(f"     szukal w          : {', '.join(f'{k} ({n})' for k, n in w['czolowe_katalogi'])}")
        print(f"     trafil na wlasciwa polke: {znak}")


if __name__ == "__main__":
    main()
