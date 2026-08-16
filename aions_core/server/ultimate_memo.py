#!/usr/bin/env python3
from __future__ import annotations

"""
UltimateMemo: Context memory with CBMS chunks (KR keys + EO/CBMS codes).

Goals:
- Persistent context as lightweight CBMS chunks (concept='context_memo').
- Instant recall via in-memory indices for KR keys and EO→CBMS codes.
- Non-invasive: optional feature; no external dependencies.
"""

from typing import Dict, List, Tuple, Optional
from pathlib import Path
import time


def _kk_build(cbms, text: str) -> set:
    try:
        return cbms._kk_build_keys(text) if hasattr(cbms, "_kk_build_keys") else set()
    except Exception:
        return set()


def _eo_codes(mem_root: str | Path, text: str) -> List[str]:
    try:
        from esperanto_bridge import to_esperanto  # type: ignore
        from codebook_engine import Codebook  # type: ignore
        cb_path = Path(mem_root) / "codebook" / "codebook.json"
        if not cb_path.exists():
            return []
        cb = Codebook.load(cb_path)
        eo = to_esperanto(text)
        return cb.encode_eo_to_cbms(eo) or []
    except Exception:
        return []


class UltimateMemo:
    def __init__(self, cbms, mem_root: str | Path):
        self.cbms = cbms
        self.mem_root = str(mem_root)
        self.memo_ids: List[str] = []
        self.memo_keys: Dict[str, set] = {}
        self.memo_codes: Dict[str, List[str]] = {}

    def record_exchange(self, query: str, response: str, refs: List[str], qc: Dict, min_refs: int = 2) -> Optional[str]:
        try:
            if not response:
                return None
            if not isinstance(refs, list):
                refs = []
            # Heuristic gate: only persist when we had some grounding
            if len(refs) < min_refs:
                return None
            # Build compact memo text
            content = (
                "CONTEXT MEMO\n"
                f"ts: {int(time.time())}\n"
                f"refs: {len(refs)}\n"
                "query:\n" + (query[:400] + ("..." if len(query) > 400 else "")) + "\n"
                "response:\n" + (response[:800] + ("..." if len(response) > 800 else ""))
            )
            meta = {"source": "ultimate_memo", "qc": (qc or {}).get("verdict", "NA")}
            cid = self.cbms.create_knowledge_chunk(content, concept="context_memo", references=refs, meta=meta)
            # Index for fast recall
            self.memo_ids.append(cid)
            self.memo_keys[cid] = _kk_build(self.cbms, content)
            self.memo_codes[cid] = _eo_codes(self.mem_root, content)
            return cid
        except Exception:
            return None

    def retrieve_context(self, query: str, top_k: int = 5) -> List[str]:
        # score by KR key overlap + EO/CBMS code overlap
        try:
            qk = _kk_build(self.cbms, query)
            q_codes = set(_eo_codes(self.mem_root, query))
            scores: List[Tuple[str, int]] = []
            for cid in self.memo_ids[-500:]:  # recent window for speed
                kk = self.memo_keys.get(cid, set())
                sc = len(qk & kk)
                if q_codes:
                    sc += len(q_codes & set(self.memo_codes.get(cid, [])))
                if sc > 0:
                    scores.append((cid, sc))
            ranked = sorted(scores, key=lambda x: (-x[1], x[0]))
            return [cid for cid, _ in ranked[:top_k]]
        except Exception:
            return []

