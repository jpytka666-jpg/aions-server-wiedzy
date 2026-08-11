#!/usr/bin/env python
"""
measure_baseline.py — pomiar bazowy M0 dla ACAE.

PO CO TO JEST
-------------
Bramka M1 brzmi "pack ma kosztowac najwyzej polowe tego, co dzisiaj". Bez liczby po
prawej stronie tej nierownosci "polowa" jest kwestia wiary. Ten skrypt liczy te liczbe.

CO LICZY
--------
B_ceiling  — suma tokenow WSZYSTKICH plikow w zakresie. Koszt zrzutu calosci.
B_query(q) — koszt dzisiejszego wejscia w kod dla zapytania q: ranking grepowy po
             terminach zapytania -> top-K plikow -> czytane w calosci -> suma tokenow.
             To jest dokladnie to, co robi dzis agent bez ACAE: Grep, potem Read.

DETERMINIZM (bramka M0)
-----------------------
Dwa uruchomienia pod rzad musza dac plik identyczny co do bajta. Dlatego:
  - zaden zegar scienny nie trafia do artefaktu; provenancja to SHA HEAD i czas commita,
  - kolejnosc plikow to sort po sciezce POSIX wzglednej wobec repo, porownanie bajtowe,
  - zaden float; wszystkie miary sa calkowite,
  - remisy w rankingu rozstrzyga sciezka, nigdy kolejnosc z systemu plikow,
  - JSON z sort_keys, zapis bajtowy (bez translacji koncow linii na Windows).

ZAKRES
------
Rozszerzenia bierzemy z LANGS w aions_core/server/ts_symbols.py — z importu, nie z kopii.
To celowe: pack z M1 obejmuje pliki, dla ktorych istnieje gramatyka, wiec B_ceiling musi
obejmowac dokladnie ten sam zbior. Inaczej bramka "<= 0,5 x B_ceiling" porownuje polowe
jednej rzeczy z caloscia innej.

URUCHOMIENIE
    ../venv/Scripts/python.exe scripts/measure_baseline.py
    ../venv/Scripts/python.exe scripts/measure_baseline.py --out _baseline/run1.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tomllib
from importlib import metadata
from pathlib import Path

# acae/scripts/measure_baseline.py -> acae/ -> korzen repo
ACAE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = ACAE_DIR.parent

# ts_symbols.py lezy w repo, nie w acae/. Import, nie kopia (regula ADDITIVE ONLY).
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from aions_core.server.ts_symbols import LANGS  # noqa: E402

import tiktoken  # noqa: E402

SCHEMA = "acae.baseline.v1"

# Slowa, ktore w zapytaniu w jezyku naturalnym sa szumem: trafiaja wszedzie i nie
# niosa sygnalu o tym, ktory plik jest wlasciwy. Zamrozone razem z queries.json —
# zmiana tej listy zmienia ranking, wiec uniewaznia baseline.
STOPWORDS = frozenset({
    "and", "are", "back", "does", "every", "for", "from", "how", "its", "not",
    "the", "this", "that", "them", "then", "there", "was", "were", "what",
    "when", "where", "which", "who", "why", "with",
})

TERM_RE = re.compile(r"[a-z0-9_]+")


def run_git(args: list[str]) -> str:
    """Wolanie gita w korzeniu repo. Podnosi wyjatek na kazdym niezerowym wyjsciu."""
    proc = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return proc.stdout.decode("utf-8", errors="replace").strip()


def submodule_paths() -> list[str]:
    """
    Sciezki submodulow wg indeksu gita (wpisy o trybie 160000, tzw. gitlink).

    Submodul to OSOBNE repozytorium. Jego tresc nie jest odtwarzalna z tego repo,
    a git check-ignore odmawia obslugi jakiejkolwiek sciezki w jego wnetrzu. Wchodzi
    wiec do raportu pominiec, nie do zakresu.
    """
    out = run_git(["ls-files", "--stage"])
    paths = []
    for line in out.split("\n"):
        if not line.startswith("160000 "):
            continue
        # format: <mode> <sha> <stage>\t<sciezka>
        _, _, rest = line.partition("\t")
        if rest:
            paths.append(rest.strip())
    return sorted(paths)


def gitignored(rel_paths: list[str]) -> set[str]:
    """
    Ktore z podanych sciezek git uznaje za ignorowane.

    Git jest autorytetem dla wlasnego formatu — wlasna implementacja .gitignore
    to czwarta kopia tej samej rzeczy i zrodlo cichych rozjazdow.
    """
    if not rel_paths:
        return set()
    payload = "\0".join(rel_paths).encode("utf-8") + b"\0"
    proc = subprocess.run(
        ["git", "check-ignore", "--stdin", "-z"],
        cwd=REPO_ROOT,
        input=payload,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # 0 = cos jest ignorowane, 1 = nic nie jest. Wszystko inne to blad gita.
    if proc.returncode not in (0, 1):
        raise RuntimeError(
            f"git check-ignore zwrocil {proc.returncode}: "
            f"{proc.stderr.decode('utf-8', errors='replace')}"
        )
    return {p for p in proc.stdout.decode("utf-8").split("\0") if p}


def query_terms(text: str, min_len: int) -> list[str]:
    """
    Rozbior zapytania na terminy do wyszukania.

    Regula: male litery, rozbicie na [a-z0-9_]+, odrzucenie terminow krotszych niz
    min_len i slow z STOPWORDS, deduplikacja, sort. Sort jest po to, zeby kolejnosc
    terminow nie zalezala od kolejnosci slow w zdaniu — wynik i tak jest suma.
    """
    terms = {
        t for t in TERM_RE.findall(text.lower())
        if len(t) >= min_len and t not in STOPWORDS
    }
    return sorted(terms)


def collect_files(roots: list[str], prune_dirs: set[str], max_bytes: int) -> tuple[list[str], dict]:
    """
    Zbiera pliki w zakresie. Zwraca (posortowane sciezki POSIX wzgledne, raport pominiec).

    Kolejnosc wyjscia pochodzi z sorted() po sciezce POSIX, nigdy z systemu plikow.
    To jest dokladnie ta wlasnosc, ktorej brakuje scan_dir() w ts_symbols.py (:275-283).
    """
    candidates: list[str] = []
    too_large: list[dict] = []
    missing_roots: list[str] = []
    in_submodule: list[str] = []

    submodules = submodule_paths()
    sub_prefixes = tuple(f"{s}/" for s in submodules)

    for root in roots:
        root_dir = REPO_ROOT / root
        if not root_dir.is_dir():
            missing_roots.append(root)
            continue
        for path in root_dir.rglob("*"):
            if not path.is_file():
                continue
            rel_parts = path.relative_to(REPO_ROOT).parts
            if any(part in prune_dirs for part in rel_parts[:-1]):
                continue
            if path.suffix.lower() not in LANGS:
                continue
            rel = path.relative_to(REPO_ROOT).as_posix()
            size = path.stat().st_size
            if size > max_bytes:
                too_large.append({"path": rel, "bytes": size})
                continue
            candidates.append(rel)

    candidates.sort()
    ignored = gitignored(candidates)
    kept = [p for p in candidates if p not in ignored]

    report = {
        "gitignored": sorted(ignored),
        "too_large": sorted(too_large, key=lambda d: d["path"]),
        "missing_roots": sorted(missing_roots),
    }
    return kept, report


def score_file(content_lower: str, lines_lower: list[str], terms: list[str]) -> int:
    """
    Ile linii pliku trafia w terminy zapytania — sumarycznie po terminach.

    Liczymy LINIE, nie wystapienia, bo to robi grep i to widzi agent w wynikach.
    Brama `term in content_lower` przed skanem linii odcina wiekszosc pracy: wiekszosc
    terminow nie wystepuje w wiekszosci plikow, a sprawdzenie calego pliku jest jednym
    przejsciem w C zamiast petli po liniach w Pythonie.
    """
    present = [t for t in terms if t in content_lower]
    if not present:
        return 0
    score = 0
    for line in lines_lower:
        for term in present:
            if term in line:
                score += 1
    return score


def canonical_bytes(obj: object) -> bytes:
    """JSON kanoniczny: klucze posortowane, bez ASCII-escape, konce linii wymuszone na \\n."""
    text = json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=2)
    return text.encode("utf-8") + b"\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Pomiar bazowy M0 dla ACAE.")
    parser.add_argument(
        "--out",
        default=None,
        help="Sciezka wyjsciowa wzgledem acae/. Domyslnie _baseline/baseline_<SHA>.json",
    )
    args = parser.parse_args()

    with (ACAE_DIR / "config" / "acae.toml").open("rb") as fh:
        cfg = tomllib.load(fh)
    pack_cfg = cfg["pack"]
    base_cfg = cfg["baseline"]

    with (ACAE_DIR / "tests" / "queries.json").open("rb") as fh:
        queries_doc = json.loads(fh.read().decode("utf-8"))
    queries = queries_doc["queries"]

    top_k = base_cfg["top_k"]
    min_term_len = base_cfg["min_term_len"]
    prune_dirs = set(base_cfg["prune_dirs"])
    max_bytes = pack_cfg["max_file_bytes"]

    head = run_git(["rev-parse", "--short", "HEAD"])
    head_full = run_git(["rev-parse", "HEAD"])
    head_committed_at = run_git(["log", "-1", "--format=%cI"])

    files, skipped = collect_files(pack_cfg["roots"], prune_dirs, max_bytes)

    enc = tiktoken.get_encoding(base_cfg["tokenizer"])
    terms_by_query = {q["id"]: query_terms(q["text"], min_term_len) for q in queries}

    tokens_by_file: dict[str, int] = {}
    scores: dict[str, dict[str, int]] = {q["id"]: {} for q in queries}
    unreadable: list[dict] = []
    ceiling = 0

    for rel in files:
        path = REPO_ROOT / rel
        try:
            raw = path.read_bytes()
        except OSError as exc:
            unreadable.append({"path": rel, "error": type(exc).__name__})
            continue
        # errors="replace" jest stratne, ale deterministyczne: ten sam bajt zawsze
        # daje ten sam znak zastepczy, wiec liczba tokenow sie nie chwieje.
        text = raw.decode("utf-8", errors="replace")
        # disallowed_special=() — bez tego tiktoken wyrzuca wyjatek na pliku, ktory
        # zawiera doslowny tekst tokenu specjalnego. W repo z promptami to realne.
        n_tokens = len(enc.encode(text, disallowed_special=()))
        tokens_by_file[rel] = n_tokens
        ceiling += n_tokens

        lower = text.lower()
        lines_lower = lower.split("\n")
        for qid, terms in terms_by_query.items():
            score = score_file(lower, lines_lower, terms)
            if score:
                scores[qid][rel] = score

    per_query = []
    for q in queries:
        qid = q["id"]
        # Remis rozstrzyga sciezka POSIX rosnaco — nigdy kolejnosc z systemu plikow.
        ranked = sorted(scores[qid].items(), key=lambda kv: (-kv[1], kv[0]))[:top_k]
        top_files = [
            {"path": rel, "score": score, "tokens": tokens_by_file[rel]}
            for rel, score in ranked
        ]
        per_query.append({
            "id": qid,
            "topic": q["topic"],
            "text": q["text"],
            "terms": terms_by_query[qid],
            "matched_files": len(scores[qid]),
            "top_files": top_files,
            "tokens": sum(f["tokens"] for f in top_files),
        })

    payload = {
        "schema": SCHEMA,
        "head": head,
        "head_full": head_full,
        "head_committed_at": head_committed_at,
        "note": (
            "Brak pola z czasem uruchomienia jest celowy: bramka M0 wymaga plikow "
            "identycznych co do bajta miedzy uruchomieniami, wiec zegar scienny nie "
            "moze trafic do artefaktu. Provenancje niesie head_committed_at."
        ),
        "tokenizer": {
            "library": "tiktoken",
            "version": metadata.version("tiktoken"),
            "encoding": base_cfg["tokenizer"],
        },
        "pinned_packages": {
            name: metadata.version(name)
            for name in ("tree-sitter", "tree-sitter-language-pack", "tiktoken")
        },
        "scope": {
            "roots": pack_cfg["roots"],
            "extensions": sorted(LANGS),
            "max_file_bytes": max_bytes,
            "prune_dirs": sorted(prune_dirs),
            "file_count": len(files),
            "skipped": {**skipped, "unreadable": sorted(unreadable, key=lambda d: d["path"])},
        },
        "ranking": {
            "top_k": top_k,
            "min_term_len": min_term_len,
            "match": "literal, case-insensitive, liczone linie trafione na termin",
            "tie_break": "sciezka POSIX rosnaco",
            "stopwords": sorted(STOPWORDS),
        },
        "b_ceiling": {"files": len(files), "tokens": ceiling},
        "b_query": per_query,
        "b_query_sum": sum(item["tokens"] for item in per_query),
    }
    payload["result_hash"] = "blake2b256:" + hashlib.blake2b(
        canonical_bytes(payload), digest_size=32
    ).hexdigest()

    out_rel = args.out or f"_baseline/baseline_{head}.json"
    out_path = ACAE_DIR / out_rel
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(canonical_bytes(payload))

    print(f"HEAD          {head} ({head_committed_at})")
    print(f"pliki         {len(files)}")
    print(f"B_ceiling     {ceiling} tokenow")
    print(f"B_query suma  {payload['b_query_sum']} tokenow w {len(per_query)} zapytaniach")
    for item in per_query:
        print(f"  {item['id']:<18} {item['tokens']:>8} tok   trafien: {item['matched_files']}")
    print(f"bramka M1     content.txt <= {ceiling // 2} tokenow")
    print(f"zapis         {out_rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
