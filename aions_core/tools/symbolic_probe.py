#!/usr/bin/env python3
"""
Symbolic probe: demonstrate NL→Esperanto→CBMS codes and symbolic retrieval.
Non-destructive; reads chunks and codebook; prints debug info.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List
import importlib.util as ilu

ROOT = Path(__file__).resolve().parent.parent
MEM = Path(os.environ.get("CBMS_MEMORY_DIR", str(ROOT / "memory")))

def _load(name: str, file: Path):
    spec = ilu.spec_from_file_location(name, str(file))
    mod = ilu.module_from_spec(spec)  # type: ignore
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore
    return mod

esperanto_bridge = _load("esperanto_bridge", ROOT / "server" / "esperanto_bridge.py")
codebook_engine = _load("codebook_engine", ROOT / "server" / "codebook_engine.py")
import sys
sys.modules["esperanto_bridge"] = esperanto_bridge
sys.modules["codebook_engine"] = codebook_engine
cbms_symbolic_index = _load("cbms_symbolic_index", ROOT / "server" / "cbms_symbolic_index.py")

to_esperanto = esperanto_bridge.to_esperanto
Codebook = codebook_engine.Codebook
SymbolicIndex = cbms_symbolic_index.SymbolicIndex


def demo(queries: List[str]) -> None:
    cb_path = MEM / "codebook" / "codebook.json"
    if not cb_path.exists():
        print(f"Codebook not found: {cb_path}")
        return
    cb = Codebook.load(cb_path)
    idx = SymbolicIndex(MEM, cb)
    built = idx.build(limit=None)
    print(f"Symbolic index built for {built} chunk(s).\n")

    for q in queries:
        eo = to_esperanto(q)
        codes = cb.encode_eo_to_cbms(eo)
        hits = idx.search(q, top_k=8)
        print("QUERY:", q)
        print("EO:", eo)
        print("CBMS:", codes)
        print("MATCHES:")
        if not hits:
            print("  (no symbolic matches)")
        else:
            for cid, score in hits:
                print(f"  - {cid} (score={score})")
        print("")


if __name__ == "__main__":
    demo([
        "Byłem dzisiaj w sklepie, kupiłem chleb.",
        "Wyjaśnij Korean-CBMS segmentację kluczy.",
        "Ile masz teraz chunków?",
    ])

