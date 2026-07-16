#!/usr/bin/env python3
"""Verify tier-1 Chroma ingest via embedded VectorStore search."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from server.store import VectorStore  # noqa: E402


def main() -> int:
    chroma_path = os.environ.get("CHROMA_PATH", str(REPO_ROOT / "data" / "chroma"))
    store = VectorStore(persist_path=chroma_path)

    checks = {
        "chroma_path": chroma_path,
        "sessions": store.list_sessions(),
        "operator_search": store.search("aions_operator", "Marcin operator profile active cases", top_k=3),
        "cbms_search": store.search("claude_marcin_main", "KBOOTSTRAP CBMS checkpoint", top_k=3),
        "operator_stats": store.session_stats("aions_operator"),
        "main_stats": store.session_stats("claude_marcin_main"),
    }
    print(json.dumps(checks, ensure_ascii=False, indent=2))

    ok = (
        checks["operator_stats"]["documents"] >= 2
        and checks["main_stats"]["documents"] >= 10
        and len(checks["operator_search"]) >= 1
        and len(checks["cbms_search"]) >= 1
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
