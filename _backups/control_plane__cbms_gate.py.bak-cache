"""CBMS-first gate (KORZENIEC / Faza 1).

Złota zasada:
    confidence >= threshold  →  odpowiedź z chunków BEZ Ollamy
    confidence <  threshold  →  miss → Bielik + Hangul keys + <<CB:*>>

API (używane przez llm_adapter + gate_demo):
    retrieve(query) → {confidence, hits, codebook_symbols, hangul_keys, ...}
    gate_decide(retrieval, threshold) → {hit, ...}
    compose_from_chunks(...) → str
    gate_answer(query) → pełna odpowiedź (hit lokalnie / miss → Ollama)
    chat_cbms_first_full(query) → wrapper pod llm_adapter.chat_full

Read-only względem chunków produkcyjnych — nie woła cbms_think / create_knowledge_chunk.

Env:
    AIONS_CBMS_FIRST=1|0          (domyślnie 1)
    AIONS_CBMS_CONFIDENCE=0.7
    AIONS_PATH / CBMS_MEMORY_DIR
"""

from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

_STOP = frozenset(
    {
        "co", "to", "jest", "jak", "czy", "dla", "oraz", "the", "a", "an", "w", "i",
        "na", "z", "o", "po", "do", "sie", "się", "nie", "tym", "tej", "ten", "ta",
        "sa", "są", "byc", "być", "ma", "mam", "jestem", "kim", "jaka", "jaki",
        "jakie", "gdzie", "kiedy", "ile", "czyli", "or", "and", "of", "in", "on",
        "at", "for", "with", "from", "by", "as", "is", "are", "was", "were", "be",
        "been", "being", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "must", "shall", "can", "need", "jutro",
        "dzisiaj", "dzis", "dziś", "prosze", "proszę", "mi", "mnie", "dziala",
        "działa", "czym", "czego", "ktory", "który", "ktore", "które",
    }
)

_TOKEN_RE = re.compile(r"[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9_<>:/]{2,}", re.UNICODE)

_MEMORY: Any = None
_CODEBOOK: Any = None
_HANGUL_FN: Any = None


def _env(name: str, default: str) -> str:
    val = os.environ.get(name)
    return val if val not in (None, "") else default


def gate_enabled() -> bool:
    return _env("AIONS_CBMS_FIRST", "1").lower() in ("1", "true", "on", "yes")


def confidence_threshold(default: float = 0.7) -> float:
    try:
        return float(_env("AIONS_CBMS_CONFIDENCE", str(default)))
    except ValueError:
        return default


def _aions_path() -> Path:
    return Path(_env("AIONS_PATH", str(REPO_ROOT / "aions_core")))


def _memory_dir() -> Path:
    return Path(_env("CBMS_MEMORY_DIR", str(_aions_path() / "memory")))


def _ensure_server_path() -> None:
    server = str(_aions_path() / "server")
    core = str(_aions_path())
    for p in (server, core):
        if p not in sys.path:
            sys.path.insert(0, p)
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))


def _get_memory() -> Any | None:
    global _MEMORY
    if _MEMORY is not None:
        return _MEMORY
    try:
        _ensure_server_path()
        from cbms_memory import CBMSMemory  # type: ignore

        _MEMORY = CBMSMemory(memory_dir=str(_memory_dir()))
        return _MEMORY
    except Exception:
        return None


def _get_codebook() -> Any | None:
    global _CODEBOOK
    if _CODEBOOK is not None:
        return _CODEBOOK
    try:
        _ensure_server_path()
        from codebook_engine import Codebook  # type: ignore

        path = _memory_dir() / "codebook" / "codebook.json"
        if not path.exists():
            return None
        _CODEBOOK = Codebook.load(path)
        return _CODEBOOK
    except Exception:
        return None


def _make_hangul(chunk_id: str) -> str:
    global _HANGUL_FN
    if _HANGUL_FN is None:
        try:
            _ensure_server_path()
            from hangul_addressing import make_hangul_code  # type: ignore

            _HANGUL_FN = make_hangul_code
        except Exception:
            _HANGUL_FN = lambda data, length=23: data[:length]  # noqa: E731
    return _HANGUL_FN(chunk_id)


