"""
SUFIT dla „nie wiem" liczonego z KSZTALTU WYNIKOW (QPP).

Pytanie: czy rozklad ocen w czolowce odroznia pytanie, na ktore odpowiedz ISTNIEJE,
od pytania o rzecz, ktorej w repo NIE MA?

Intuicja z literatury (NQC, Clarity, WIG): gdy wyszukiwanie sie udalo, czolowka jest
ROZWARSTWIONA — jedna rzecz wyraznie wyzej od reszty. Gdy nie ma czego znalezc, wyniki
sa PLASKIE, bo silnik zwraca dziesiec rownie miernych rzeczy, bo musi cos zwrocic.

TO NIE JEST MECHANIZM I NIE MA WERDYKTU WOBEC KRYTERIUM.
--------------------------------------------------------
Zeby z tego zrobic „nie wiem", trzeba postawic PROG. Prog dobrany na szesciu negatywach
jest dokladnie tym pokretlem, ktore uniewaznia cala prerejestracje. Wiec najpierw
tansze pytanie: czy sygnal w ogole istnieje? Ten sam ruch, ktory przed M8 oszczedzil
tydzien (`measure_prose_ceiling.py`: policz, czy proza w ogole istnieje, zanim
zaczniesz na niej trenowac).

Jesli rozklady sie nakladaja — kierunek zamkniety i nie udajemy, ze da sie postawic
granice. Jesli sie rozdzielaja — powstanie osobna prerejestracja z progiem
uzasadnionym strukturalnie.

`k = 10` USTALONE Z GORY, NIE DOBRANE: kryterium `recall@10` istnieje w tym projekcie
od M0, wiec dziesiatka jest liczba pierwotna, starsza od tego pomiaru.

Arytmetyka calkowita, jak wszedzie: zadnych floatow w porzadkowaniu ani w wyniku.
Weryfikacja hasza packa wylaczona swiadomie — to pomiar strukturalny.
"""

import json
import math
import pathlib
import tomllib

from acae.core import collect_entries
from acae.describe import load_descriptions
from acae.embed import StaticEmbedder, symbol_text_with_description
from acae.pack import FsLocator, FsReader

ACAE = pathlib.Path("acae")
K = 10


def odchylenie(wartosci):
    """Odchylenie standardowe w arytmetyce calkowitej. `isqrt` — dokladny pierwiastek."""
    n = len(wartosci)
    if n == 0:
        return 0
    srednia = sum(wartosci) // n
    wariancja = sum((w - srednia) ** 2 for w in wartosci) // n
    return math.isqrt(wariancja)


def main():
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
    wektory = []
    for e in entries:
        p = str(e["path"])
        for row in e["symbols"]:
            wektory.append(embedder.vector(symbol_text_with_description(p, row, opisy.get(p, ""))))
    M = np.vstack(wektory)
    normy = [int(np.dot(v, v)) for v in M]

    def oceny(tekst):
        qv = embedder.vector(tekst)
        nq = int(np.dot(qv, qv))
        if nq == 0:
            return [0] * len(normy)
        il = M @ qv
        out = []
        for d, nd in zip(il, normy):
            d = int(d)
            out.append(0 if d <= 0 or nd == 0 else math.isqrt((10**6 * d * d) // (nq * nd)))
        return out

    wiersze = []
    for q in pytania:
        w = sorted(oceny(q["question"]), reverse=True)
        czolo = w[:K]
        srednia_wszystkich = max(1, sum(w) // len(w))
        sd = odchylenie(czolo)
        wiersze.append({
            "id": q["id"],
            "kind": q["kind"],
            "top1": czolo[0],
            "top10": czolo[-1],
            "spadek": czolo[0] - czolo[-1],
            "srednia_czola": sum(czolo) // K,
            "nqc": (1000 * sd) // srednia_wszystkich,
            "sd": sd,
        })

    poz = [r for r in wiersze if r["kind"] == "positive"]
    neg = [r for r in wiersze if r["kind"] == "negative"]

    def opisz(nazwa, grupa, pole):
        w = sorted(r[pole] for r in grupa)
        return (f"{nazwa:<12} min {w[0]:>5}  mediana {w[len(w)//2]:>5}  "
                f"max {w[-1]:>5}   (n={len(w)})")

    print("=" * 72)
    print("CZY KSZTALT WYNIKOW ODROZNIA 'JEST ODPOWIEDZ' OD 'NIE MA ODPOWIEDZI'?")
    print("=" * 72)
    for pole, tytul in (
        ("nqc", "NQC — rozrzut czolowki znormalizowany (wyzej = pewniej)"),
        ("spadek", "SPADEK — o ile pierwszy wynik gorszy od dziesiatego"),
        ("sd", "ODCHYLENIE w czolowce"),
        ("top1", "TOP1 — najlepszy wynik"),
        ("srednia_czola", "SREDNIA czolowki"),
    ):
        print(f"\n{tytul}")
        print("   " + opisz("pozytywy", poz, pole))
        print("   " + opisz("negatywy", neg, pole))
        pw = sorted(r[pole] for r in poz)
        nw = sorted(r[pole] for r in neg)
        # Ile negatywow lezy PONIZEJ mediany pozytywow — im wiecej, tym lepiej rozdziela
        mediana_poz = pw[len(pw) // 2]
        ponizej = sum(1 for x in nw if x < mediana_poz)
        # Czy da sie w ogole poprowadzic granice: czy najwyzszy negatyw < najnizszy pozytyw
        rozlaczne = nw[-1] < pw[0] or pw[-1] < nw[0]
        print(f"   negatywow ponizej mediany pozytywow: {ponizej} z {len(nw)}"
              f"   |   rozklady rozlaczne: {'TAK' if rozlaczne else 'NIE'}")

    print()
    print("-" * 72)
    print("SZESC PYTAN NEGATYWNYCH — pelne liczby:")
    print("-" * 72)
    print(f"   {'id':<8}{'NQC':>7}{'top1':>7}{'top10':>7}{'spadek':>8}")
    for r in sorted(neg, key=lambda r: r["nqc"]):
        print(f"   {r['id']:<8}{r['nqc']:>7}{r['top1']:>7}{r['top10']:>7}{r['spadek']:>8}")
    print()
    print("   dla porownania, pozytywy o najnizszym NQC:")
    for r in sorted(poz, key=lambda r: r["nqc"])[:6]:
        print(f"   {r['id']:<8}{r['nqc']:>7}{r['top1']:>7}{r['top10']:>7}{r['spadek']:>8}")


if __name__ == "__main__":
    main()
