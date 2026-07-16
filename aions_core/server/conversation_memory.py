#!/usr/bin/env python3
from __future__ import annotations

import json
import time
import re
from pathlib import Path
from typing import Dict, Any, List


def _conv_dir(mem_root: Path) -> Path:
    d = mem_root / "conversations"
    d.mkdir(parents=True, exist_ok=True)
    return d


def log_exchange(mem_root: str | Path, session_id: str, user_text: str, assistant_text: str) -> int:
    mem = Path(mem_root)
    fp = _conv_dir(mem) / f"{session_id or 'default'}.jsonl"
    try:
        print(f"LOG path={fp}")
    except Exception:
        pass
    rec = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "user": user_text,
        "assistant": assistant_text,
    }
    with fp.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    try:
        return sum(1 for _ in fp.open("r", encoding="utf-8"))
    except Exception:
        return 1


def summarize_if_needed(cbms, session_id: str, every_n: int = 5) -> str | None:
    mem_root = cbms.memory_dir
    fp = _conv_dir(mem_root) / f"{session_id or 'default'}.jsonl"
    if not fp.exists():
        return None
    try:
        lines = fp.read_text(encoding="utf-8").splitlines()
    except Exception:
        return None
    n = len(lines)
    if n == 0 or n % every_n != 0:
        return None
    last = lines[-every_n:]
    convo = [json.loads(x) for x in last if x.strip()]
    text_blob = " \n ".join([(r.get("user") or "") + " \n " + (r.get("assistant") or "") for r in convo])
    concepts = cbms._extract_concepts(text_blob)
    summary = (
        "Podsumowanie rozmowy (ostatnie "
        + str(every_n)
        + " wymian):\n- Tematy: "
        + ", ".join(concepts or ["general"]) + "\n- Streszczenie: " + text_blob[:600]
    )
    try:
        cid = cbms.create_knowledge_chunk(summary, concept="conversation_summary", references=[], meta={"session_id": session_id})
        try:
            print(f"SUMMARY created {cid} for session={session_id}")
        except Exception:
            pass
    except Exception:
        cid = None
    return cid


def update_user_profile(cbms, user_text: str) -> str | None:
    text = user_text.strip()
    name = None
    m = re.search(r"moje imie(?:\s*to)?\s+([A-Za-zÀ-ÿ\-]+)", text, re.IGNORECASE)
    if not m:
        m = re.search(r"nazywam\s+si[eę]\s+([A-Za-zÀ-ÿ\-]+)", text, re.IGNORECASE)
    if m:
        name = m.group(1)
    if name:
        content = f"Profil użytkownika: imię={name} (źródło: rozmowa)"
        try:
            cid = cbms.create_knowledge_chunk(content, concept="user_profile", references=[])
            return cid
        except Exception:
            return None
    return None


def get_best_conversation_context(cbms, query: str, top_summaries: int = 2, top_profiles: int = 1) -> List[str]:
    texts: List[str] = []
    try:
        q_keys = cbms._kk_build_keys(query) if hasattr(cbms, "_kk_build_keys") else set()
        sum_ids = list((cbms.manifest.get("concept_map", {}) or {}).get("conversation_summary", []) or [])
        scored: List[tuple[int, str, str]] = []
        for cid in sum_ids:
            ch = cbms.retrieve_chunk(cid)
            if not ch:
                continue
            tx = ch.get("content", "")
            ov = len(q_keys & (cbms._kk_build_keys(tx) if hasattr(cbms, "_kk_build_keys") else set()))
            if ov > 0:
                scored.append((ov, cid, tx))
        for _, _, tx in sorted(scored, key=lambda x: -x[0])[:top_summaries]:
            texts.append(tx)
        prof_ids = list((cbms.manifest.get("concept_map", {}) or {}).get("user_profile", []) or [])
        for cid in prof_ids[-top_profiles:]:
            ch = cbms.retrieve_chunk(cid)
            if ch and ch.get("content"):
                texts.append(ch["content"])
    except Exception:
        pass
    return texts


def rollup_summaries(cbms, batch: int = 20) -> str | None:
    try:
        sum_ids = list((cbms.manifest.get("concept_map", {}) or {}).get("conversation_summary", []) or [])
        if len(sum_ids) and len(sum_ids) % batch == 0:
            latest = sum_ids[-batch:]
            texts = []
            for cid in latest:
                ch = cbms.retrieve_chunk(cid)
                if ch and ch.get("content"):
                    texts.append(f"[{cid}] {ch['content']}")
            roll = "Konsolidacja sesji (ostatnie " + str(batch) + "):\n\n" + "\n\n".join(texts)
            cid = cbms.create_knowledge_chunk(roll, concept="session_rollup", references=latest)
            return cid
    except Exception:
        return None
    return None
