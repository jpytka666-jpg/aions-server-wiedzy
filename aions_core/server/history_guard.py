#!/usr/bin/env python3
"""
Bramka historyczna: czy rzecz jest juz w ksiedze, czy nie.

POPRAWKI 2026-09-21 (audyt po commicie 1617f9d), trzy realne bledy:

1. FALSZYWE "KNOWN" NA POJEDYNCZYCH POSPOLITYCH SLOWACH.
   Regula `q in h` dawala 80 punktow, gdy krotkie zapytanie bylo podciagiem
   dowolnego tytulu. Zmierzone przed poprawka: "system" -> KNOWN CBMS,
   "memory" -> KNOWN CBMS, "gate" -> KNOWN POCKET_QC, "new" -> KNOWN
   NOVELTY_NEEDS_HISTORY, "pocket" -> KNOWN POCKET_QC.
   To odwraca sens bramki. Bramka ma blokowac falszywe "nowe", a tak
   ostemplowywala jako "znane" wszystko, co zawieralo pospolite slowo.
   Falszywe KNOWN jest grozniejsze niz falszywe UNKNOWN, bo UNKNOWN i tak
   NIE POZWALA powiedziec "nowe" — a KNOWN zagluszy prawdziwe znalezisko.
   Poprawka: zapytanie jednowyrazowe musi trafic DOKLADNIE w id, nazwe albo
   alias. Nie w tytul, nie przez podciag.

2. PODKRESLNIKI NIE BYLY NORMALIZOWANE.
   `_norm` zostawialo `_`, wiec maszynowy `R2_opakowanie_syntezy` trafial w
   100, a to samo napisane przez czlowieka ze spacjami — "R2 opakowanie
   syntezy" — wracalo jako UNKNOWN. Ta sama rzecz, dwa rozne werdykty.
   Poprawka: `_` jest teraz separatorem jak kazdy inny znak.

3. SLABE TRAFIENIA GINELY BEZ SLADU.
   Odrzucone dopasowania znikaly. Teraz wracaja w `possible_matches` przy
   UNKNOWN, zeby informacja nie przepadla, ale zeby NIE liczyla sie jako dowod.
"""
from __future__ import annotations
import json, re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "AIONS_CATALOG" / "architecture_history.json"

# Podciag liczy sie dopiero od tej dlugosci. Ponizej to loteria.
MIN_SUBSTRING_LEN = 8
PROG = 25


def _norm(value: str) -> str:
    # POPRAWKA 2: `_` NIE jest juz zachowywany, inaczej maszynowy kod bramki
    # i ludzki zapis tej samej rzeczy normalizuja sie inaczej.
    return re.sub(r"[^a-z0-9]+", " ", (value or "").casefold()).strip()


def load_ledger() -> dict[str, Any]:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def _identyfikatory(item: dict[str, Any]) -> list[str]:
    """Pola, ktore NAZYWAJA rzecz. Tu wolno trafic jednym slowem."""
    vals = [item.get("id", ""), item.get("name", "")]
    vals.extend(item.get("aliases") or [])
    return [_norm(str(v)) for v in vals if v]


def _opisy(item: dict[str, Any]) -> list[str]:
    """Pola, ktore rzecz OPISUJA. Tu jedno pospolite slowo nie wystarcza."""
    vals = [item.get("title", ""), item.get("statement", "")]
    return [_norm(str(v)) for v in vals if v]


def _hay(item: dict[str, Any]) -> list[str]:
    return _identyfikatory(item) + _opisy(item)


def _ocena(q: str, item: dict[str, Any]) -> int:
    qt = set(q.split())
    jedno_slowo = len(qt) <= 1

    best = 0
    for h in _identyfikatory(item):
        if not h:
            continue
        if q == h:
            return 100
        if jedno_slowo:
            # POPRAWKA 1: jedno slowo musi byc calym identyfikatorem, nie jego kawalkiem.
            continue
        if h in q and h in _tokeny_ciagle(q):
            best = max(best, 80)
        elif q in h and len(q) >= MIN_SUBSTRING_LEN:
            best = max(best, 80)

    if jedno_slowo:
        return best

    for h in _hay(item):
        if not h:
            continue
        ht = set(h.split())
        overlap = len(qt & ht)
        if overlap:
            best = max(best, int(60 * overlap / max(len(qt), 1)))
    return best


