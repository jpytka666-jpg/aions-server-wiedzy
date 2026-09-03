#!/usr/bin/env python3
# ==========================================
# AIONS FILE HEADER
# ==========================================
# AUTHOR: M. SZUL
# AI MODEL: Claude Opus 5
# CREATED: 2026-08-27
# LANGUAGE: Python 3
#
# PROJECT: AIONS
# REPOSITORY: jpytka666-jpg/aions-server-wiedzy
# BRANCH: main
# COMPONENT: Unified Memory / jedna pamiec z dwoch
#
# PURPOSE:
#   One read and one write across both memories AIONS keeps, so a finding written once
#   is findable by either route and neither store can hold something the other has
#   never heard of.
#
# WHY IT EXISTS:
#   There are two memories and they did not know about each other. The vector store has
#   1244 entries in this session's collection and finds by MEANING. The block store has
#   171 blocks and finds by WORDS, exactly and in microseconds. A rule written into one
#   was invisible from the other: asked "czy edytowac plik czy wygenerowac go od nowa",
#   the vector store returned three unrelated entries at 0.51, 0.50, 0.49 and not the
#   rule that answers precisely that, because the rule had gone into the block store.
#
# WHY BOTH, NOT ONE:
#   By meaning  - knows that "wygenerowac od nowa" and "przepisac" are the same thing.
#                 Needs a model, answers approximately, cannot show WHY it matched.
#   By words    - exact, instant, no model, and can point at the symbol that decided.
#                 Blind to synonyms.
#   Measured on five real questions phrased the way a future situation would phrase
#   them: word search found the rule 5/5 only after the block was given a "when to
#   recall this" section; before that, 2/5.
#
# HOW RESULTS ARE MERGED:
#   By RANK, never by score. One store returns 14.06 and the other 0.567; adding those
#   or scaling one onto the other would invent a relationship that does not exist.
#   Reciprocal rank fusion asks only "how near the top was it in its own store", which
#   is the one thing both answers genuinely share. Every hit keeps its source, so the
#   caller always knows whether a match was exact or approximate.
#
# DATA POLICY:
#   Writing goes to BOTH stores or reports which one failed. A silent one-sided write is
#   how the split happened in the first place.
#
# TECH STACK:
#   Python 3. Rust is the default for this system and stays so - but both stores are
#   Python: chromadb has no Rust client here, and the block index this calls is the
#   Python module the memory server already loads. Reimplementing either in Rust would
#   mean a second definition of what a memory is, which is the exact fault this file
#   exists to repair. What we lose is start-up time, and nothing here runs per keystroke.
#
# DEPENDENCIES:
#   chromadb, cbms_shared_index, write_knowledge_block
#
# LOCAL WORKSPACE:
#   E:\server wiedzy\aions_core\server
#
# GIT COMMIT: PENDING
# ==========================================
"""Jedna pamiec z dwoch: szuka po znaczeniu i po slowach naraz, zapisuje do obu."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

MEMORY = Path(os.environ.get("AIONS_MEMORY") or Path(__file__).resolve().parent.parent / "memory")
CHROMA = Path(os.environ.get("CHROMA_PATH") or r"E:/server wiedzy/data/chroma")
SESJA = os.environ.get("AIONS_SESSION") or "claude_marcin_main"

# Reciprocal rank fusion. The constant damps the top of each list so a single store
# cannot dominate on rank alone; 60 is the value the method is usually used with and
# nothing here is sensitive enough to justify tuning it.
K_RANGI = 60


def _po_slowach(query: str, top_k: int) -> list[dict[str, Any]]:
    try:
        from cbms_shared_index import SharedBookIndex
        idx = SharedBookIndex(MEMORY)
        if idx.build() == 0:
            return []
        out = []
        for miejsce, (cid, wynik) in enumerate(idx.search(query, top_k=top_k), start=1):
            fragment, gdzie = idx.deep(cid, query, 200)
            out.append({
                "id": cid, "zrodlo": "slowa", "miejsce": miejsce,
                "wynik_wlasny": round(float(wynik), 3),
                "gdzie": gdzie, "tekst": fragment,
            })
        return out
    except Exception as exc:
        return [{"blad": f"szukanie po slowach: {type(exc).__name__}: {exc}"}]


def _po_znaczeniu(query: str, top_k: int) -> list[dict[str, Any]]:
    try:
        import chromadb
        klient = chromadb.PersistentClient(path=str(CHROMA))
        kol = klient.get_collection(f"session_{SESJA}")
        r = kol.query(query_texts=[query], n_results=top_k)
        out = []
        dokumenty = (r.get("documents") or [[]])[0]
        identy = (r.get("ids") or [[]])[0]
        odleglosci = (r.get("distances") or [[]])[0]
        for miejsce, (i, d) in enumerate(zip(identy, dokumenty), start=1):
            # Chroma returns a distance; nearer is smaller. Reported as-is rather than
            # converted into a similarity, because the conversion depends on the metric
            # and a wrong one reads like confidence.
            odl = odleglosci[miejsce - 1] if miejsce - 1 < len(odleglosci) else None
            out.append({
                "id": i, "zrodlo": "znaczenie", "miejsce": miejsce,
                "wynik_wlasny": round(float(odl), 3) if odl is not None else None,
                "tekst": (d or "")[:200],
            })
        return out
    except Exception as exc:
        return [{"blad": f"szukanie po znaczeniu: {type(exc).__name__}: {exc}"}]


def recall(query: str, top_k: int = 5) -> dict[str, Any]:
    """Both stores, merged by rank, every hit labelled with where it came from."""
    slowa = _po_slowach(query, top_k)
    znacz = _po_znaczeniu(query, top_k)

    bledy = [x["blad"] for x in slowa + znacz if "blad" in x]
    slowa = [x for x in slowa if "blad" not in x]
    znacz = [x for x in znacz if "blad" not in x]

    punkty: dict[str, float] = {}
    wpisy: dict[str, dict] = {}
    for lista in (slowa, znacz):
        for w in lista:
            punkty[w["id"]] = punkty.get(w["id"], 0.0) + 1.0 / (K_RANGI + w["miejsce"])
            # Keep the richer record: a word hit carries the passage and its offset.
            if w["id"] not in wpisy or w["zrodlo"] == "slowa":
                wpisy[w["id"]] = w
            else:
                wpisy[w["id"]] = {**wpisy[w["id"]], "takze": w["zrodlo"]}

    # Found by BOTH is the strongest signal available here - exact wording and meaning
    # agreeing is not something either store can fake on its own.
    for i in set(x["id"] for x in slowa) & set(x["id"] for x in znacz):
        wpisy[i]["oba_zrodla"] = True

    ranking = sorted(punkty.items(), key=lambda kv: -kv[1])[:top_k]
    return {
        "pytanie": query,
        "znalezione": [{**wpisy[i], "razem": round(p, 5)} for i, p in ranking],
        "po_slowach": len(slowa),
        "po_znaczeniu": len(znacz),
        "bledy": bledy or None,
    }


def remember(text: str, concept: str) -> dict[str, Any]:
    """Write to BOTH, and say plainly which half failed if one does."""
    wynik: dict[str, Any] = {}
    try:
        from write_knowledge_block import write_block
        wynik["blok"] = write_block(text, concept, source="pamiec-wspolna")
    except Exception as exc:
        wynik["blok"] = {"blad": f"{type(exc).__name__}: {exc}"}
    try:
        import chromadb
        klient = chromadb.PersistentClient(path=str(CHROMA))
        kol = klient.get_or_create_collection(f"session_{SESJA}")
        import hashlib
        doc_id = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
        kol.upsert(ids=[doc_id], documents=[text], metadatas=[{"pojecie": concept}])
        wynik["wektory"] = {"doc_id": doc_id}
    except Exception as exc:
        wynik["wektory"] = {"blad": f"{type(exc).__name__}: {exc}"}
    wynik["obie_polowy"] = "blad" not in wynik["blok"] and "blad" not in wynik["wektory"]
    return wynik


def main() -> int:
    import json
    if len(sys.argv) < 2:
        print("unified_memory.py <pytanie>              szukaj w obu pamieciach")
        print("unified_memory.py --zapisz <pojecie> <plik>   zapisz do obu")
        return 2
    if sys.argv[1] == "--zapisz":
        if len(sys.argv) < 4:
            print("--zapisz <pojecie> <plik>")
            return 2
        tekst = Path(sys.argv[3]).read_text(encoding="utf-8")
        print(json.dumps(remember(tekst, sys.argv[2]), ensure_ascii=False, indent=1))
        return 0
    print(json.dumps(recall(" ".join(sys.argv[1:])), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
