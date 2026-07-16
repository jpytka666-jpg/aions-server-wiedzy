#!/usr/bin/env python3
"""Ingest tier-1 CBMS metadata + operator profile into Chroma prod (embedded VectorStore)."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import chromadb  # noqa: E402

from server.store import VectorStore  # noqa: E402

DEFAULT_CHROMA = REPO_ROOT / "data" / "chroma"


def _assert_chroma_version() -> None:
    """Refuse to write with an incompatible chromadb build.

    Prod DB is 0.5.x on-disk format (BLOB seq_id). chromadb >=0.6/1.x uses a
    Rust engine expecting INTEGER seq_id and fails with an InternalError during
    compaction. Always run ingest via prod venv (E:\\server wiedzy\\venv, 0.5.3).
    """
    version = chromadb.__version__
    if not version.startswith("0.5"):
        raise SystemExit(
            f"[AIONS ingest guard] Wykryto chromadb {version}, wymagane 0.5.x.\n"
            "Baza data/chroma jest w formacie 0.5.x (BLOB seq_id). chromadb 1.x (Rust) "
            "wywala compaction: 'u64 INTEGER is not compatible with BLOB'.\n"
            "Uruchom przez prod venv: scripts\\aions_python.ps1 scripts\\ingest_tier1_chroma.py"
        )
AIONS_CORE = REPO_ROOT / "aions_core"
OPERATOR_PROFILE = AIONS_CORE / "memory" / "operator_profile.json"
MANIFEST = AIONS_CORE / "memory" / "knowledge_manifest.json"

PLASTER_CONCEPTS = {"plasters", "plasters_usage", "plasters_plan"}
PLASTER_ID_PREFIXES = ("KPLASTER", "KDOCPLASTERS")

TIER1_PRIORITY_IDS = [
    "KBOOTSTRAP",
    "KCBMSACCESS001",
    "KCLAUDE_MEMORY_RULE",
    "KMEMSRC001",
    "KOPSPLAY001",
    "KGUARD001",
    "KCODEBOOK001",
    "KCBMSPIPE001",
    "KWEBRAG001",
    "KTESTSUITE001",
    "KCURSOROPS001",
    "KCURSORGIT001",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _base_meta(source: str, tags: list[str], **extra: object) -> dict:
    return {
        "agent": "ingest_tier1_chroma",
        "source": source,
        "tags": tags,
        "timestamp": _now_iso(),
        "ttl_days": 365,
        **extra,
    }


def _format_operator_profile(data: dict) -> str:
    identity = data.get("identity", {})
    lines = [
        "Operator profile (AIONS tier-1)",
        f"Name: {identity.get('name', '?')}",
        f"Role: {identity.get('role', '?')}",
        f"Locale: {identity.get('locale', '?')}",
        "",
        "Active cases:",
    ]
    for case in data.get("active_cases", []):
        lines.append(
            f"- [{case.get('status', '?')}] {case.get('title', case.get('id', '?'))}: "
            f"{case.get('summary', '')}"
        )
    lines.append("")
    lines.append("Goals:")
    for goal in data.get("goals", []):
        lines.append(f"- ({goal.get('priority', '?')}) {goal.get('title', '?')}")
    lines.append("")
    lines.append("Recent decisions:")
    for decision in data.get("decisions", [])[:5]:
        lines.append(
            f"- {decision.get('date', '?')} | {decision.get('topic', '?')}: "
            f"{decision.get('decision', '')}"
        )
    return "\n".join(lines)


def _is_plaster(chunk_id: str, concept: str) -> bool:
    if concept in PLASTER_CONCEPTS:
        return True
    upper = chunk_id.upper()
    return any(upper.startswith(prefix) for prefix in PLASTER_ID_PREFIXES)


def _load_manifest_entries() -> list[tuple[str, str, dict]]:
    with MANIFEST.open(encoding="utf-8") as fh:
        manifest = json.load(fh)
    entries: list[tuple[str, str, dict]] = []
    for chunk_id, info in manifest.get("chunk_index", {}).items():
        concept = str(info.get("concept", "general"))
        if _is_plaster(chunk_id, concept):
            continue
        text = f"CBMS chunk {chunk_id} | concept: {concept} | size: {info.get('size', '?')}"
        meta = _base_meta(
            "cbms_manifest",
            ["tier1", "cbms", "metadata"],
            chunk_id=chunk_id,
            concept=concept,
        )
        entries.append((f"tier1_cbms_{chunk_id}", text, meta))
    return entries


def _select_sample(entries: list[tuple[str, str, dict]], limit: int = 40) -> list[tuple[str, str, dict]]:
    by_id = {doc_id: (doc_id, text, meta) for doc_id, text, meta in entries}
    selected: list[tuple[str, str, dict]] = []
    seen: set[str] = set()

    for chunk_id in TIER1_PRIORITY_IDS:
        doc_id = f"tier1_cbms_{chunk_id}"
        if doc_id in by_id and doc_id not in seen:
            selected.append(by_id[doc_id])
            seen.add(doc_id)

    for doc_id, text, meta in entries:
        if len(selected) >= limit:
            break
        if doc_id in seen:
            continue
        selected.append((doc_id, text, meta))
        seen.add(doc_id)
    return selected


def ingest(dry_run: bool = False) -> dict:
    chroma_path = os.environ.get("CHROMA_PATH", str(DEFAULT_CHROMA))
    if not OPERATOR_PROFILE.is_file():
        raise FileNotFoundError(f"Missing operator profile: {OPERATOR_PROFILE}")
    if not MANIFEST.is_file():
        raise FileNotFoundError(f"Missing manifest: {MANIFEST}")

    with OPERATOR_PROFILE.open(encoding="utf-8") as fh:
        profile_data = json.load(fh)

    operator_text = _format_operator_profile(profile_data)
    operator_item = (
        "tier1_operator_profile",
        operator_text,
        _base_meta("operator_profile.json", ["tier1", "operator", "profile"]),
    )

    manifest_entries = _load_manifest_entries()
    sample_entries = _select_sample(manifest_entries, limit=40)
    index_text = "CBMS tier-1 index (non-plaster operational chunks):\n" + "\n".join(
        text for _, text, _ in sample_entries[:40]
    )
    index_item = (
        "tier1_cbms_index",
        index_text,
        _base_meta(
            "knowledge_manifest.json",
            ["tier1", "cbms", "index"],
            chunk_count=len(manifest_entries),
            sample_count=len(sample_entries),
        ),
    )

    plan = {
        "chroma_path": chroma_path,
        "aions_operator": [operator_item, index_item],
        "claude_marcin_main": sample_entries,
        "manifest_non_plaster": len(manifest_entries),
        "sample_size": len(sample_entries),
    }

    if dry_run:
        return {"dry_run": True, **plan}

    _assert_chroma_version()
    store = VectorStore(persist_path=chroma_path)
    op_ids = store.add_items("aions_operator", [operator_item, index_item])
    main_ids = store.add_items("claude_marcin_main", sample_entries)

    return {
        "dry_run": False,
        "chroma_path": chroma_path,
        "aions_operator_docs": len(op_ids),
        "claude_marcin_main_docs": len(main_ids),
        "manifest_non_plaster": len(manifest_entries),
        "sample_size": len(sample_entries),
        "sessions": store.list_sessions(),
    }


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    result = ingest(dry_run=dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
