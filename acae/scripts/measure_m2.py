#!/usr/bin/env python
"""
measure_m2.py — bramka M2.

BRAMKA (decyzja D4 planu)
-------------------------
Dla **co najmniej 8 z 10** zamrozonych zapytan:

    tokens(wycinek outline + dociagniete ciala)  <  B_query(q)

`B_query(q)` pochodzi z baseline'u M0 i opisuje to, co agent robi dzis bez ACAE:
ranking grepowy, top-5 plikow, czytane w calosci. Porownanie jest per zapytanie,
bo pack jest jednym artefaktem wspolnym dla wszystkich zapytan i porownanie 1:1
z suma B_query nie mialoby sensu (to bylo P4/D4 w korekcie planu).

DETERMINIZM
-----------
Te same zasady co w measure_baseline.py: zaden zegar scienny nie trafia do artefaktu,
zadnych floatow (stosunki jako promile calkowite), JSON kanoniczny, zapis bajtowy.

URUCHOMIENIE
    ../venv/Scripts/python.exe scripts/measure_m2.py
    ../venv/Scripts/python.exe scripts/measure_m2.py --out _baseline/m2_run1.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tomllib
from importlib import metadata
from pathlib import Path

ACAE_DIR = Path(__file__).resolve().parent.parent

from acae.canon import canonical_json, content_hash  # noqa: E402
from acae.core import collect_entries  # noqa: E402
from acae.pack import FsLocator, FsReader  # noqa: E402
from acae.retrieve import build_slice  # noqa: E402

SCHEMA = "acae.m2.v1"
REQUIRED_PASSES = 8


def run_git(args: list[str], cwd: Path) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
    )
    return proc.stdout.decode("utf-8", errors="replace").strip()


def find_baseline(explicit: str | None) -> Path:
    """
    Baseline jest JEDEN. Gdy jest ich wiecej, wybor musi byc jawny — cichy wybor
    „najnowszego" ustawialby bramke wobec przypadkowej liczby.
    """
    if explicit:
        return ACAE_DIR / explicit
    found = sorted((ACAE_DIR / "_baseline").glob("baseline_*.json"))
    if len(found) != 1:
        raise SystemExit(
            f"oczekiwano dokladnie jednego _baseline/baseline_*.json, znaleziono {len(found)}; "
            "wskaz plik przez --baseline"
        )
    return found[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Bramka M2 dla ACAE.")
    parser.add_argument("--out", default=None, help="Sciezka wyjsciowa wzgledem acae/.")
    parser.add_argument("--baseline", default=None, help="Plik baseline z M0.")
    parser.add_argument("--outline-limit", type=int, default=40)
    parser.add_argument("--drill", type=int, default=5)
    parser.add_argument("--max-body-lines", type=int, default=200)
    args = parser.parse_args()

    repo_root = ACAE_DIR.parent

    with (ACAE_DIR / "config" / "acae.toml").open("rb") as fh:
        cfg = tomllib.load(fh)
    with (ACAE_DIR / "tests" / "queries.json").open("rb") as fh:
        queries = json.loads(fh.read().decode("utf-8"))["queries"]

    baseline_path = find_baseline(args.baseline)
    baseline = json.loads(baseline_path.read_bytes())
    b_query = {item["id"]: item["tokens"] for item in baseline["b_query"]}

    missing = [q["id"] for q in queries if q["id"] not in b_query]
    if missing:
        raise SystemExit(f"baseline nie zna zapytan: {missing}; przelicz measure_baseline.py")

    import tiktoken

    enc = tiktoken.get_encoding(baseline["tokenizer"]["encoding"])

    # Szkielet budujemy RAZ i uzywamy do wszystkich dziesieciu zapytan.
    # Inaczej kazde zapytanie parsowaloby cale repo od nowa.
    locator = FsLocator(
        root=str(repo_root),
        roots=cfg["pack"]["roots"],
        prune_dirs=cfg.get("baseline", {}).get("prune_dirs", []),
        max_file_bytes=cfg["pack"]["max_file_bytes"],
    )
    reader = FsReader(str(repo_root))
    entries, _skipped = collect_entries(locator, reader)

    results = []
    passed = 0
    for q in queries:
        text, meta = build_slice(
            entries,
            q["text"],
            reader,
            outline_limit=args.outline_limit,
            drill_limit=args.drill,
            max_body_lines=args.max_body_lines,
        )
        tokens = len(enc.encode(text.decode("utf-8"), disallowed_special=()))
        base = b_query[q["id"]]
        ok = tokens < base
        passed += int(ok)
        results.append({
            "id": q["id"],
            "topic": q["topic"],
            "terms": meta["terms"],
            "outline_symbols": meta["outline_symbols"],
            "drilled": meta["drilled"],
            "files": meta["files"],
            "b_query": base,
            "slice_tokens": tokens,
            # Stosunek jako promile calkowite — float nie ma postaci kanonicznej.
            "ratio_permille": (tokens * 1000) // base if base else 0,
            "passed": ok,
        })

    payload = {
        "schema": SCHEMA,
        "head": run_git(["rev-parse", "--short", "HEAD"], repo_root),
        "baseline": {
            "file": baseline_path.name,
            "head": baseline["head"],
            "result_hash": baseline["result_hash"],
        },
        "params": {
            "outline_limit": args.outline_limit,
            "drill_limit": args.drill,
            "max_body_lines": args.max_body_lines,
        },
        "tokenizer": {
            "library": "tiktoken",
            "version": metadata.version("tiktoken"),
            "encoding": baseline["tokenizer"]["encoding"],
        },
        "scope": {"files_in_outline_source": len(entries)},
        "queries": results,
        "passed": passed,
        "required": REQUIRED_PASSES,
        "verdict": "PASS" if passed >= REQUIRED_PASSES else "FAIL",
    }
    payload["result_hash"] = content_hash(canonical_json(payload))

    out_rel = args.out or f"_baseline/m2_{payload['head']}.json"
    out_path = ACAE_DIR / out_rel
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(canonical_json(payload, indent=2))

    print(f"baseline  {baseline_path.name} (HEAD {baseline['head']})")
    print(f"parametry outline<={args.outline_limit}  drill={args.drill}  max_body={args.max_body_lines}")
    print(f"{'zapytanie':<20}{'wycinek':>9}{'B_query':>10}{'udzial':>9}  wynik")
    for item in results:
        mark = "OK " if item["passed"] else "NIE"
        print(
            f"{item['id']:<20}{item['slice_tokens']:>9}{item['b_query']:>10}"
            f"{item['ratio_permille'] / 10:>8.1f}%  {mark}"
        )
    print(f"\nzaliczone {passed}/{len(results)} przy wymaganych {REQUIRED_PASSES} -> {payload['verdict']}")
    print(f"zapis     {out_rel}")
    return 0 if payload["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
