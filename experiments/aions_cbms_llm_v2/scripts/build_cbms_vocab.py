#!/usr/bin/env python3
"""KORZENIEC — budowa natywnego vocab Hangul + codebook.

Czyta (read-only):
  - korean_cbms_tokenizer.json  (~4016 sylab Hangul jako adresy)
  - codebook.json               (symbole CBMS + frazy eo/pl)

Pisze TYLKO do artifacts/ w tym eksperymencie.
NIE rusza D:\\LOCAL LLM MODELS ani chunków CBMS.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HANGUL = Path(
    r"E:\AJAJAJ\AI DEVELOPMENT\WORK SPACE\IMPORT FROM_E\BIELIK_KOREAN_CBMS\korean_cbms_tokenizer.json"
)
DEFAULT_CODEBOOK = Path(
    r"E:\server wiedzy\aions_core\memory\codebook\codebook.json"
)
OUT_DIR = ROOT / "artifacts" / "vocab"

KORZENIEC_CONTROLS = [
    "<cbms>",
    "</cbms>",
    "<addr>",
    "</addr>",
    "<eo>",
    "</eo>",
    "<gate_hit>",
    "<gate_miss>",
]


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def build_vocab(hangul_path: Path, codebook_path: Path) -> dict:
    hangul = load_json(hangul_path)
    codebook = load_json(codebook_path)

    base_vocab: dict[str, int] = dict(hangul.get("vocab", {}))
    if not base_vocab:
        raise SystemExit(f"Brak vocab w {hangul_path}")

    # Zachowaj oryginalne ID Hangul (adresy muszą być stabilne).
    token_to_id = dict(sorted(base_vocab.items(), key=lambda kv: kv[1]))
    id_to_token = {i: t for t, i in token_to_id.items()}
    next_id = max(token_to_id.values()) + 1

    symbols = codebook.get("symbols", {})
    codebook_tokens: dict[str, dict] = {}

    for sym, meta in symbols.items():
        # Token symbolu: <<CB:SYM>> żeby nie kolidował z Hangul / PL
        tok = f"<<CB:{sym}>>"
        if tok in token_to_id:
            continue
        token_to_id[tok] = next_id
        id_to_token[next_id] = tok
        codebook_tokens[tok] = {
            "id": next_id,
            "symbol": sym,
            "sem": meta.get("sem"),
            "eo": meta.get("eo", []),
            "pl": meta.get("pl", []),
        }
        next_id += 1

    control_added: dict[str, int] = {}
    for tok in KORZENIEC_CONTROLS:
        if tok in token_to_id:
            control_added[tok] = token_to_id[tok]
            continue
        token_to_id[tok] = next_id
        id_to_token[next_id] = tok
        control_added[tok] = next_id
        next_id += 1

    hangul_only = {
        t: i
        for t, i in token_to_id.items()
        if not t.startswith("<<CB:") and t not in KORZENIEC_CONTROLS
    }

    return {
        "project": "KORZENIEC",
        "version": "2.0.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "hangul_tokenizer": str(hangul_path),
            "codebook": str(codebook_path),
            "hangul_type": hangul.get("type"),
            "hangul_compression": hangul.get("compression_ratio"),
        },
        "counts": {
            "total": len(token_to_id),
            "hangul_and_specials": len(hangul_only),
            "codebook_symbols": len(codebook_tokens),
            "korzeniec_controls": len(control_added),
        },
        "token_to_id": token_to_id,
        "codebook_tokens": codebook_tokens,
        "control_tokens": control_added,
        "notes": [
            "Hangul IDs zachowane 1:1 względem korean_cbms_tokenizer.json",
            "Codebook i control tokeny doklejone PO Hangul (id >= 4016)",
            "To jest vocab ADRESOWY CBMS — nie zastępuje tokenizera Bielika PL",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="KORZENIEC build_cbms_vocab")
    ap.add_argument("--hangul", type=Path, default=DEFAULT_HANGUL)
    ap.add_argument("--codebook", type=Path, default=DEFAULT_CODEBOOK)
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    for label, path in (("hangul", args.hangul), ("codebook", args.codebook)):
        if not path.is_file():
            print(f"[ERR] brak pliku {label}: {path}", file=sys.stderr)
            return 2

    vocab = build_vocab(args.hangul, args.codebook)
    print(
        f"[KORZENIEC] vocab total={vocab['counts']['total']} "
        f"hangul={vocab['counts']['hangul_and_specials']} "
        f"codebook={vocab['counts']['codebook_symbols']} "
        f"controls={vocab['counts']['korzeniec_controls']}"
    )

    if args.dry_run:
        print("[dry-run] OK — nic nie zapisano")
        sample = list(vocab["codebook_tokens"].items())[:3]
        for tok, meta in sample:
            print(f"  {tok} -> id={meta['id']} sem={meta['sem']}")
        return 0

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out_dir / "korzeniec_vocab.json"
    # Lżejszy plik indeksowy bez pełnego token_to_id (opcjonalnie pełny też)
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(vocab, fh, ensure_ascii=False, indent=2)

    slim = {
        "project": vocab["project"],
        "counts": vocab["counts"],
        "codebook_tokens": vocab["codebook_tokens"],
        "control_tokens": vocab["control_tokens"],
        "sources": vocab["sources"],
    }
    slim_path = args.out_dir / "korzeniec_vocab_slim.json"
    with slim_path.open("w", encoding="utf-8") as fh:
        json.dump(slim, fh, ensure_ascii=False, indent=2)

    print(f"[OK] wrote {out_path}")
    print(f"[OK] wrote {slim_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
