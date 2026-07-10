#!/usr/bin/env python3
"""KORZENIEC — smoke test CBMS-first gate (Faza 1).

Uruchamia 5–10 zapytań Marcin/AIONS, zapisuje hit/miss/conf do artifacts/gate_smoke.json.
Domyślnie NIE wymaga Ollamy — testuje retrieval + gate_decide.
Opcja --with-llm: pełny gate_answer (miss → Bielik).

Użycie:
  cd "E:\\server wiedzy"
  python experiments/aions_cbms_llm_v2/scripts/gate_demo.py
  python experiments/aions_cbms_llm_v2/scripts/gate_demo.py --with-llm
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

os.environ.setdefault("AIONS_PATH", str(REPO / "aions_core"))
os.environ.setdefault("CHROMA_PATH", str(REPO / "data" / "chroma"))
os.environ.setdefault("AIONS_CBMS_FIRST", "1")
os.environ.setdefault("AIONS_CBMS_CONFIDENCE", "0.7")

OUT_PATH = Path(__file__).resolve().parents[1] / "artifacts" / "gate_smoke.json"

SAMPLE_QUERIES: list[dict[str, str]] = [
    {
        "id": "q01_pipeline",
        "query": "Jak działa pipeline CBMS end-to-end?",
        "expect": "hit",
        "note": "KCBMSPIPE001 — cheat sheet operacyjny",
    },
    {
        "id": "q02_codebook",
        "query": "Co to jest codebook w CBMS i kompresja koreańska?",
        "expect": "hit",
        "note": "chunki o codebook.json + symbols",
    },
    {
        "id": "q03_access",
        "query": "Jak uzyskać pełny dostęp do chunków CBMS?",
        "expect": "hit",
        "note": "KCBMSACCESS001",
    },
    {
        "id": "q04_crla",
        "query": "Czym jest CRLA turniej kandydatów w CBMS?",
        "expect": "hit",
        "note": "CRLA / crla_core w chunkach",
    },
    {
        "id": "q05_hangul",
        "query": "Kompresja koreańska Hangul sylaby i korean keys w CBMS codebook",
        "expect": "hit",
        "note": "KCODEBOOK001 / KCBMSPIPE001 — Hangul=adres, nie NLG",
    },
    {
        "id": "q06_chroma",
        "query": "Jak działa CBMS pipeline end-to-end korean keys i symbolic index?",
        "expect": "hit",
        "note": "KCBMSPIPE001 — Chroma lokalnie bywa padnięta, pipeline jest w CBMS",
    },
    {
        "id": "q07_esperanto",
        "query": "Esperanto bridge symbolic index codebook encode",
        "expect": "hit",
        "note": "symbolic index / esperanto_bridge",
    },
    {
        "id": "q08_operator",
        "query": "Kim jest Marcin i jakie ma hobby w życiu prywatnym?",
        "expect": "miss",
        "note": "abstrakcyjne / poza CBMS — gate miss",
    },
    {
        "id": "q09_quantum",
        "query": "Wyjaśnij kwantową grawitację w teorii strun",
        "expect": "miss",
        "note": "poza wiedzą AIONS",
    },
    {
        "id": "q10_weather",
        "query": "Jaka będzie pogoda jutro w Tokio?",
        "expect": "miss",
        "note": "poza CBMS — gate musi miss (nie udajemy wiedzy)",
    },
]


def run_smoke(*, with_llm: bool = False, threshold: float = 0.7) -> dict:
    from control_plane.cbms_gate import gate_answer, gate_decide, retrieve  # noqa: WPS433

    results: list[dict] = []
    hits = misses = errors = 0

    for item in SAMPLE_QUERIES:
        q = item["query"]
        row: dict = {
            "id": item["id"],
            "query": q,
            "expect": item["expect"],
            "note": item["note"],
        }
        try:
            if with_llm:
                out = gate_answer(q, threshold=threshold, top_k=5)
                row["gate"] = out.get("gate")
                row["confidence"] = out.get("confidence")
                row["provider"] = out.get("provider")
                row["top_chunk"] = (out.get("retrieval") or {}).get("hits", [{}])[0].get("id")
                row["answer_preview"] = (out.get("content") or "")[:200]
            else:
                retrieval = retrieve(q, top_k=5)
                decision = gate_decide(retrieval, threshold=threshold)
                row["gate"] = "hit" if decision["hit"] else "miss"
                row["confidence"] = retrieval.get("confidence")
                row["top_chunk"] = (retrieval.get("hits") or [{}])[0].get("id")
                row["top_score"] = (retrieval.get("hits") or [{}])[0].get("score")
                row["sources"] = [h.get("source") for h in (retrieval.get("hits") or [])[:3]]
                row["query_codes"] = retrieval.get("codebook_symbols", [])[:5]
        except Exception as exc:  # noqa: BLE001
            row["gate"] = "error"
            row["error"] = str(exc)
            errors += 1
            results.append(row)
            continue

        if row.get("gate") == "hit":
            hits += 1
        elif row.get("gate") == "miss":
            misses += 1

        expect = item["expect"]
        row["pass"] = row.get("gate") == expect
        results.append(row)

    passed = sum(1 for r in results if r.get("pass"))
    # PASS: zero błędów runtime + ≥70% zgodności expect hit/miss
    status = "PASS" if errors == 0 and passed >= max(1, int(len(results) * 0.7)) else "FAIL"
    return {
        "project": "KORZENIEC",
        "phase": "1-gate-smoke",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "threshold": threshold,
        "with_llm": with_llm,
        "summary": {
            "total": len(results),
            "hits": hits,
            "misses": misses,
            "errors": errors,
            "expect_pass": passed,
            "status": status,
        },
        "results": results,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="KORZENIEC gate smoke test")
    ap.add_argument("--with-llm", action="store_true", help="pełny gate_answer (miss → Ollama)")
    ap.add_argument("--threshold", type=float, default=0.7)
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    args = ap.parse_args()

    report = run_smoke(with_llm=args.with_llm, threshold=args.threshold)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)

    s = report["summary"]
    print(f"[gate_demo] status={s['status']} hits={s['hits']} misses={s['misses']} errors={s['errors']}")
    print(f"[gate_demo] wrote {args.out}")
    for r in report["results"]:
        mark = "OK" if r.get("pass") else "!!"
        print(
            f"  {mark} {r['id']}: gate={r.get('gate')} conf={r.get('confidence')} "
            f"expect={r.get('expect')} chunk={r.get('top_chunk')}"
        )
    return 0 if s["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