def _significant_tokens(text: str) -> list[str]:
    toks = [t.lower() for t in _TOKEN_RE.findall(text or "")]
    return [t for t in toks if t not in _STOP and len(t) > 2]


def _lexical_score(query: str, concept: str, content: str) -> float:
    qtoks = _significant_tokens(query)
    if not qtoks:
        return 0.0
    hay_concept = (concept or "").lower()
    hay_content = (content or "").lower()
    hits = 0.0
    for t in qtoks:
        if t in hay_concept:
            hits += 1.0
        elif t in hay_content:
            hits += 0.75
    return min(1.0, hits / len(qtoks))


def encode_query_symbols(query: str) -> list[str]:
    cb = _get_codebook()
    if cb is None:
        return []
    try:
        _ensure_server_path()
        from esperanto_bridge import to_esperanto  # type: ignore

        eo = to_esperanto(query)
        return list(cb.encode_eo_to_cbms(eo) or [])
    except Exception:
        try:
            return list(cb.encode_eo_to_cbms(query.lower()) or [])
        except Exception:
            return []


def format_cb_tokens(symbols: list[str]) -> str:
    return " ".join(f"<<CB:{s}>>" for s in symbols)


def _load_chunk(mem: Any, chunk_id: str) -> dict[str, Any] | None:
    try:
        data = mem.retrieve_chunk(chunk_id)
        if data:
            return data
    except Exception:
        pass
    path = _memory_dir() / "chunks" / f"{chunk_id}.json"
    try:
        import json

        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def _chroma_hits(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Best-effort Chroma — często padnięta lokalnie; nie blokuje gate."""
    try:
        _ensure_server_path()
        os.environ.setdefault("CHROMA_PATH", str(REPO_ROOT / "data" / "chroma"))
        from server.store import VectorStore  # type: ignore

        store = VectorStore(persist_path=os.environ.get("CHROMA_PATH"))
        raw = store.search("claude_marcin_main", query, top_k=top_k)
        out: list[dict[str, Any]] = []
        for h in raw:
            cid = str(h.get("id") or "")
            for prefix in ("tier1_cbms_", "cbms_", "chunk_"):
                if cid.startswith(prefix):
                    cid = cid[len(prefix) :]
            out.append(
                {
                    "id": cid,
                    "score": float(h.get("score") or 0.0),
                    "source": "chroma",
                }
            )
        return out
    except Exception:
        return []


def retrieve(query: str, top_k: int = 5) -> dict[str, Any]:
    """Główny retrieval: Korean Keys + lexical + codebook + (opcjonalnie) Chroma."""
    mem = _get_memory()
    symbols = encode_query_symbols(query)
    hits: list[dict[str, Any]] = []

    if mem is None:
        return {
            "query": query,
            "confidence": 0.0,
            "hits": [],
            "codebook_symbols": symbols,
            "hangul_keys": [],
            "error": "CBMSMemory unavailable",
        }

    kr_scores: dict[str, int] = {}
    nkeys = 1
    if getattr(mem, "korean_index_enabled", False) and hasattr(mem, "_kk_build_keys"):
        q_keys = mem._kk_build_keys(query)
        nkeys = max(len(q_keys), 1)
        for cid, keys in getattr(mem, "_chunk_keys", {}).items():
            ov = len(q_keys & keys)
            if ov > 0:
                kr_scores[cid] = ov

    sym_boost: dict[str, float] = {}
    if getattr(mem, "symbolic_enabled", False) and getattr(mem, "_symbolic_idx", None):
        try:
            for cid, cnt in mem._symbolic_idx.search(query, top_k=12):
                sym_boost[cid] = min(0.25, 0.08 * float(cnt))
        except Exception:
            pass

    chroma = _chroma_hits(query, top_k=top_k)
    chroma_by_id = {h["id"]: float(h["score"]) for h in chroma if h.get("id")}
    chroma_boost = {cid: min(0.35, score * 0.35) for cid, score in chroma_by_id.items()}

    ranked_ids = sorted(kr_scores.items(), key=lambda x: (-x[1], x[0]))
    candidates = [cid for cid, _ in ranked_ids[: max(50, top_k * 10)]]
    for cid in list(sym_boost) + list(chroma_by_id):
        if cid not in candidates:
            candidates.append(cid)

    q_upper = query.upper()
    for f in (_memory_dir() / "chunks").glob("K*.json"):
        if f.stem in q_upper and f.stem not in candidates:
            candidates.insert(0, f.stem)

    # Lexical / concept scan — KR top-N często pomija krótkie, precyzyjne chunki (np. KCBMSACCESS001)
    qtoks = _significant_tokens(query)
    # synonimy domenowe (Hangul = adres koreański w CBMS)
    expanded = list(qtoks)
    q_l0 = query.lower()
    if "hangul" in q_l0 or "hangul_code" in q_l0:
        expanded.extend(["korea", "korean", "koreańsk", "sylab", "adres"])
    if "chroma" in q_l0 or "recall" in q_l0:
        expanded.extend(["chroma", "pamięć", "memory", "sesja", "vector"])
    if "dostęp" in q_l0 or "access" in q_l0:
        expanded.extend(["dostęp", "chunk", "pełny", "access"])
    expanded = list(dict.fromkeys(expanded))

    try:
        scan_hits: list[tuple[int, str]] = []
        for f in (_memory_dir() / "chunks").glob("K*.json"):
            try:
                import json as _json

                meta = _json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            concept = (meta.get("concept") or "").lower()
            content_head = (meta.get("content") or "")[:1200].lower()
            blob = concept + "\n" + content_head
            n = sum(1 for t in expanded if len(t) >= 4 and t.lower() in blob)
            if n > 0:
                # bonus za trafienie w concept
                if any(t.lower() in concept for t in expanded if len(t) >= 4):
                    n += 2
                scan_hits.append((n, f.stem))
        scan_hits.sort(key=lambda x: (-x[0], x[1]))
        for _n, stem in scan_hits[:40]:
            if stem not in candidates:
                candidates.append(stem)
    except Exception:
        pass

    cb = _get_codebook()
    for cid in candidates:
        data = _load_chunk(mem, cid)
        if not data:
            continue
        content = (data.get("content") or "").strip()
        concept = (data.get("concept") or "").strip()
        if not content and not concept:
            continue
        lex = _lexical_score(query, concept, content)
        kr_ratio = min(1.0, float(kr_scores.get(cid, 0)) / float(nkeys))
        boost = sym_boost.get(cid, 0.0) + chroma_boost.get(cid, 0.0)

        # codebook phrase presence
        for sym in symbols:
            meta = (cb.symbols.get(sym) if cb else None) or {}
            phrases = list(meta.get("pl") or []) + list(meta.get("eo") or []) + [sym]
            blob = f"{concept}\n{content}".lower()
            if any(str(p).lower() in blob for p in phrases if p):
                boost = max(boost, 0.12)

        conf = 0.70 * lex + 0.20 * kr_ratio + boost
        chroma_raw = chroma_by_id.get(cid, 0.0)
        if chroma_raw > 0:
            conf = max(conf, 0.40 * lex + 0.60 * chroma_raw)
        if cid.upper() in q_upper:
            conf = max(conf, 0.92)
        if concept and concept.lower() in query.lower():
            conf = max(conf, 0.85)
        # Silny overlap leksykalny = pewny hit (krótkie kanoniczne chunki typu KCBMSACCESS001)
        if lex >= 0.55:
            conf = max(conf, 0.72 + 0.2 * (lex - 0.55))

        blob_l = f"{concept}\n{content}".lower()
        q_l = query.lower()
        domain_hits = 0
        for term in (
            "cbms", "crla", "hangul", "codebook", "esperanto", "chroma",
            "korzeniec", "korean", "hangul_code", "symbolic", "adresow",
            "dostęp", "pipeline", "chunk",
        ):
            if term in q_l and term in blob_l:
                domain_hits += 1
        if domain_hits:
            conf += min(0.20, 0.05 * domain_hits)

        # Trigramy bez leksyki nie mogą same zrobić gate hit
        if lex < 0.18 and cid.upper() not in q_upper:
            conf = min(conf, 0.65)

        hangul = (data.get("hangul_code") or "").strip() or _make_hangul(cid)
        sources = ["korean_keys", "lexical"]
        if cid in sym_boost:
            sources.append("symbolic")
        if cid in chroma_by_id:
            sources.append("chroma")

        hits.append(
            {
                "id": cid,
                "score": round(min(1.0, conf), 4),
                "text": content or concept,
                "concept": concept,
                "hangul_key": hangul,
                "lexical": round(lex, 4),
                "kr_ratio": round(kr_ratio, 4),
                "source": "+".join(sources),
                "full_content": True,
            }
        )

    # Chroma-only hits (nie weszły przez KR pool)
    for cid, chroma_score in chroma_by_id.items():
        if any(h["id"] == cid for h in hits):
            continue
        data = _load_chunk(mem, cid)
        if not data:
            continue
        content = (data.get("content") or "").strip()
        concept = (data.get("concept") or "").strip()
        lex = _lexical_score(query, concept, content)
        conf = max(chroma_score, 0.35 * lex + 0.65 * chroma_score)
        if lex < 0.28:
            conf = min(conf, 0.65)
        hits.append(
            {
                "id": cid,
                "score": round(min(1.0, conf), 4),
                "text": content or concept,
                "concept": concept,
                "hangul_key": (data.get("hangul_code") or "").strip() or _make_hangul(cid),
                "lexical": round(lex, 4),
                "kr_ratio": 0.0,
                "source": "chroma",
                "full_content": True,
            }
        )

    hits.sort(key=lambda h: (-h["score"], -h.get("lexical", 0), h["id"]))
    hits = hits[:top_k]
    confidence = float(hits[0]["score"]) if hits else 0.0
    hangul_keys = [h["hangul_key"] for h in hits if h.get("hangul_key")]

    return {
        "query": query,
        "confidence": round(confidence, 4),
        "hits": hits,
        "codebook_symbols": symbols,
        "hangul_keys": hangul_keys,
        "n_candidates": len(candidates),
    }


def gate_decide(retrieval: dict[str, Any], threshold: float = 0.7) -> dict[str, Any]:
    conf = float(retrieval.get("confidence") or 0.0)
    hit = conf >= float(threshold) and bool(retrieval.get("hits"))
    return {
        "hit": hit,
        "confidence": conf,
        "threshold": float(threshold),
        "reason": "confidence>=threshold" if hit else (
            "confidence<threshold" if retrieval.get("hits") else "no_hits"
        ),
    }


def compose_from_chunks(
    query: str,
    hits: list[dict[str, Any]],
    symbols: list[str] | None = None,
) -> str:
    symbols = symbols or []
    if not hits:
        return ""
    lines: list[str] = [
        f"[CBMS-gate HIT] Odpowiedź z pamięci (bez LLM). Query: {query.strip()}",
        "",
    ]
    if symbols:
        lines.append(f"Symbole codebook: {format_cb_tokens(symbols)}")
        lines.append("")
    for i, h in enumerate(hits, 1):
        addr = h.get("hangul_key") or _make_hangul(str(h.get("id") or ""))
        lines.append(
            f"### [{i}] {h.get('id')}  <addr>{addr}</addr>  "
            f"(conf={float(h.get('score') or 0):.2f}, concept={h.get('concept') or '—'})"
        )
        body = (h.get("text") or "").strip()
        if len(body) > 1200:
            body = body[:1200] + " […]"
        lines.append(body)
        lines.append("")
    lines.append("Źródło: CBMS chunks (read-only). Gate nie wywołał Ollamy/Bielika.")
    return "\n".join(lines).strip()


def enrich_prompt_context(retrieval: dict[str, Any]) -> str:
    """Blok Hangul + <<CB:*>> do promptu gdy gate miss."""
    parts: list[str] = []
    addrs = retrieval.get("hangul_keys") or [
        h.get("hangul_key") for h in retrieval.get("hits") or [] if h.get("hangul_key")
    ]
    if addrs:
        parts.append("<addr>" + " ".join(str(a) for a in addrs if a) + "</addr>")
    symbols = retrieval.get("codebook_symbols") or []
    if symbols:
        parts.append("<cbms>" + format_cb_tokens(list(symbols)) + "</cbms>")
    hits = retrieval.get("hits") or []
    if hits:
        brief = "; ".join(f"{h.get('id')}({h.get('score')})" for h in hits[:5])
        parts.append(f"CBMS candidates: {brief}")
    return "\n".join(parts)


def gate_answer(
    query: str,
    *,
    threshold: float | None = None,
    top_k: int = 5,
    tier: str = "small",
    history: list[dict[str, str]] | None = None,
    force_llm: bool = False,
) -> dict[str, Any]:
    """Hit → compose z chunków; miss → Bielik z kontekstem KORZENIEC."""
    thr = confidence_threshold() if threshold is None else float(threshold)
    started = time.time()
    retrieval = retrieve(query, top_k=top_k)
    decision = gate_decide(retrieval, threshold=thr)

    if decision["hit"] and not force_llm:
        content = compose_from_chunks(
            query,
            retrieval.get("hits") or [],
            retrieval.get("codebook_symbols") or [],
        )
        return {
            "content": content,
            "model": "cbms-gate",
            "provider": "cbms_gate",
            "tier": tier,
            "tokens": None,
            "tok_s": None,
            "total_s": None,
            "wall_s": round(time.time() - started, 2),
            "gate": "hit",
            "confidence": retrieval.get("confidence"),
            "threshold": thr,
            "retrieval": retrieval,
            "cbms_hits": retrieval.get("hits") or [],
            "profile_loaded": False,
            "used_llm": False,
        }

    # miss → istniejący adapter LLM (force_llm omija rekurencję gate)
    from control_plane.llm_adapter import chat_full  # type: ignore

    enrich = enrich_prompt_context(retrieval)
    # Gdy Chroma pusta — przekaż treść z gate hits jako kontekst tekstowy
    result = chat_full(
        query,
        tier=tier,
        history=history,
        top_k=top_k,
        use_context=True,
        korzeniec_enrich=enrich or None,
        force_llm=True,
    )
    # Dołóż hit texts jeśli Chroma nic nie dała
    if not result.get("cbms_hits") and retrieval.get("hits"):
        result["cbms_hits"] = [
            {
                "id": h.get("id"),
                "score": h.get("score"),
                "text": h.get("text"),
                "full_content": True,
            }
            for h in retrieval["hits"]
        ]
    result["gate"] = "miss"
    result["confidence"] = retrieval.get("confidence")
    result["threshold"] = thr
    result["retrieval"] = retrieval
    result["used_llm"] = True
    result["wall_s"] = round(time.time() - started, 2)
    return result


def chat_cbms_first_full(
    user_message: str,
    tier: str = "small",
    *,
    history: list[dict[str, str]] | None = None,
    top_k: int = 3,
    force_llm: bool = False,
) -> dict[str, Any]:
    """Publiczny entrypoint dla llm_adapter.chat_full."""
    return gate_answer(
        user_message,
        top_k=max(top_k, 3),
        tier=tier,
        history=history,
        force_llm=force_llm,
    )


# Aliasy zgodne z wcześniejszymi szkicami
def evaluate(query: str, *, top_k: int = 5, threshold: float | None = None) -> dict[str, Any]:
    thr = confidence_threshold() if threshold is None else float(threshold)
    retrieval = retrieve(query, top_k=top_k)
    decision = gate_decide(retrieval, threshold=thr)
    return {**retrieval, **decision}
