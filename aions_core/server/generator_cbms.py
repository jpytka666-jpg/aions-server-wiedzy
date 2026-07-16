#!/usr/bin/env python3
from __future__ import annotations

from typing import List, Dict, Any


def _load_chunk_texts(cbms, chunk_ids: List[str], limit: int = 5) -> List[str]:
    out: List[str] = []
    for cid in chunk_ids[:limit]:
        ch = cbms.retrieve_chunk(cid)
        if ch and ch.get("content"):
            out.append(ch["content"].strip())
    return out


def compose_answer(
    query: str,
    cbms,
    chunk_ids: List[str] | None = None,
    crla_result: Dict[str, Any] | None = None,
    convo_context: List[str] | None = None,
    style_prefs: Dict[str, Any] | None = None,
    persona: str = "default",
    max_points: int = 4,
) -> str:
    chunk_ids = chunk_ids or []
    texts = _load_chunk_texts(cbms, chunk_ids, limit=max_points)
    header = "Na bazie wiedzy CBMS przygotowałem ustrukturyzowaną odpowiedź:\n\n"
    if not texts:
        return header + "(brak wystarczających fragmentów do syntezy)"
    teza = f"Pytanie: {query.strip()}"
    lines = ["Kluczowe punkty:"]
    for i, tx in enumerate(texts, 1):
        snippet = (tx[:220] + "...") if len(tx) > 220 else tx
        lines.append(f"{i}. {snippet}")
    ctx_lines: List[str] = []
    if convo_context:
        ctx_lines.append("Kontekst rozmowy:")
        for i, c in enumerate(convo_context[:3], 1):
            sn = (c[:200] + "...") if len(c) > 200 else c
            ctx_lines.append(f"{i}. {sn}")
    crla_lines: List[str] = []
    if crla_result:
        w = crla_result.get("winner", {})
        if w and not w.get("refused"):
            try:
                wid = w.get("candidate_id")
                sc = float(w.get("score", 0.0))
                lat = float(w.get("latency_ms", 0.0))
                crla_lines.append(
                    f"Konfiguracja CRLA: zwycięzca {wid}, wynik {sc:.3f}, latencja {lat:.3f} ms."
                )
            except Exception:
                pass
    podsum = (
        "\nWnioski: odpowiedź oparto wyłącznie na wybranych fragmentach CBMS"
        f" (liczba: {len(texts)})."
    )
    parts = [header, teza, "\n" + "\n".join(lines)]
    if ctx_lines:
        parts.append("\n" + "\n".join(ctx_lines))
    if crla_lines:
        parts.append("\n" + "\n".join(crla_lines))
    parts.append(podsum)
    return "\n\n".join(parts) + f"\n\n[Źródło: CBMS, {len(chunk_ids)} chunków]"
