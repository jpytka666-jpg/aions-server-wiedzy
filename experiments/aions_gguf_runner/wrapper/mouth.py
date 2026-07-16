"""Speak / understand / gate-first API (Faza 0)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from . import config
from .generate import SPEAK_SYSTEM, UNDERSTAND_SYSTEM, generate
from .protected_spans import ensure_preserved, extract, spans_ok

_JSON_RE = re.compile(r"\{[^{}]*\}", re.DOTALL)


def _extract_json(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    text = text.strip()
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass
    m = _JSON_RE.search(text)
    if m:
        try:
            obj = json.loads(m.group(0))
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass
    return None


def health() -> dict[str, Any]:
    cli = config.llama_cli_path()
    gguf = config.gguf_path()
    mode = config.backend_mode()
    return {
        "ok": True,
        "status": "ok",
        "backend": "llamacpp" if mode == "real" else "stub",
        "mode": mode,
        "model": config.model_tag(),
        "host": config.host(),
        "gguf": str(gguf),
        "gguf_exists": gguf.is_file(),
        "llama_cli": str(cli) if cli else None,
        "llama_cli_exists": bool(cli and cli.is_file()),
        "n_predict": config.n_predict(),
        "n_ctx": config.n_ctx(),
        "note": "Faza 0 — thin wrapper; gate hit must bypass this runner",
    }


def understand(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if not text:
        return {"ok": False, "error": "text is empty"}

    raw = generate(UNDERSTAND_SYSTEM, text, kind="understand", n_predict=min(120, config.n_predict()))
    if not raw.get("ok"):
        return raw

    parsed = _extract_json(raw.get("content") or "")
    if not parsed:
        # stub-like fallback from text heuristics if model garbled JSON
        return {
            "ok": False,
            "error": "model did not return valid JSON",
            "raw": (raw.get("content") or "")[:500],
            "model": raw.get("model"),
            "backend": raw.get("backend"),
            "mode": raw.get("mode"),
        }

    need = str(parsed.get("need", "cbms")).lower().strip()
    if need not in {"cbms", "memory", "web", "tool"}:
        need = "cbms"
    lang = str(parsed.get("lang", "pl")).lower().strip() or "pl"
    remember = parsed.get("remember", False)
    if isinstance(remember, str):
        remember = remember.strip().lower() in {"1", "true", "yes", "tak"}
    else:
        remember = bool(remember)
    summary = str(parsed.get("summary", "")).strip() or text[:200]

    return {
        "ok": True,
        "intent": {
            "lang": lang,
            "need": need,
            "remember": remember,
            "summary": summary,
        },
        "model": raw.get("model") or config.model_tag(),
        "backend": raw.get("backend"),
        "mode": raw.get("mode"),
        "wall_s": raw.get("wall_s"),
        "eval_count": raw.get("eval_count"),
    }


def speak(context: str, user_lang: str = "pl") -> dict[str, Any]:
    context = (context or "").strip()
    if not context:
        return {"ok": False, "error": "context is empty"}

    lang = (user_lang or "").strip().lower() or "pl"
    if lang.startswith("en"):
        lang_label = "English"
    elif lang.startswith("pl"):
        lang_label = "Polish"
    else:
        lang_label = lang

    user = (
        f"Reply language: {lang_label}\n\n"
        f"CONTEXT (facts from AIONS — use only this):\n{context}\n\n"
        "Write the short user-facing reply now. "
        "Preserve <addr>...</addr> and <<CB:*>> exactly."
    )
    raw = generate(SPEAK_SYSTEM, user, kind="speak")
    if not raw.get("ok"):
        return raw

    reply = (raw.get("content") or "").strip()
    if not reply:
        return {"ok": False, "error": "empty model reply", "model": raw.get("model")}

    reply, span_meta = ensure_preserved(context, reply)
    # hard mouth budget
    if len(reply) > 800:
        reply = reply[:800] + "…"

    return {
        "ok": True,
        "reply": reply,
        "user_lang": lang,
        "model": raw.get("model") or config.model_tag(),
        "backend": raw.get("backend"),
        "mode": raw.get("mode"),
        "wall_s": raw.get("wall_s"),
        "span_check": spans_ok(context, reply),
        "span_meta": span_meta,
        "protected": extract(context),
        "fallback_from_real_error": raw.get("fallback_from_real_error"),
        "next": raw.get("next"),
    }


def _try_gate(query: str) -> dict[str, Any] | None:
    """Read-only CBMS gate. Returns decision dict or None if unavailable."""
    root = config.REPO_ROOT
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        from control_plane.cbms_gate import (  # type: ignore
            compose_from_chunks,
            gate_decide,
            retrieve,
        )
    except Exception as e:
        return {"ok": False, "skipped": True, "error": str(e)[:200]}

    try:
        retrieval = retrieve(query, top_k=3)
        decision = gate_decide(retrieval, threshold=0.7)
        hit = bool(decision.get("hit"))
        out: dict[str, Any] = {
            "ok": True,
            "hit": hit,
            "confidence": retrieval.get("confidence"),
            "reason": decision.get("reason"),
            "source": "control_plane.cbms_gate",
        }
        if hit:
            out["reply"] = compose_from_chunks(
                query,
                retrieval.get("hits") or [],
                retrieval.get("codebook_symbols") or [],
            )
            out["runner_called"] = False
            out["mouth_calls"] = 0
        else:
            out["runner_called"] = True
        return out
    except Exception as e:
        return {"ok": False, "skipped": True, "error": str(e)[:200]}


def speak_with_gate(
    context: str,
    user_lang: str = "pl",
    *,
    gate_query: str | None = None,
) -> dict[str, Any]:
    """Gate-first: HIT → CBMS reply, runner not called; MISS → speak()."""
    if gate_query:
        gate = _try_gate(gate_query)
        if gate and gate.get("ok") and gate.get("hit"):
            return {
                "ok": True,
                "reply": gate.get("reply") or "",
                "user_lang": user_lang or "pl",
                "model": None,
                "backend": "cbms_gate",
                "mode": "bypass",
                "runner_called": False,
                "mouth_calls": 0,
                "gate": {
                    "hit": True,
                    "confidence": gate.get("confidence"),
                    "reason": gate.get("reason"),
                },
            }
        gate_info = gate
    else:
        gate_info = None

    result = speak(context, user_lang=user_lang)
    result["runner_called"] = True
    result["mouth_calls"] = 1
    if gate_info is not None:
        result["gate"] = {
            "hit": False,
            "confidence": gate_info.get("confidence"),
            "reason": gate_info.get("reason"),
            "skipped": gate_info.get("skipped"),
            "error": gate_info.get("error"),
        }
    return result
