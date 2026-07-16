#!/usr/bin/env python3
"""Scan E: treasure locations and emit machine-readable catalog JSON."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG_DIR = REPO_ROOT / "AIONS_CATALOG"
OUTPUT_JSON = CATALOG_DIR / "catalog_2026.json"
SCAN_ROOT = REPO_ROOT / "scan_results" / "full_system_20260702_035156"
AIONS_CORE = REPO_ROOT / "aions_core"
MANIFEST = AIONS_CORE / "memory" / "knowledge_manifest.json"

TREASURE_ROOTS: list[dict] = [
    {
        "id": "aions_core_cbms",
        "path": AIONS_CORE,
        "type": "cbms_operational",
        "status": "connected",
        "cbms_linked": True,
        "notes": "Kanoniczny AIONS_PATH; 561 chunków operacyjnych",
    },
    {
        "id": "aions_catalog",
        "path": CATALOG_DIR,
        "type": "catalog_index",
        "status": "connected",
        "cbms_linked": False,
        "notes": "Indeks referencyjny AIONS_CATALOG",
    },
    {
        "id": "plasters_200g_master",
        "path": Path(r"E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\plasters_200g"),
        "type": "plasters",
        "status": "connected",
        "cbms_linked": True,
        "notes": "200 PACK-*, ~343k Q&A (metadata); główna kopia robocza",
    },
    {
        "id": "plasters_fullstack",
        "path": Path(r"E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\plasters_fullstack"),
        "type": "plasters",
        "status": "connected",
        "cbms_linked": True,
        "notes": "448 PACK-* fullstack",
    },
    {
        "id": "plasters_unified",
        "path": Path(r"E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\plasters_unified"),
        "type": "plasters",
        "status": "archived",
        "cbms_linked": True,
        "notes": "Plan unifikacji; katalog pusty lub przeniesiony",
    },
    {
        "id": "master_clean_unclassified",
        "path": Path(r"E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED"),
        "type": "workspace_archive",
        "status": "connected",
        "cbms_linked": False,
        "notes": "Plastery, thinking_patterns, MAIPA i inne paczki (~61 GB)",
    },
    {
        "id": "ajajaj_root",
        "path": Path(r"E:\AJAJAJ"),
        "type": "backup_archive",
        "status": "connected",
        "cbms_linked": False,
        "notes": "Pełna kopia CBMS indexes, SEED, plasters (~184 GB)",
    },
    {
        "id": "cbms_index_full",
        "path": Path(r"E:\AJAJAJ\CBMS_INDEX_FULL"),
        "type": "cbms_index",
        "status": "disconnected",
        "cbms_linked": False,
        "notes": "6819 docs kr_meta.json — nie podłączony do operacyjnego MCP",
    },
    {
        "id": "cbms_index_korean",
        "path": Path(r"E:\AJAJAJ\CBMS_INDEX_KOREAN"),
        "type": "cbms_index",
        "status": "disconnected",
        "cbms_linked": False,
        "notes": "Korean syllable index (~8042 patterns)",
    },
    {
        "id": "cbms_seed",
        "path": Path(r"E:\AJAJAJ\CBMS_SEED"),
        "type": "model_artifacts",
        "status": "archived",
        "cbms_linked": False,
        "notes": "SEED Mistral repack metadata; duże binaria poza tym folderem",
    },
    {
        "id": "ajajaj_plasters_200g",
        "path": Path(r"E:\AJAJAJ\plasters_200g"),
        "type": "plasters",
        "status": "archived",
        "cbms_linked": True,
        "notes": "Kopia zapasowa plasters_200g",
    },
    {
        "id": "aions_complete",
        "path": Path(r"E:\AJAJAJ\AIONS_COMPLETE"),
        "type": "legacy_snapshot",
        "status": "archived",
        "cbms_linked": False,
        "notes": "Snapshot AIONS_COMPLETE z seed era",
    },
    {
        "id": "full_system_scan",
        "path": SCAN_ROOT,
        "type": "scan_artifact",
        "status": "connected",
        "cbms_linked": False,
        "notes": "full_system_20260702_035156 — inventory D/E/F/C",
    },
    {
        "id": "chroma_prod",
        "path": REPO_ROOT / "data" / "chroma",
        "type": "vector_store",
        "status": "connected",
        "cbms_linked": True,
        "notes": "ChromaDB prod (tier-1 + treasures ingest)",
    },
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _dir_stats(path: Path) -> dict:
    if not path.is_dir():
        return {"exists": False, "file_count": 0, "size_bytes": 0, "size_gb": 0.0, "pack_count": 0}
    file_count = 0
    size_bytes = 0
    pack_count = 0
    for root, dirs, files in os.walk(path):
        for name in files:
            file_count += 1
            try:
                size_bytes += (Path(root) / name).stat().st_size
            except OSError:
                pass
        for name in dirs:
            if name.upper().startswith("PACK-"):
                pack_count += 1
    return {
        "exists": True,
        "file_count": file_count,
        "size_bytes": size_bytes,
        "size_gb": round(size_bytes / (1024**3), 2),
        "pack_count": pack_count,
    }


def _manifest_stats() -> dict:
    if not MANIFEST.is_file():
        return {"manifest_chunks": 0, "manifest_path": str(MANIFEST)}
    with MANIFEST.open(encoding="utf-8") as fh:
        data = json.load(fh)
    disk = len(list((AIONS_CORE / "memory" / "chunks").glob("*.json")))
    return {
        "manifest_chunks": data.get("total_chunks", len(data.get("chunk_index", {}))),
        "disk_chunks": disk,
        "manifest_path": str(MANIFEST),
    }


def build_catalog() -> dict:
    entries = []
    for spec in TREASURE_ROOTS:
        path = Path(spec["path"])
        stats = _dir_stats(path)
        entry = {
            "id": spec["id"],
            "path": str(path),
            "type": spec["type"],
            "status": spec["status"],
            "cbms_linked": spec["cbms_linked"],
            "notes": spec["notes"],
            **stats,
        }
        entries.append(entry)

    scan_summary = {}
    master_map = SCAN_ROOT / "master_map.json"
    if master_map.is_file():
        with master_map.open(encoding="utf-8") as fh:
            scan_summary = json.load(fh)

    return {
        "version": "2026.07",
        "generated_at": _now_iso(),
        "generator": "scripts/catalog_e_treasures.py",
        "canonical_cbms": str(AIONS_CORE),
        "cbms_manifest": _manifest_stats(),
        "full_system_scan": scan_summary.get("campaign_id"),
        "treasure_count": len(entries),
        "treasures": entries,
    }


def main() -> int:
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    catalog = build_catalog()
    with OUTPUT_JSON.open("w", encoding="utf-8") as fh:
        json.dump(catalog, fh, ensure_ascii=False, indent=2)
    print(json.dumps({"output": str(OUTPUT_JSON), "treasures": catalog["treasure_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
