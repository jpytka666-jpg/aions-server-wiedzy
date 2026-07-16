"""
AIONS Mouth — thin Ollama / llama.cpp layer for aions-context MCP.

Qwen = translator / mouth only. AIONS decides (CBMS, memory, tools).
Does not invent facts; does not pretend to call tools.

Backends (env AIONS_MOUTH_BACKEND):
  ollama   — OLLAMA_HOST /api/chat
  llamacpp — AIONS GGUF Runner (experiments/aions_gguf_runner) in-process (default when set)
  gguf     — alias for llamacpp

If backend=ollama and Ollama is down (connection refused), auto-falls back to llamacpp.
HTTP GGUF server (:11435) is used ONLY when AIONS_GGUF_HTTP=1 — never as silent default
(avoids WinError 10061 noise when no GGUF HTTP daemon is running).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None  # type: ignore

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
GGUF_HOST = os.environ.get("AIONS_GGUF_HOST", "http://127.0.0.1:11435").rstrip("/")
MOUTH_MODEL = os.environ.get("AIONS_MOUTH_MODEL", "aions-mouth")
MOUTH_TIMEOUT_S = float(os.environ.get("AIONS_MOUTH_TIMEOUT", "120"))
MOUTH_NUM_PREDICT = int(os.environ.get("AIONS_MOUTH_NUM_PREDICT", "200"))


def mouth_backend() -> str:
    """Resolve mouth backend from env (llamacpp / ollama)."""
    raw = (os.environ.get("AIONS_MOUTH_BACKEND") or "").strip().lower()
    if raw in {"gguf", "llama", "llama.cpp", "llamacpp"}:
        return "llamacpp"
    if raw in {"ollama"}:
        return "ollama"
    # Unset: keep historical default (ollama), but MCP should set AIONS_MOUTH_BACKEND.
    return "ollama"


def _log(msg: str) -> None:
    print(f"[aions-mouth] {msg}", file=sys.stderr, flush=True)


def _is_connect_fail(err: str) -> bool:
    e = (err or "").lower()
    needles = (
        "10061",
        "connection refused",
        "connecterror",
        "connect call failed",
        "actively refused",
        "failed to establish",
        "name or service not known",
        "nodename nor servname",
        "timed out",
        "timeout",
    )
    return any(n in e for n in needles)


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
- Preserve ANY <addr>...</addr> and <<CB:*>> tokens EXACTLY — opaque CBMS addresses, not Korean NLG.
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
        return {"ok": False, "error": "httpx not installed", "backend": "ollama"}
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
        return {
            "ok": False,
            "error": str(e),
            "model": model,
            "host": OLLAMA_HOST,
            "backend": "ollama",
            "connect_fail": _is_connect_fail(str(e)),
        }

    content = ""
    msg = data.get("message") or {}
    if isinstance(msg, dict):
        content = (msg.get("content") or "").strip()
    return {
        "ok": True,
        "content": content,
        "model": data.get("model") or model,
        "host": OLLAMA_HOST,
        "backend": "ollama",
        "eval_count": data.get("eval_count"),
        "total_duration_ns": data.get("total_duration"),
    }


def _runner_root() -> Path:
    # mcpServers/VS_CODE_MCP_CODEX/src → repo root
    return Path(__file__).resolve().parents[3]


def _llamacpp_inprocess(kind: str, **kwargs: Any) -> Dict[str, Any]:
    """Import experiments/aions_gguf_runner.wrapper (Faza 0)."""
    exp = _runner_root() / "experiments" / "aions_gguf_runner"
    if str(exp) not in sys.path:
        sys.path.insert(0, str(exp))
    try:
        from wrapper import mouth as gguf_mouth  # type: ignore
    except Exception as e:
        return {"ok": False, "error": f"gguf wrapper import failed: {e}", "backend": "llamacpp"}

    if kind == "understand":
        return gguf_mouth.understand(kwargs.get("text") or "")
    if kind == "speak":
        return gguf_mouth.speak(kwargs.get("context") or "", user_lang=kwargs.get("user_lang") or "pl")
    return {"ok": False, "error": f"unknown kind {kind}", "backend": "llamacpp"}


def _llamacpp_http(kind: str, **kwargs: Any) -> Dict[str, Any]:
    if httpx is None:
        return {"ok": False, "error": "httpx not installed", "backend": "llamacpp"}
    try:
        with httpx.Client(timeout=MOUTH_TIMEOUT_S) as client:
            if kind == "understand":
                resp = client.post(f"{GGUF_HOST}/v1/understand", json={"text": kwargs.get("text") or ""})
            else:
                resp = client.post(
                    f"{GGUF_HOST}/v1/speak",
                    json={
                        "context": kwargs.get("context") or "",
                        "user_lang": kwargs.get("user_lang") or "pl",
                    },
                )
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict):
                data.setdefault("backend", "llamacpp")
                data.setdefault("host", GGUF_HOST)
            return data if isinstance(data, dict) else {"ok": False, "error": "bad response"}
    except Exception as e:
        return {"ok": False, "error": str(e), "backend": "llamacpp", "host": GGUF_HOST}


def _prefer_gguf_http() -> bool:
    return (os.environ.get("AIONS_GGUF_HTTP") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _via_llamacpp(kind: str, **kwargs: Any) -> Dict[str, Any]:
    """In-process llama-cli/GGUF by default; HTTP only if AIONS_GGUF_HTTP=1."""
    if _prefer_gguf_http():
        http_res = _llamacpp_http(kind, **kwargs)
        if http_res.get("ok"):
            return http_res
        _log(f"GGUF HTTP failed ({http_res.get('error')}); trying in-process")
        local = _llamacpp_inprocess(kind, **kwargs)
        if local.get("ok"):
            return local
        return {
            "ok": False,
            "error": local.get("error") or http_res.get("error") or "llamacpp failed",
            "backend": "llamacpp",
            "http_error": http_res.get("error"),
        }

    local = _llamacpp_inprocess(kind, **kwargs)
    if local.get("ok"):
        return local
    # Do NOT probe :11435 unless explicitly enabled — that caused WinError 10061
    # when Ollama was down and operators thought usta still hit Ollama.
    return local


def _parse_understand(result: Dict[str, Any], text: str) -> Dict[str, Any]:
    parsed = _extract_json(result["content"])
    if not parsed:
        return {
            "ok": False,
            "error": "model did not return valid JSON",
            "raw": result["content"][:500],
            "model": result.get("model"),
            "backend": result.get("backend"),
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
        "backend": result.get("backend") or "ollama",
    }


def understand(text: str) -> Dict[str, Any]:
    """Parse user text into intent JSON for AIONS routing."""
    text = (text or "").strip()
    if not text:
        return {"ok": False, "error": "text is empty"}

    backend = mouth_backend()
    if backend == "llamacpp":
        _log("understand via llamacpp")
        return _via_llamacpp("understand", text=text)

    result = _chat(UNDERSTAND_SYSTEM, text, temperature=0.1)
    if not result.get("ok"):
        if result.get("connect_fail") or _is_connect_fail(str(result.get("error") or "")):
            _log(
                f"ollama connect fail ({result.get('error')}); "
                "auto-fallback → llamacpp"
            )
            fb = _via_llamacpp("understand", text=text)
            if isinstance(fb, dict):
                fb.setdefault("fallback_from", "ollama")
                fb.setdefault("ollama_error", result.get("error"))
            return fb
        return result

    return _parse_understand(result, text)


def speak(context: str, user_lang: str = "") -> Dict[str, Any]:
    """Rephrase CONTEXT into a short reply in user_lang (pl/en)."""
    context = (context or "").strip()
    if not context:
        return {"ok": False, "error": "context is empty"}

    lang = (user_lang or "").strip().lower() or "pl"

    if mouth_backend() == "llamacpp":
        _log("speak via llamacpp")
        return _via_llamacpp("speak", context=context, user_lang=lang)

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
    result = _chat(SPEAK_SYSTEM, user, temperature=0.3)
    if not result.get("ok"):
        if result.get("connect_fail") or _is_connect_fail(str(result.get("error") or "")):
            _log(
                f"ollama connect fail ({result.get('error')}); "
                "auto-fallback → llamacpp"
            )
            fb = _via_llamacpp("speak", context=context, user_lang=lang)
            if isinstance(fb, dict):
                fb.setdefault("fallback_from", "ollama")
                fb.setdefault("ollama_error", result.get("error"))
            return fb
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
        "backend": "ollama",
    }
