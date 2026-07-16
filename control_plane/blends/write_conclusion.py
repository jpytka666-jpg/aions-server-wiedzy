#!/usr/bin/env python3
"""Write conclusion from analyzed blend. Optional CBMS chunk export (file only)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "aions_core" / "memory" / "blends"))

from blend_lib import (  # noqa: E402
    BLEND_DIR,
    CONCLUSIONS_DIR,
    SEED_DIR,
    analyze_mistake,
    export_cbms_chunk,
    load_blend,
    save_blend,
    update_manifest,
    write_conclusion,
)

CHUNKS_DIR = REPO_ROOT / "aions_core" / "memory" / "chunks"
INGEST_NOTE = BLEND_DIR / "CBMS_INGEST_NOTE.md"


def resolve_input(path: str) -> Path:
    p = Path(path)
    if p.exists():
        return p
    for base in (CONCLUSIONS_DIR, SEED_DIR):
        candidate = base / f"{path}.json"
        if candidate.exists():
            return candidate
        candidate2 = base / path
        if candidate2.exists():
            return candidate2
    raise FileNotFoundError(f"Blend not found: {path}")


def append_ingest_note(chunk_id: str, blend_id: str) -> None:
    line = f"- `{chunk_id}` ← `{blend_id}` (pending manual ingest — nie dotykać prod Chroma)\n"
    if INGEST_NOTE.exists():
        body = INGEST_NOTE.read_text(encoding="utf-8")
        if chunk_id in body:
            return
    else:
        body = (
            "# CBMS Ingest Note — Blend Learning\n\n"
            "Offline only. Dodaj chunki do `knowledge_manifest.json` ręcznie lub przez\n"
            "`ingest_cbms_data.py` na **dev mirror**, nigdy na prod Chroma bez zgody.\n\n"
            "## Pending chunks\n\n"
        )
    INGEST_NOTE.write_text(body + line, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="AIONS blend conclusion writer")
    parser.add_argument("input", help="Analyzed blend path or id")
    parser.add_argument("-o", "--output", help="Output path")
    parser.add_argument(
        "--export-cbms",
        action="store_true",
        help="Write CBMS-ready chunk JSON to aions_core/memory/chunks/ (no manifest/Chroma)",
    )
    parser.add_argument("--chunk-id", help="Override CBMS chunk id")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    src = resolve_input(args.input)
    blend = load_blend(src)
    blend = analyze_mistake(blend)
    blend = write_conclusion(blend)
    if blend.get("status") == "concluded" and src.parent == SEED_DIR:
        blend["status"] = "verified"

    out = Path(args.output) if args.output else CONCLUSIONS_DIR / f"{blend['id']}.json"
    save_blend(blend, out)
    update_manifest(blend, out)

    chunk_path = None
    if args.export_cbms:
        chunk = export_cbms_chunk(blend, chunk_id=args.chunk_id)
        chunk_path = CHUNKS_DIR / f"{chunk['id']}.json"
        chunk_path.parent.mkdir(parents=True, exist_ok=True)
        with chunk_path.open("w", encoding="utf-8") as fh:
            json.dump(chunk, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        blend.setdefault("cbms_meta", {})["chunk_id"] = chunk["id"]
        blend["cbms_meta"]["ingest_ready"] = True
        save_blend(blend, out)
        append_ingest_note(chunk["id"], blend["id"])

    if args.json:
        print(json.dumps(blend, ensure_ascii=False, indent=2))
    else:
        c = blend["conclusion"]
        print(f"OK concluded {blend['id']}")
        print(f"  rule: {c['rule']}")
        print(f"  verify: {c['verify_before_claim']}")
        print(f"  output: {out}")
        if chunk_path:
            print(f"  cbms_chunk: {chunk_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
