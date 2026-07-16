#!/usr/bin/env python3
"""One-shot: register treasure catalog as CBMS chunk KTREASURECAT2026."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CHUNK_ID = "KTREASURECAT2026"
CHUNK_PATH = REPO / "aions_core" / "memory" / "chunks" / f"{CHUNK_ID}.json"
MANIFEST_PATH = REPO / "aions_core" / "memory" / "knowledge_manifest.json"

catalog = json.loads((REPO / "AIONS_CATALOG" / "catalog_2026.json").read_text(encoding="utf-8"))
lines = [
    "E: TREASURE CATALOG 2026-07 — lokalizacje skarbów (tier-2 metadata, bez kopii binariów)",
    "Zapytania: gdzie jest plasters_200g, CBMS_INDEX_FULL, AJAJAJ backup.",
    "",
]
for t in catalog["treasures"]:
    lines.append(
        f"- {t['id']}: {t['path']} | type={t['type']} status={t['status']} "
        f"packs={t.get('pack_count', 0)} size_gb={t.get('size_gb', 0)} | {t.get('notes', '')}"
    )
content = "\n".join(lines)
refs = [
    str(REPO / "AIONS_CATALOG" / "catalog_2026.json"),
    str(REPO / "AIONS_CATALOG" / "INDEX.md"),
]

if CHUNK_PATH.exists():
    data = json.loads(CHUNK_PATH.read_text(encoding="utf-8"))
    data["content"] = content
    data["references"] = refs
    data["size"] = len(content)
    action = "updated"
else:
    data = {
        "id": CHUNK_ID,
        "concept": "treasure_catalog",
        "content": content,
        "created": datetime.now(timezone.utc).isoformat(),
        "size": len(content),
        "references": refs,
        "access_count": 0,
        "last_accessed": None,
    }
    action = "created"

CHUNK_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
manifest["chunk_index"][CHUNK_ID] = {
    "concept": "treasure_catalog",
    "size": len(content),
    "created": data.get("created", datetime.now(timezone.utc).isoformat()),
    "file": str(CHUNK_PATH),
}
manifest["total_chunks"] = len(manifest["chunk_index"])
MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"{action}: {CHUNK_ID} (manifest total={manifest['total_chunks']})")
