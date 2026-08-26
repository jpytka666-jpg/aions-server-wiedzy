#!/usr/bin/env python3
# ==========================================
# AUTHOR: M. SZUL
# AI MODEL: Claude Opus 5
# TIMESTAMP: 2026-08-26 00:00:00
# REASON FOR CREATION: Every number written into the CBMS discovery record has to come
#   from the live store, not from recollection. This walks that store read-only and
#   emits one machine-readable measurement file that the documentation cites.
# MECHANICS: Opens every chunk JSON under the memory directory for reading, tallies
#   concepts, optional fields, addressing schemes and code-carrying blocks, counts the
#   sibling directories (quarantine, purgatory, blends) and compares the manifest's
#   own total against the files actually on disk. Writes measurements.json. Opens
#   nothing for writing inside the memory directory.
# SYSTEM PART: discovery/ - CBMS structure recovery
# ARCHITECTURE FUNCTION: The evidence source. cbms/ARCHITECTURE.md and cbms/findings.json
#   state conclusions; this states the counts those conclusions rest on, so a later
#   reader can re-run it and see whether the store has drifted.
# DEPENDENCIES/LINKS: reads aions_core/memory/{chunks,chunks_quarantine,chunks_purgatory,
#   blends,knowledge_manifest.json,gate_rejections.jsonl}; consumed by discovery/ingest.py
# TECH STACK: Python 3, standard library only. The thing being measured is a tree of
#   JSON files; a dependency would buy nothing and add a way for the measurement to fail.
# LOCAL WORKSPACE: worktree of aions-server-wiedzy, branch discovery/cbms-structure
# GIT COMMIT: PENDING
# GITHUB METADATA: jpytka666-jpg/aions-server-wiedzy, branch discovery/cbms-structure
# ==========================================
"""Measure the live CBMS store. Read-only, by construction."""

from __future__ import annotations

import argparse
import collections
import json
import os
import sys
from pathlib import Path

# Fields every chunk is expected to carry. Anything else is an extension some
# writer added later, and knowing which writers added what is half the structure.
CORE_FIELDS = {
    "id",
    "concept",
    "content",
    "created",
    "size",
    "references",
    "access_count",
    "last_accessed",
}


def default_memory_dir() -> Path:
    """Repo-relative by default; the env var wins when the store sits elsewhere."""
    env = os.environ.get("AIONS_MEMORY_DIR")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent / "aions_core" / "memory"


def load_chunks(chunks_dir: Path):
    """Yield (path, parsed) for every readable chunk; report the unreadable ones."""
    broken = []
    for path in sorted(chunks_dir.glob("*.json")):
        try:
            yield path, json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001 - the reason matters, the type does not
            broken.append({"file": path.name, "error": str(exc)[:200]})
    if broken:
        yield None, {"__broken__": broken}


def measure(memory_dir: Path) -> dict:
    chunks_dir = memory_dir / "chunks"
    if not chunks_dir.is_dir():
        raise SystemExit(f"no chunks directory under {memory_dir}")

    concepts = collections.Counter()
    fields = collections.Counter()
    coded = []          # chunks whose content was reduced to codebook symbols
    hangul = 0          # chunks carrying a Hangul address
    refs_out = []       # out-degree, to see the poisoned hubs the code warns about
    non_chunk_refs = collections.Counter()
    broken = []

    for path, chunk in load_chunks(chunks_dir):
        if path is None:
            broken = chunk["__broken__"]
            continue
        concepts[chunk.get("concept", "?")] += 1
        for key in chunk:
            fields[key] += 1
        if "hangul_code" in chunk:
            hangul += 1
        if "cbms_codes" in chunk or "eo" in chunk:
            coded.append(
                {
                    "id": chunk.get("id"),
                    "concept": chunk.get("concept"),
                    "created": chunk.get("created"),
                    "codes": chunk.get("cbms_codes"),
                    "eo": chunk.get("eo"),
                }
            )
        refs = chunk.get("references")
        if isinstance(refs, list):
            refs_out.append(len(refs))
            for ref in refs:
                if isinstance(ref, str) and not ref.startswith("K"):
                    # The retrieval code skips these; counting them shows how much
                    # of the graph is not a graph at all.
                    kind = "url" if "://" in ref else ("path" if ("/" in ref or "\\" in ref) else "label")
                    non_chunk_refs[kind] += 1

    manifest_path = memory_dir / "knowledge_manifest.json"
    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            manifest = {}

    def count_json(name: str) -> int:
        d = memory_dir / name
        return len(list(d.glob("*.json"))) if d.is_dir() else 0

    def count_lines(name: str) -> int:
        f = memory_dir / name
        if not f.exists():
            return 0
        with f.open("r", encoding="utf-8", errors="replace") as fh:
            return sum(1 for _ in fh)

    live = sum(concepts.values())
    refs_out.sort(reverse=True)

    return {
        "measured_from": str(memory_dir),
        "stores": {
            "chunks_live": live,
            "chunks_quarantine": count_json("chunks_quarantine"),
            "chunks_purgatory": count_json("chunks_purgatory"),
            "blends": len(list((memory_dir / "blends").glob("*"))) if (memory_dir / "blends").is_dir() else 0,
            "gate_rejections_logged": count_lines("gate_rejections.jsonl"),
        },
        "manifest": {
            "version": manifest.get("version"),
            "total_chunks_claimed": manifest.get("total_chunks"),
            "chunk_index_entries": len(manifest.get("chunk_index", {})),
            "concept_map_entries": len(manifest.get("concept_map", {})),
            "thinking_sessions": len(manifest.get("thinking_sessions", [])),
            # A manifest that disagrees with the filesystem is itself a finding.
            "drift_vs_files": live - int(manifest.get("total_chunks") or 0),
        },
        "addressing": {
            "chunks_with_hangul_code": hangul,
            "chunks_without_hangul_code": live - hangul,
        },
        "codebook_layer": {
            "chunks_carrying_codes": len(coded),
            "distinct_concepts_among_them": len({c["concept"] for c in coded}),
            "samples": coded[:20],
        },
        "reference_graph": {
            "chunks_with_references": len(refs_out),
            "max_out_degree": refs_out[0] if refs_out else 0,
            "top_out_degrees": refs_out[:10],
            "non_chunk_reference_targets": dict(non_chunk_refs),
        },
        "concepts": dict(concepts.most_common()),
        "optional_fields": {k: v for k, v in fields.most_common() if k not in CORE_FIELDS},
        "unreadable_chunks": broken,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--memory-dir", type=Path, default=None,
                    help="CBMS memory directory (default: repo aions_core/memory, or AIONS_MEMORY_DIR)")
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "cbms" / "measurements.json")
    args = ap.parse_args()

    memory_dir = args.memory_dir or default_memory_dir()
    result = measure(memory_dir)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    s = result["stores"]
    print(f"live {s['chunks_live']} | quarantine {s['chunks_quarantine']} | "
          f"purgatory {s['chunks_purgatory']} | blends {s['blends']}")
    print(f"hangul-addressed {result['addressing']['chunks_with_hangul_code']} | "
          f"codebook-encoded {result['codebook_layer']['chunks_carrying_codes']}")
    print(f"manifest drift vs files: {result['manifest']['drift_vs_files']:+d}")
    print(f"written: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
