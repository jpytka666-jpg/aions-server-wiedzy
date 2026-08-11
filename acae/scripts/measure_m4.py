#!/usr/bin/env python
"""
measure_m4.py — ablacja M4. Kazdy etap mierzony OSOBNO, wobec kryterium zapisanego wczesniej.

CO MIERZY
---------
recall@10 / recall@25 — czy prawdziwy symbol w ogole wpadl do wycinka
MRR                   — jak wysoko; symbol na 24. pozycji jest formalnie trafiony,
                        a praktycznie nie, i tylko MRR to widzi
kontrola negatywna    — 6 pytan o funkcjonalnosc, ktorej w repo NIE MA. Mierzymy stosunek
                        sredniego najlepszego wyniku na negatywach do tego na pozytywach.
                        Bez tej liczby „semantic retrieval" i „rozszerzam agresywnie, wiec
                        cos zawsze trafie" wygladaja identycznie.

DLACZEGO STOSUNEK, A NIE SUROWY WYNIK
-------------------------------------
Warianty rankera maja rozne skale (BM25F liczy logarytmy, poprzedni scoring sumowal wagi
calkowite). Porownywanie surowych wynikow miedzy wariantami nie znaczy nic. Stosunek
negatywy/pozytywy jest bezwymiarowy, wiec porownywalny.

URUCHOMIENIE
    ../venv/Scripts/python.exe scripts/measure_m4.py --variant baseline
    ../venv/Scripts/python.exe scripts/measure_m4.py --variant bm25f
    ../venv/Scripts/python.exe scripts/measure_m4.py --variant bm25f --set heldout   # RAZ, na koncu
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tomllib
from importlib import metadata
from pathlib import Path

ACAE_DIR = Path(__file__).resolve().parent.parent

from acae.bm25f import Bm25fIndex  # noqa: E402
from acae.canon import canonical_json, content_hash  # noqa: E402
from acae.core import collect_entries  # noqa: E402
from acae.pack import FsLocator, FsReader  # noqa: E402
from acae.retrieve import query_terms, select, term_rarity  # noqa: E402

SCHEMA = "acae.m4.v1"
TOP_K = (10, 25)
DEPTH = 25

SETS = {"dev": "tests/dev_questions.json", "heldout": "tests/heldout_questions.json"}


def run_git(args: list[str], cwd: Path) -> str:
    proc = subprocess.run(["git", *args], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return proc.stdout.decode("utf-8", "replace").strip()


def rank_baseline(entries, terms, depth):
    """Obecny ranker z M2: wagi pol + `term_rarity` z sufitem. Punkt odniesienia."""
    rarity = term_rarity(entries, terms)
    outline, _ = select(entries, terms, depth, 0)
    del rarity
    return outline


def is_hit(item, question) -> bool:
    """
    Trafienie: dokladny `name_path` albo sama nazwa liscia przy zgodnym pliku.

    Sama nazwa liscia bez zgodnosci pliku bylaby zbyt hojna — `__init__` trafialby wszedzie.
    """
    name = str(item["row"]["name_path"])
    path = str(item["path"])
    for target in question["answer_symbols"]:
        if name == target:
            return True
        if name.split("/")[-1] == target.split("/")[-1] and path in question["answer_files"]:
            return True
    return False


def evaluate(entries, index, queries, variant, depth=DEPTH):
    positives, negatives, per_query = [], [], []
    for q in queries:
        terms = query_terms(q["question"])
        if variant == "baseline":
            ranked = rank_baseline(entries, terms, depth)
        elif variant == "bm25f":
            ranked = index.rank(terms, depth)
        else:
            raise SystemExit(f"nieznany wariant: {variant}")

        top1 = ranked[0]["score"] if ranked else 0
        if q["kind"] == "negative":
            negatives.append(top1)
            per_query.append({"id": q["id"], "kind": "negative", "top1_score": top1, "returned": len(ranked)})
            continue

        rank_of_hit = 0
        for position, item in enumerate(ranked, 1):
            if is_hit(item, q):
                rank_of_hit = position
                break
        positives.append({"id": q["id"], "rank": rank_of_hit, "top1": top1})
        per_query.append({
            "id": q["id"], "kind": "positive", "rank": rank_of_hit, "top1_score": top1,
            "hit_at_10": bool(rank_of_hit and rank_of_hit <= 10),
            "hit_at_25": bool(rank_of_hit and rank_of_hit <= 25),
        })

    n = max(1, len(positives))
    recall = {f"recall_at_{k}_permille": sum(1000 for p in positives if p["rank"] and p["rank"] <= k) // n for k in TOP_K}
    mrr_permille = sum((1000 // p["rank"]) for p in positives if p["rank"]) // n
    mean_pos_top1 = sum(p["top1"] for p in positives) // n
    mean_neg_top1 = sum(negatives) // max(1, len(negatives))
    neg_ratio = (mean_neg_top1 * 1000) // max(1, mean_pos_top1)

    return {
        "counts": {"positive": len(positives), "negative": len(negatives)},
        **recall,
        "mrr_permille": mrr_permille,
        "mean_top1_positive": mean_pos_top1,
        "mean_top1_negative": mean_neg_top1,
        "negative_ratio_permille": neg_ratio,
        "per_query": per_query,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Ablacja M4 dla ACAE.")
    parser.add_argument("--variant", required=True, choices=("baseline", "bm25f"))
    parser.add_argument("--set", dest="qset", default="dev", choices=tuple(SETS))
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    repo_root = ACAE_DIR.parent
    with (ACAE_DIR / "config" / "acae.toml").open("rb") as fh:
        cfg = tomllib.load(fh)
    qpath = ACAE_DIR / SETS[args.qset]
    queries = json.loads(qpath.read_bytes())["queries"]

    locator = FsLocator(
        root=str(repo_root), roots=cfg["pack"]["roots"],
        prune_dirs=cfg.get("baseline", {}).get("prune_dirs", []),
        max_file_bytes=cfg["pack"]["max_file_bytes"],
    )
    entries, _ = collect_entries(locator, FsReader(str(repo_root)))
    index = Bm25fIndex(entries) if args.variant == "bm25f" else None

    result = evaluate(entries, index, queries, args.variant)

    payload = {
        "schema": SCHEMA,
        "variant": args.variant,
        "question_set": {
            "name": args.qset,
            "file": qpath.name,
            "content_hash": content_hash(qpath.read_bytes()),
        },
        "head": run_git(["rev-parse", "--short", "HEAD"], repo_root),
        "scope": {"files": len(entries), "symbols": sum(len(e["symbols"]) for e in entries)},
        "depth": DEPTH,
        "packages": {"tiktoken": metadata.version("tiktoken")},
        "metrics": {k: v for k, v in result.items() if k != "per_query"},
        "per_query": result["per_query"],
    }
    payload["result_hash"] = content_hash(canonical_json(payload))

    out_rel = args.out or f"_baseline/m4_{args.variant}_{args.qset}_{payload['head']}.json"
    out_path = ACAE_DIR / out_rel
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(canonical_json(payload, indent=2))

    m = payload["metrics"]
    print(f"wariant   {args.variant}   zbior {args.qset} ({m['counts']['positive']}+/{m['counts']['negative']}-)")
    print(f"recall@10 {m['recall_at_10_permille']/10:.1f}%")
    print(f"recall@25 {m['recall_at_25_permille']/10:.1f}%")
    print(f"MRR       {m['mrr_permille']/1000:.3f}")
    print(f"kontrola  negatywy/pozytywy = {m['negative_ratio_permille']/10:.1f}%  (nizej = lepiej)")
    print(f"zapis     {out_rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