def _tokeny_ciagle(q: str) -> set[str]:
    """Wszystkie ciagle podciagi tokenow zapytania, zeby `h in q` trafialo na
    granicy slowa, a nie w srodku wyrazu ("new" w "renewal")."""
    tok = q.split()
    out = set()
    for i in range(len(tok)):
        for j in range(i + 1, len(tok) + 1):
            out.add(" ".join(tok[i:j]))
    return out


def lookup(text: str) -> list[dict[str, Any]]:
    q = _norm(text)
    if not q:
        return []
    out = []
    data = load_ledger()
    for section in ("mechanisms", "defects", "decisions"):
        for item in data.get(section, []):
            best = _ocena(q, item)
            if best >= PROG:
                row = dict(item)
                row["section"] = section
                row["match_score"] = best
                out.append(row)
    return sorted(out, key=lambda x: (-x["match_score"], x.get("id", "")))


def _slabe_trafienia(text: str) -> list[dict[str, str]]:
    """Co bylo blisko, ale nie wystarczylo. Informacja, NIE dowod."""
    q = _norm(text)
    if not q:
        return []
    qt = set(q.split())
    out = []
    data = load_ledger()
    for section in ("mechanisms", "defects", "decisions"):
        for item in data.get(section, []):
            if _ocena(q, item) >= PROG:
                continue
            for h in _hay(item):
                if h and (qt & set(h.split())):
                    out.append({"id": item.get("id", ""), "section": section})
                    break
    return out[:5]


def classify(text: str) -> dict[str, Any]:
    hits = lookup(text)
    if hits:
        top = hits[0]
        return {"history_status": "KNOWN", "id": top.get("id"), "section": top.get("section"),
                "status": top.get("status"), "known_since": top.get("known_since") or top.get("first_known"),
                "evidence": top.get("evidence", []), "match_score": top.get("match_score")}
    return {"history_status": "UNKNOWN_NOT_PROVEN_NEW", "evidence": [],
            "possible_matches": _slabe_trafienia(text)}


def validate(ledger_path: Path | None = None) -> list[str]:
    """
    Validate structure AND semantic evidence contracts.

    File existence alone is not evidence. Every record must carry at least one
    evidence_check. Each check names a file and content anchors that must
    actually occur in that file. This does not prove an arbitrary natural-
    language claim mathematically, but it prevents the specific failure where
    a real file about something else is cited as evidence.
    """
    errors = []
    path = ledger_path or LEDGER
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    for section in ("mechanisms", "defects", "decisions"):
        ids = set()
        for item in data.get(section, []):
            iid = item.get("id")
            if not iid:
                errors.append(f"{section}: missing id")
                continue
            if iid in ids:
                errors.append(f"{section}: duplicate id {iid}")
            ids.add(iid)

            ev = item.get("evidence") or []
            if not ev:
                errors.append(f"{iid}: no evidence")
            for rel in ev:
                if rel.startswith("commit "):
                    continue
                if not (ROOT / rel).exists():
                    errors.append(f"{iid}: missing evidence path: {rel}")

            contracts = item.get("evidence_checks") or []
            if not contracts:
                errors.append(f"{iid}: no semantic evidence_checks")
                continue
            for n, contract in enumerate(contracts, 1):
                rel = contract.get("path", "")
                if not rel:
                    errors.append(f"{iid}: evidence_check #{n} missing path")
                    continue
                p = ROOT / rel
                if not p.is_file():
                    errors.append(f"{iid}: semantic evidence file missing: {rel}")
                    continue
                if rel not in ev:
                    errors.append(f"{iid}: semantic evidence path not listed in evidence: {rel}")
                try:
                    content = p.read_text(encoding="utf-8").casefold()
                except Exception as e:
                    errors.append(f"{iid}: cannot read semantic evidence {rel}: {type(e).__name__}")
                    continue
                for anchor in contract.get("contains_all") or []:
                    if str(anchor).casefold() not in content:
                        errors.append(f"{iid}: semantic anchor missing in {rel}: {anchor!r}")
                any_anchors = contract.get("contains_any") or []
                if any_anchors and not any(str(a).casefold() in content for a in any_anchors):
                    errors.append(f"{iid}: none of semantic anchors found in {rel}: {any_anchors!r}")
    return errors
