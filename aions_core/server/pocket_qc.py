#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Any


def _logs_dir() -> Path:
    root = Path(os.environ.get("CBMS_BASE_DIR", Path(__file__).resolve().parent.parent))
    p = root / "logs"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _append_log(name: str, obj: Dict[str, Any]) -> None:
    try:
        f = _logs_dir() / name
        with f.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(obj, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _codebook_symbols_for_text(text: str, memory_dir: str | Path) -> int:
    try:
        from esperanto_bridge import to_esperanto  # type: ignore
        from codebook_engine import Codebook  # type: ignore
        mem = Path(memory_dir)
        cb_path = mem / "codebook" / "codebook.json"
        if not cb_path.exists():
            return 0
        cb = Codebook.load(cb_path)
        eo = to_esperanto(text)
        codes = cb.encode_eo_to_cbms(eo)
        return len(codes)
    except Exception:
        return 0


def qc_text(text: str, memory_dir: str | Path) -> Dict[str, Any]:
    logic_ok = not any(tok in text.upper() for tok in ["<SCRIPT", "DROP TABLE", "@@", "{ {", "}}}}"])
    cbms_count = _codebook_symbols_for_text(text, memory_dir)
    verdict = "PASS" if (logic_ok and cbms_count > 0) else ("RETRY" if logic_ok else "FAIL")
    out = {"type": "text", "verdict": verdict, "logic_ok": logic_ok, "cbms_symbols": cbms_count}
    _append_log("pocket_qc.jsonl", out)
    return out


def qc_crla_result(result: Dict[str, Any], memory_dir: str | Path) -> Dict[str, Any]:
    w = (result or {}).get("winner") or {}
    refused = bool(w.get("refused"))
    score = float(w.get("score", 0.0))
    f_det = float(w.get("f2_determinism", 0.0)) if isinstance(w.get("f2_determinism", 0.0), (int, float)) else 0.0
    logic_ok = (score >= 0.3) and (f_det >= 0.3) and not refused
    text = (w.get("text") or w.get("answer") or "")
    cbms_count = _codebook_symbols_for_text(text, memory_dir) if text else 0

    if logic_ok and cbms_count > 0:
        verdict = "PASS"
    elif not logic_ok and cbms_count == 0:
        verdict = "FAIL"
    else:
        verdict = "RETRY"

    out = {
        "type": "crla",
        "verdict": verdict,
        "refused": refused,
        "score": score,
        "f2_determinism": f_det,
        "cbms_symbols": cbms_count,
    }
    _append_log("pocket_qc.jsonl", out)
    return out

