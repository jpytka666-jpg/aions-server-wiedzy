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


def _bramka_zapisu(text: str) -> tuple[bool, str]:
    """
    Werdykt bramki `learning_gate` — czy tekst jest echem, czy trescia.

    DLACZEGO TA, A NIE LICZENIE SYMBOLI (pomiar 2026-08-16):
    poprzedni warunek PASS wymagal `cbms_symbols > 0`. Ksiazka kodowa ma 16 hasel,
    z czego piec to podrecznikowy przyklad o kupowaniu chleba. Sprawdzone na wiekszej
    ksiazce (477 hasel): sensowny akapit koduje sie na 1 symbol, echo na 0. Waskim
    gardlem nie jest ksiazka, tylko tlumacz PL->EO przed nia, zrobiony pod to samo demo.
    Do tego liczenie slow ze slownika mierzy SLOWNICTWO, a nasze echo jest nabite
    terminami systemowymi — przy dzialajacym tlumaczu wypadaloby LEPIEJ niz odpowiedz
    sensowna. Bramka mierzy to, o co chodzi, i jest skalibrowana: 0 falszywych alarmow
    na 164 blokach wiedzy, lapie 455 z 457 smieci.

    Gdy bramki nie da sie wczytac, mowimy o tym WPROST w werdykcie zamiast cicho
    przepuszczac — cichy fallback w kontroli jakosci to kontrola jakosci, ktorej nie ma.
    """
    try:
        from cbms_memory import CBMSMemory  # type: ignore
    except Exception as e:
        return False, f"bramka_niedostepna:{type(e).__name__}"
    try:
        # `learning_gate` czyta wylacznie `self._GATE_RULES`, ktore jest atrybutem KLASY,
        # wiec dziala na instancji bez `__init__` i nie dotyka dysku.
        return CBMSMemory.learning_gate(CBMSMemory.__new__(CBMSMemory), text)
    except Exception as e:
        return False, f"bramka_blad:{type(e).__name__}"


def _ugruntowanie(chunk_ids, memory_dir: str | Path) -> tuple[int, int]:
    """
    Ile wskazanych blokow NAPRAWDE istnieje w bazie.

    Odpowiedz powolujaca sie na bloki, ktorych nie ma, jest nieugruntowana —
    i dotad nikt tego nie sprawdzal. Zwraca (istniejace, wskazane).
    """
    ids = [str(x) for x in (chunk_ids or []) if x]
    if not ids:
        return 0, 0
    katalog = Path(memory_dir) / "chunks"
    return sum(1 for i in ids if (katalog / f"{i}.json").exists()), len(ids)


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
    # POPRAWKA 2026-08-16: szukalismy pol `text` i `answer` W ZWYCIEZCY, a zwyciezca
    # ich NIE MA — `CandidateResult` niesie `answer_preview`. Pelna odpowiedz lezy
    # o poziom wyzej, w wyniku `run_crla`. Skutek bledu: `text` bylo zawsze puste,
    # `cbms_symbols` zawsze 0, wiec werdykt PASS byl nieosiagalny — kontrola jakosci
    # od poczatku wystawiala wylacznie oceny negatywne.
    text = ((result or {}).get("answer")
            or w.get("answer_preview")
            or "")
    cbms_count = _codebook_symbols_for_text(text, memory_dir) if text else 0

    # --- WERDYKT (przebudowany 2026-08-16, prerejestracja M17) -------------------
    # Trzy warunki zamiast liczenia symboli. Kazdy sprawdzalny, kazdy juz istnial
    # w systemie — nowego mechanizmu tu nie ma, jest tylko podlaczenie tego, co bylo.
    nie_echo, powod_bramki = _bramka_zapisu(text) if text else (False, "R6_za_krotkie")
    istniejace, wskazane = _ugruntowanie(w.get("chunk_ids"), memory_dir)
    ugruntowana = istniejace > 0

    if not logic_ok:
        verdict = "FAIL"
    elif nie_echo and ugruntowana:
        verdict = "PASS"
    else:
        verdict = "RETRY"

    out = {
        "type": "crla",
        "verdict": verdict,
        "refused": refused,
        "score": score,
        "f2_determinism": f_det,
        "nie_echo": nie_echo,
        "powod_bramki": powod_bramki,
        "blokow_istniejacych": istniejace,
        "blokow_wskazanych": wskazane,
        # DIAGNOSTYKA, NIE WARUNEK. Zostaje, zeby bylo widac stan lancucha
        # tlumacz -> ksiazka kodowa, ale nie decyduje juz o niczym.
        "cbms_symbols": cbms_count,
    }
    _append_log("pocket_qc.jsonl", out)
    return out

