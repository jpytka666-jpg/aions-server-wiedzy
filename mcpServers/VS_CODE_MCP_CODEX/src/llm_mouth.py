"""
AIONS Mouth — thin Ollama/Qwen layer for aions-context MCP.

Qwen = translator / mouth only. AIONS decides (CBMS, memory, tools).
Does not invent facts; does not pretend to call tools.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional

try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None  # type: ignore

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
MOUTH_MODEL = os.environ.get("AIONS_MOUTH_MODEL", "aions-mouth")
MOUTH_TIMEOUT_S = float(os.environ.get("AIONS_MOUTH_TIMEOUT", "120"))
MOUTH_NUM_PREDICT = int(os.environ.get("AIONS_MOUTH_NUM_PREDICT", "200"))

UNDERSTAND_SYSTEM = """You are AIONS Mouth (Qwen): a thin intent parser / translator.
AIONS (the host system) makes all decisions. You do NOT call tools, browse, or invent facts.
Return ONLY valid JSON (no markdown) with keys:
- lang: "pl" | "en" | other ISO-ish code of the user text
- need: one of "cbms" | "memory" | "web" | "tool" (what AIONS should use next)
- remember: boolean — whether this looks worth storing in memory
- summary: short 1-2 sentence paraphrase of the user intent
Do not add other keys. Do not wrap in code fences."""

SPEAK_SYSTEM = """You are AIONS Mouth (Qwen): a thin translator / speaker.
AIONS decided the facts. You ONLY rephrase the given CONTEXT into a short, clear reply.
Rules:
- Use ONLY information present in CONTEXT. Never invent facts, URLs, or tool results.
- Do not pretend to call tools or search.
- Keep the answer short (2-6 sentences unless CONTEXT is a list that needs bullets).
- Match the requested user language (PL or EN).
- If CONTEXT is empty or insufficient, say you lack data — do not guess."""


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Best-effort JSON object extraction from model output."""
    if not text:
        return None
    text = text.strip()
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if m:
        try:
            obj = json.loads(m.group(0))
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass
    return None


def _chat(system: str, user: str, *, temperature: float = 0.2) -> Dict[str, Any]:
    """Call Ollama /api/chat. Returns {ok, content|error, model, raw?}."""
    if httpx is None:
        return {"ok": False, "error": "httpx not installed"}
    model = MOUTH_MODEL
    url = f"{OLLAMA_HOST}/api/chat"
    payload = {
        "model": model,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": MOUTH_NUM_PREDICT,
        },
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    try:
        with httpx.Client(timeout=MOUTH_TIMEOUT_S) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        return {"ok": False, "error": str(e), "model": model, "host": OLLAMA_HOST}

    content = ""
    msg = data.get("message") or {}
    if isinstance(msg, dict):
        content = (msg.get("content") or "").strip()
    return {
        "ok": True,
        "content": content,
        "model": data.get("model") or model,
        "host": OLLAMA_HOST,
        "eval_count": data.get("eval_count"),
        "total_duration_ns": data.get("total_duration"),
    }


def understand(text: str) -> Dict[str, Any]:
    """Parse user text into intent JSON for AIONS routing."""
    text = (text or "").strip()
    if not text:
        return {"ok": False, "error": "text is empty"}

    result = _chat(UNDERSTAND_SYSTEM, text, temperature=0.1)
    if not result.get("ok"):
        return result

    parsed = _extract_json(result["content"])
    if not parsed:
        return {
            "ok": False,
            "error": "model did not return valid JSON",
            "raw": result["content"][:500],
            "model": result.get("model"),
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
        "model": result.get("model"),
        "host": result.get("host"),
    }


def speak(context: str, user_lang: str = "") -> Dict[str, Any]:
    """Rephrase CONTEXT into a short reply in user_lang (pl/en)."""
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
        "Write the short user-facing reply now."
    )
    result = _chat(SPEAK_SYSTEM, user, temperature=0.3)
    if not result.get("ok"):
        return result

    reply = (result.get("content") or "").strip()
    if not reply:
        return {"ok": False, "error": "empty model reply", "model": result.get("model")}

    return {
        "ok": True,
        "reply": reply,
        "user_lang": lang,
        "model": result.get("model"),
        "host": result.get("host"),
    }
