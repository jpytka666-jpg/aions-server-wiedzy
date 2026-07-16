#!/usr/bin/env python3
"""
CBMS Codebook engine: load a small codebook and map EO text ↔ CBMS codes.
Greedy phrase matching with simple precedence (longest first).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple


class Codebook:
    def __init__(self, symbols: Dict[str, Dict]):
        self.symbols = symbols or {}
        # Build EO phrase → code lookup (many phrases per code)
        self._eo2code: List[Tuple[str, str]] = []  # (phrase, code)
        for code, meta in self.symbols.items():
            for phr in meta.get("eo", []) or []:
                phr = phr.strip().lower()
                if phr:
                    self._eo2code.append((phr, code))
        # Longest phrases first
        self._eo2code.sort(key=lambda x: len(x[0]), reverse=True)

    @staticmethod
    def load(path: Path) -> "Codebook":
        obj = json.loads(path.read_text(encoding="utf-8"))
        return Codebook(obj.get("symbols", {}))

    def encode_eo_to_cbms(self, eo_text: str) -> List[str]:
        s = " " + eo_text.strip().lower() + " "
        codes: List[str] = []
        used = [False] * len(s)
        # Greedy: mark spans as used so we don't double-match
        for phr, code in self._eo2code:
            start = 0
            while True:
                idx = s.find(" " + phr + " ", start)
                if idx == -1:
                    break
                span = (idx + 1, idx + 1 + len(phr))
                if not any(used[i] for i in range(span[0], span[1])):
                    for i in range(span[0], span[1]):
                        used[i] = True
                    codes.append(code)
                start = idx + 1
        return codes

    def decode_cbms_to_eo(self, codes: List[str]) -> str:
        parts: List[str] = []
        for c in codes:
            meta = self.symbols.get(c) or {}
            eo = (meta.get("eo") or [""])[0]
            parts.append(eo)
        return " ".join(p for p in parts if p)
