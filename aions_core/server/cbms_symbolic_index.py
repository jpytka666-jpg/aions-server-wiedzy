#!/usr/bin/env python3
"""
Symbolic index over CBMS codes built on-the-fly from chunk contents.
Non-destructive: does not modify chunk files; computes EO→CBMS for each chunk.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

from esperanto_bridge import to_esperanto
from codebook_engine import Codebook


class SymbolicIndex:
    def __init__(self, memory_dir: Path, codebook: Codebook):
        self.memory_dir = Path(memory_dir)
        self.chunks_dir = self.memory_dir / "chunks"
        self.cb = codebook
        self.sym2chunks: Dict[str, set] = {}
        self.chunk_codes: Dict[str, List[str]] = {}

    def build(self, limit: int | None = None) -> int:
        count = 0
        for i, f in enumerate(sorted(self.chunks_dir.glob("*.json"))):
            if limit and i >= limit:
                break
            try:
                obj = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            cid = obj.get("id") or f.stem
            content = (obj.get("content") or "").strip()
            if not content:
                continue
            eo = to_esperanto(content)
            codes = self.cb.encode_eo_to_cbms(eo)
            if not codes:
                continue
            self.chunk_codes[cid] = codes
            for c in codes:
                self.sym2chunks.setdefault(c, set()).add(cid)
            count += 1
        return count

    def search(self, query: str, top_k: int = 12) -> List[Tuple[str, int]]:
        eo = to_esperanto(query)
        q_codes = self.cb.encode_eo_to_cbms(eo)
        scores: Dict[str, int] = {}
        for c in q_codes:
            for cid in self.sym2chunks.get(c, ()):
                scores[cid] = scores.get(cid, 0) + 1
        ranked = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
        return ranked[:top_k]

