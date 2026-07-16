#!/usr/bin/env python3
"""
Simple Esperanto bridge for AIONS/CBMS.
Deterministic, lightweight normalization from PL/EN → EO for symbolic encoding.

This is intentionally minimal: small dictionaries + regex rules. It is
designed to be safe (no heavy deps) and easy to extend.
"""
from __future__ import annotations

import re
from typing import Dict

_WS = re.compile(r"\s+")


def _normalize_text(s: str) -> str:
    s = s.strip().lower()
    # unify quotes/punct spacing
    s = _WS.sub(" ", s)
    return s


def _pl_to_eo_basic(s: str) -> str:
    """Very small PL→EO dictionary for MVP demonstration.
    This is not a translator — just a deterministic mapping for frequent phrases.
    """
    repl: Dict[str, str] = {
        # time / place
        "dzisiaj": "hodiaŭ",
        "dziś": "hodiaŭ",
        "w": "en",
        "w sklepie": "en vendejo",
        "do sklepu": "al vendejo",
        "sklep": "vendejo",
        # verbs (1sg past/present)
        "byłem": "mi estis",
        "byłam": "mi estis",
        "jestem": "mi estas",
        "kupiłem": "mi aĉetis",
        "kupiłam": "mi aĉetis",
        # objects
        "chleb": "pano",
        # CBMS/CRLA domain (basic)
        "cbms": "cbms",
        "pamięć": "memoro",
        "blok": "bloko",
        "chunk": "fragmento",
        "fragment": "fragmento",
        "klucze": "ŝlosiloj",
        "fakty": "faktoj",
        "indeks": "indekso",
        "odmowa": "refuzo",
        "panika": "paniko",
        "turniej": "turniro",
        "zwycięzca": "gajninto",
        "wynik": "poentaro",
        "latencja": "latenco",
        "deterministyczność": "determinismo",
    }
    # Token-wise replace to tolerate punctuation (keep separators)
    parts = re.findall(r"\w+|\W+", s, flags=re.UNICODE)
    out_parts = []
    for tok in parts:
        if tok.isalnum() and tok in repl:
            out_parts.append(repl[tok])
        else:
            out_parts.append(tok)
    return "".join(out_parts)


def to_esperanto(s: str, lang: str = "pl") -> str:
    """Return a regularized Esperanto string for symbolic processing.
    Currently supports Polish best-effort; others pass through normalization.
    """
    s = _normalize_text(s)
    if lang == "pl":
        s = _pl_to_eo_basic(s)
    return s


def from_esperanto_to_pl(eo: str) -> str:
    """Very rough EO→PL back rendering for demo.
    Not a translator — used only to show pipeline behavior in probes.
    """
    repl = {
        "hodiaŭ": "dzisiaj",
        "en vendejo": "w sklepie",
        "al vendejo": "do sklepu",
        "vendejo": "sklep",
        "mi estis": "byłem",
        "mi estas": "jestem",
        "mi aĉetis": "kupiłem",
        "pano": "chleb",
    }
    out = eo
    for k in sorted(repl.keys(), key=len, reverse=True):
        out = re.sub(rf"\b{k}\b", repl[k], out)
    return out
