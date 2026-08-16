"""
M16 — czy turniej CRLA ma w ogole co wygrywac.

Pomiar wykonany DOKLADNIE wedlug prerejestracji z .now/STATE.md (2026-08-16T12:30).
Kryterium bylo zapisane PRZED napisaniem tego pliku i nie jest tu zmieniane.

WARUNEK KONIECZNY  : mediana liczby ROZNYCH odpowiedzi wsrod 8 kandydatow >= 3
WARUNEK DRUGI      : >= 25% pytan ma kandydata przechodzacego bramke `learning_gate`
                     tam, gdzie pojedyncze wywolanie jej NIE przechodzi

Bramka jest sedzia niezaleznym: zmierzona osobno (0 falszywych alarmow na 164 blokach),
nie wie nic o turnieju i nie zostala pod niego dotknieta.

BEZPIECZENSTWO: `cbms_think` moze wolac `create_knowledge_chunk`, wiec 270 wywolan
zapisywaloby do zywej bazy. Pomiar dziala na KOPII wskazanej przez --memory.
"""

import argparse
import json
import pathlib
import statistics
import sys


def zbuduj_pytania(chunks_dir: pathlib.Path, ile: int) -> list[str]:
    """
    30 pojec z blokow bazy, alfabetycznie, pierwsze unikalne.

    ZASTRZEZENIE, ktore musi isc razem z wynikiem: pytania pochodza z tej samej bazy,
    ktora przeszukujemy, wiec wynik jest ZAWYZONY. Sluzy do znalezienia sufitu,
    nie do porownan z czymkolwiek innym.
    """
    pojecia = set()
    for p in sorted(chunks_dir.glob("*.json")):
        try:
            c = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        k = (c.get("concept") or "").strip()
        if k:
            pojecia.add(k)
    return sorted(pojecia)[:ile]


def kawalki(lista: list[str], n: int) -> list[list[str]]:
    """Rozlaczne kawalki listy blokow — kandydat i dostaje i-ty. Zero losowosci."""
    if not lista:
        return [[] for _ in range(n)]
    rozmiar = max(1, len(lista) // n)
    out = [lista[i * rozmiar:(i + 1) * rozmiar] for i in range(n)]
    return [k for k in out]


def main() -> int:
    ap = argparse.ArgumentParser(description="M16: sufit turnieju CRLA.")
    ap.add_argument("--memory", required=True, help="KOPIA katalogu pamieci, nie zywa baza.")
    ap.add_argument("--server", required=True, help="Katalog aions_core/server.")
    ap.add_argument("--pytania", type=int, default=30)
    ap.add_argument("--kandydatow", type=int, default=8)
    ap.add_argument("--json-out", default="")
    args = ap.parse_args()

    sys.path.insert(0, args.server)
    from cbms_memory import CBMSMemory  # noqa: E402

    mem_dir = pathlib.Path(args.memory)
    pytania = zbuduj_pytania(mem_dir / "chunks", args.pytania)
    m = CBMSMemory(memory_dir=str(mem_dir))

    wiersze = []
    for q in pytania:
        baza = m.cbms_think(q)
        odp_baza = (baza.get("answer") or "")
        bloki = [str(x) for x in (baza.get("chunk_references") or [])]
        baza_przechodzi = m.learning_gate(odp_baza)[0]

        odpowiedzi, przechodzacy = [], 0
        for ctx in kawalki(bloki, args.kandydatow):
            r = m.cbms_think(q, context=ctx)
            a = (r.get("answer") or "")
            odpowiedzi.append(a)
            if m.learning_gate(a)[0]:
                przechodzacy += 1

        wiersze.append({
            "pytanie": q,
            "blokow_w_bazowym": len(bloki),
            "roznych_odpowiedzi": len(set(odpowiedzi)),
            "baza_przechodzi_bramke": baza_przechodzi,
            "kandydatow_przechodzacych": przechodzacy,
            "wygrana": (not baza_przechodzi) and przechodzacy > 0,
        })

    rozne = [w["roznych_odpowiedzi"] for w in wiersze]
    mediana = statistics.median(rozne) if rozne else 0
    wygrane = sum(1 for w in wiersze if w["wygrana"])
    udzial = wygrane / len(wiersze) if wiersze else 0.0

    kon_ok = mediana >= 3
    drugi_ok = udzial >= 0.25

    print(f"pytan: {len(wiersze)}   kandydatow na pytanie: {args.kandydatow}")
    print()
    print("WARUNEK KONIECZNY  mediana roznych odpowiedzi >= 3")
    print(f"   zmierzone: {mediana}   rozklad: {sorted(set(rozne))}"
          f"   -> {'SPELNIONY' if kon_ok else 'NIESPELNIONY'}")
    print()
    if kon_ok:
        print("WARUNEK DRUGI      >= 25% pytan z wygrana kandydata nad bazowym")
        print(f"   zmierzone: {wygrane}/{len(wiersze)} = {udzial:.1%}"
              f"   -> {'SPELNIONY' if drugi_ok else 'NIESPELNIONY'}")
    else:
        print("WARUNEK DRUGI      nie liczony — pierwszy nie przeszedl,")
        print("                   wiec turniej nie ma z czego wybierac.")
    print()
    ile_baza = sum(1 for w in wiersze if w["baza_przechodzi_bramke"])
    print(f"na marginesie: odpowiedz pojedynczego wywolania przechodzi bramke "
          f"w {ile_baza}/{len(wiersze)} pytan")
    print()
    print("WERDYKT:", "PRZYJETY" if (kon_ok and drugi_ok) else "ODRZUCONY")

    if args.json_out:
        pathlib.Path(args.json_out).write_text(
            json.dumps({
                "kryterium": {"mediana_roznych_odpowiedzi_min": 3, "udzial_wygranych_min": 0.25},
                "zmierzone": {"mediana_roznych_odpowiedzi": mediana, "udzial_wygranych": udzial,
                              "baza_przechodzi_bramke": ile_baza},
                "warunek_konieczny": kon_ok, "warunek_drugi": drugi_ok,
                "werdykt": "PRZYJETY" if (kon_ok and drugi_ok) else "ODRZUCONY",
                "wiersze": wiersze,
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"pelny wynik: {args.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
