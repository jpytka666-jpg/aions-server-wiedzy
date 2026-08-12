"""
SUFIT dla wlasnych embeddingow trenowanych na naszym korpusie.

Pytanie: czy w ludzkiej prozie tego repo (komunikaty commitow + chunki CBMS) slowa
z pytania w ogole wspolwystepuja z wlasciwym plikiem? Jesli slowo `machine` nigdy nie
pojawia sie w zadnym tekscie wskazujacym pliki od prowieniencji, to zadne trenowanie
tej pary nie nauczy — informacji tam po prostu nie ma.

To jest pomiar SUFITU, nie mechanizmu. Nic nie buduje. Tylko odczyt.
Zbior held-out NIETKNIETY.
"""
import json
import pathlib
import tomllib

from acae.core import collect_entries
from acae.pack import FsLocator, FsReader
from acae.retrieve import query_terms, score_symbol, term_rarity
from acae.scope import ScopeIndex

ACAE = pathlib.Path("acae")


def main():
    cfg = tomllib.loads((ACAE / "config" / "acae.toml").read_text())
    loc = FsLocator(".", cfg["pack"]["roots"], cfg["baseline"]["prune_dirs"], cfg["pack"]["max_file_bytes"])
    reader = FsReader(".")
    entries, _ = collect_entries(loc, reader)
    queries = json.loads((ACAE / "tests" / "dev_questions.json").read_bytes())["queries"]
    pozytywne = [q for q in queries if q["kind"] == "positive"]

    print("buduje indeks prozy (commity + chunki CBMS)...")
    scope = ScopeIndex(entries, reader, ".")

    # Ile w ogole mamy ludzkiej prozy?
    znakow = sum(len(t) for _, t, _ in scope.prose_docs)
    slow_unikalnych = len(scope.prose_index)
    print(f"\n=== ROZMIAR KORPUSU LUDZKIEJ PROZY ===")
    print(f"  dokumentow (commity + chunki) : {len(scope.prose_docs)}")
    print(f"  znakow                        : {znakow}")
    print(f"  unikalnych slow               : {slow_unikalnych}")
    print(f"  dla porownania: sensowny word2vec potrzebuje ~1e8 znakow")

    zerowe, osiagalne_prosto, osiagalne_luzno = [], [], []

    for q in pozytywne:
        terms = query_terms(q["question"])
        rarity = term_rarity(entries, terms)

        # Czy wlasciwy symbol ma leksykalne zero?
        najlepszy = 0
        for e in entries:
            path = str(e["path"])
            for row in e["symbols"]:
                nazwa = str(row["name_path"])
                trafiony = any(
                    nazwa == t or (nazwa.split("/")[-1] == t.split("/")[-1] and path in q["answer_files"])
                    for t in q["answer_symbols"]
                )
                if trafiony:
                    najlepszy = max(najlepszy, score_symbol(path, row, terms, rarity))
        if najlepszy > 0:
            continue

        zerowe.append(q["id"])
        cele = set(q["answer_files"])

        # SUFIT A: ktores slowo pytania wystepuje w prozie wskazujacej wlasciwy plik
        trafione_slowa = sorted({
            t for t in terms
            if cele & set(scope.prose_index.get(t, {}))
        })
        if trafione_slowa:
            osiagalne_prosto.append((q["id"], trafione_slowa))

        # SUFIT B: jakikolwiek dokument prozy wskazuje wlasciwy plik (jest o czym uczyc)
        dokumenty = [ref for ref, _, ref_cele in scope.prose_docs if ref_cele & cele]
        if dokumenty:
            osiagalne_luzno.append((q["id"], len(dokumenty)))

    n = len(zerowe)
    print(f"\n=== GRUPA ZEROWA: {n} pytan ===")
    print(f"\nSUFIT A — slowo z pytania wystepuje w prozie wskazujacej wlasciwy plik:")
    print(f"  {len(osiagalne_prosto)} z {n}")
    for qid, slowa in osiagalne_prosto:
        print(f"    {qid}: {slowa}")

    print(f"\nSUFIT B — jakakolwiek proza w ogole opisuje wlasciwy plik:")
    print(f"  {len(osiagalne_luzno)} z {n}")
    for qid, ile in osiagalne_luzno:
        print(f"    {qid}: {ile} dokumentow")

    bez_niczego = [q for q in zerowe if q not in dict(osiagalne_luzno)]
    print(f"\nNIEOSIAGALNE Z NASZEGO KORPUSU (zero prozy o tych plikach): {len(bez_niczego)} z {n}")
    print(f"  {bez_niczego}")


if __name__ == "__main__":
    main()
