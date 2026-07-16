#!/usr/bin/env python3
"""Tier-2 ingest: treasure location metadata into Chroma (no binary copy)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import chromadb  # noqa: E402

from server.store import VectorStore  # noqa: E402

CATALOG_JSON = REPO_ROOT / "AIONS_CATALOG" / "catalog_2026.json"
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
            "Uruchom przez prod venv: scripts\\aions_python.ps1 scripts\\ingest_treasures_tier2.py"
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _base_meta(treasure_id: str, **extra: object) -> dict:
    return {
        "agent": "ingest_treasures_tier2",
        "source": "catalog_2026.json",
        "tags": ["tier2", "treasure", "catalog"],
        "treasure_id": treasure_id,
        "timestamp": _now_iso(),
        "ttl_days": 365,
        **extra,
    }


def _format_treasure(entry: dict) -> str:
    lines = [
        f"E: treasure {entry['id']}",
        f"Path: {entry['path']}",
        f"Type: {entry['type']} | Status: {entry['status']} | CBMS linked: {entry.get('cbms_linked', False)}",
        f"Files: {entry.get('file_count', 0)} | PACK dirs: {entry.get('pack_count', 0)} | Size GB: {entry.get('size_gb', 0)}",
        f"Notes: {entry.get('notes', '')}",
    ]
    return "\n".join(lines)


def _load_catalog() -> dict:
    if not CATALOG_JSON.is_file():
        raise FileNotFoundError(
            f"Missing {CATALOG_JSON}; run scripts/catalog_e_treasures.py first"
        )
    with CATALOG_JSON.open(encoding="utf-8") as fh:
        return json.load(fh)


def ingest(dry_run: bool = False) -> dict:
    import os

    catalog = _load_catalog()
    treasures = catalog.get("treasures", [])
    items: list[tuple[str, str, dict]] = []

    index_lines = ["E: treasure catalog (tier-2 metadata index):"]
    for entry in treasures:
        if not entry.get("exists", True):
            continue
        doc_id = f"tier2_treasure_{entry['id']}"
        text = _format_treasure(entry)
        meta = _base_meta(
            entry["id"],
            path=entry["path"],
            treasure_type=entry["type"],
            status=entry["status"],
            cbms_linked=bool(entry.get("cbms_linked")),
            file_count=int(entry.get("file_count", 0)),
            pack_count=int(entry.get("pack_count", 0)),
            size_gb=float(entry.get("size_gb", 0)),
        )
        items.append((doc_id, text, meta))
        index_lines.append(f"- {entry['id']}: {entry['path']} ({entry['type']}, {entry['status']})")

    index_item = (
        "tier2_treasure_index",
        "\n".join(index_lines),
        _base_meta(
            "catalog_index",
            treasure_count=len(items),
            catalog_version=catalog.get("version"),
        ),
    )

    chroma_path = os.environ.get("CHROMA_PATH", str(DEFAULT_CHROMA))
    plan = {
        "chroma_path": chroma_path,
        "treasure_docs": len(items),
        "collections": {
            "aions_operator": [index_item],
            "claude_marcin_main": items,
        },
    }

    if dry_run:
        return {"dry_run": True, **plan}

    _assert_chroma_version()
    store = VectorStore(persist_path=chroma_path)
    op_ids = store.add_items("aions_operator", [index_item])
    main_ids = store.add_items("claude_marcin_main", items)
    return {
        "dry_run": False,
        "chroma_path": chroma_path,
        "aions_operator_docs": len(op_ids),
        "claude_marcin_main_docs": len(main_ids),
        "treasure_docs": len(items),
        "sessions": store.list_sessions(),
    }


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    result = ingest(dry_run=dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
