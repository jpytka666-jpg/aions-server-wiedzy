#!/usr/bin/env python3
"""
Uruchamia jeden przebieg CRLA i przepuszcza wynik przez bramke Pocket QC.

PO CO TO ISTNIEJE
Pocket QC nie jest usluga. To biblioteka, ktora pisze do logu tylko wtedy, gdy
ktos ja zawola. Miedzy 16 sierpnia a 21 wrzesnia 2026 nikt jej nie wolal, wiec
log stal w miejscu i wygladalo to tak, jakby uklad odpornosciowy byl zepsuty.
Nie byl. Nie mial czego sprawdzac.

Ten plik jest najmniejsza rzecza, ktora zamienia Pocket QC z biblioteki w cos,
co da sie uruchomic z jednej linijki i z harmonogramu.

UZYCIE
    python tools/uruchom_pocket_qc.py "pytanie"
    python tools/uruchom_pocket_qc.py          # pytanie domyslne

Kod wyjscia: 0 gdy bramka wydala werdykt (jakikolwiek), 2..5 gdy lancuch pekl
na konkretnym etapie. Werdykt RETRY to NIE jest blad programu. To jest bramka
robiaca swoja robote.

Wynik ladzie w aions_core/logs/pocket_qc.jsonl, jedna linia na przebieg.\nWerdykt zawiera pole history: KNOWN vs UNKNOWN_NOT_PROVEN_NEW, aby stary defect\nnie byl przedstawiany jako nowe odkrycie.
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(ROOT))

PYTANIE_DOMYSLNE = "Czym jest CBMS i jak adresuje pamiec?"


def main(argv: list[str]) -> int:
    pytanie = argv[1] if len(argv) > 1 else PYTANIE_DOMYSLNE

    try:
        from cbms_memory import CBMSMemory
        from crla_core import run_crla
        from pocket_qc import qc_crla_result
    except Exception:
        traceback.print_exc()
        print("ETAP: import", file=sys.stderr)
        return 2

    pamiec = ROOT / "memory"

    try:
        cbms = CBMSMemory(memory_dir=str(pamiec))
    except Exception:
        traceback.print_exc()
        print("ETAP: budowa CBMSMemory", file=sys.stderr)
        return 3

    try:
        wynik = run_crla(cbms, pytanie, seed=123, n_candidates=4)
    except Exception:
        traceback.print_exc()
        print("ETAP: run_crla", file=sys.stderr)
        return 4

    try:
        werdykt = qc_crla_result(wynik, str(pamiec))
    except Exception:
        traceback.print_exc()
        print("ETAP: qc_crla_result", file=sys.stderr)
        return 5

    print(json.dumps(werdykt, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
