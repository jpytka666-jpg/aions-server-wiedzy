"""AIONS LLM adapter — warstwa "usta" (Faza 5).

Cienki adapter, który pozwala AIONS *mówić* przez lokalny LLM (Ollama/Bielik),
wstrzykując do promptu kontekst z CBMS + profil operatora + historię.

NIE dotyka rule-based plannera. To wyłącznie warstwa generowania odpowiedzi.

Konfiguracja przez zmienne środowiskowe:
    AIONS_LLM_PROVIDER   ollama | openai | none        (domyślnie: ollama)
    OLLAMA_HOST          http://localhost:11434
    AIONS_LLM_MODEL_SMALL   model "mały/szybki"  (domyślnie: bielik-aions)
    AIONS_LLM_MODEL_LARGE   model "duży"         (domyślnie: phi4)
    AIONS_LLM_TIMEOUT    timeout HTTP w sekundach (domyślnie: 180)
    AIONS_PATH           katalog CBMS (domyślnie: <repo>/aions_core)
    CHROMA_PATH          ścieżka bazy Chroma (domyślnie: <repo>/data/chroma)
    AIONS_CBMS_FIRST     1 = CBMS-first gate przed Ollamą (domyślnie: 1)
    AIONS_CBMS_CONFIDENCE  próg gate hit (domyślnie: 0.7)

    # tylko provider=openai:
    OPENAI_API_KEY, OPENAI_BASE_URL (domyślnie https://api.openai.com/v1)

Użycie:
    from control_plane.llm_adapter import chat
    print(chat("Kim jestem?", tier="small"))
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Konfiguracja
# ---------------------------------------------------------------------------

def _env(name: str, default: str) -> str:
    val = os.environ.get(name)
    return val if val not in (None, "") else default


PROVIDER = _env("AIONS_LLM_PROVIDER", "ollama").lower()
OLLAMA_HOST = _env("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
MODEL_SMALL = _env("AIONS_LLM_MODEL_SMALL", "bielik-aions")
MODEL_LARGE = _env("AIONS_LLM_MODEL_LARGE", "phi4")
REQUEST_TIMEOUT = float(_env("AIONS_LLM_TIMEOUT", "600"))
NUM_PREDICT = int(_env("AIONS_LLM_NUM_PREDICT", "350"))

DEFAULT_SYSTEM_PROMPT = (
    "Jesteś AIONS — lokalny asystent operacyjny. Twój operator (użytkownik) ma na imię Marcin.\n"
    "AIONS = Advanced Intelligence Operating System: prywatny, offline-first system wiedzy\n"
    "oparty o CBMS (Code Book Memory System) i pamięć wektorową (ChromaDB).\n\n"
    "Zasady:\n"
    "- Odpowiadaj ZAWSZE po polsku, zwięźle i konkretnie.\n"
    "- Operator to Marcin — to on zadaje pytania; Ty jesteś jego narzędziem.\n"
    "- Poniżej dostajesz sekcje KONTEKST (profil operatora, fragmenty CBMS, historia).\n"
    "  Opieraj odpowiedź na tym kontekście, a nie na ogólnej wiedzy. Cytuj konkrety, gdy pasują.\n"
    "- Jeśli w kontekście brakuje danych — powiedz to wprost, nie zmyślaj.\n"
)


class LLMError(RuntimeError):
    """Czytelny błąd warstwy LLM (brak Ollamy, timeout, zły provider)."""


# ---------------------------------------------------------------------------
# Profil operatora
# ---------------------------------------------------------------------------

def _aions_path() -> Path:
    return Path(_env("AIONS_PATH", str(REPO_ROOT / "aions_core")))


def load_operator_profile() -> dict[str, Any]:
    """Wczytuje AIONS_PATH/memory/operator_profile.json (best-effort)."""
    path = _aions_path() / "memory" / "operator_profile.json"
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def _profile_summary(profile: dict[str, Any]) -> str:
    if not profile:
        return ""
    lines: list[str] = []
    ident = profile.get("identity", {})
    if ident:
        who = ", ".join(
            f"{k}: {v}" for k, v in ident.items() if v
        )
        lines.append(f"Operator — {who}")
    goals = profile.get("goals", [])
    if goals:
        gtxt = "; ".join(g.get("title", "") for g in goals if g.get("title"))
        if gtxt:
            lines.append(f"Cele operatora: {gtxt}")
    cases = [c for c in profile.get("active_cases", []) if c.get("status") in ("active", "in_progress")]
    if cases:
        ctxt = "; ".join(f"{c.get('title')} ({c.get('status')})" for c in cases)
        lines.append(f"Aktywne wątki: {ctxt}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Kontekst z CBMS (Chroma, sesja claude_marcin_main)
# ---------------------------------------------------------------------------

def _chunk_id(raw_id: str | None) -> str | None:
    """Sprowadza id z Chromy (np. 'tier1_cbms_K02D..') do id pliku chunka ('K02D..')."""
    if not raw_id:
        return None
    cid = str(raw_id)
    for prefix in ("tier1_cbms_", "cbms_", "chunk_"):
        if cid.startswith(prefix):
            cid = cid[len(prefix):]
    return cid


def _load_chunk_content(chunk_id: str | None) -> str | None:
    """Wczytuje PEŁNĄ treść chunka z aions_core/memory/chunks/<id>.json (jeśli jest).

    Chroma indeksuje tylko cienkie linie ('CBMS chunk … | size: N'); realna wiedza
    jest w plikach JSON (patrz KCBMSACCESS001)."""
    if not chunk_id:
        return None
    path = _aions_path() / "memory" / "chunks" / f"{chunk_id}.json"
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        content = (data.get("content") or "").strip()
        return content or None
    except Exception:
        return None


def cbms_context(query: str, top_k: int = 3, session: str = "claude_marcin_main") -> list[dict[str, Any]]:
    """Semantyczne wyszukanie top-k fragmentów CBMS. Best-effort — nigdy nie rzuca.

    Zwraca listę {id, score, text} gdzie text to PEŁNA treść chunka (z plików JSON),
    a nie tylko cienka linia indeksu z Chromy."""
    try:
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        os.environ.setdefault("CHROMA_PATH", str(REPO_ROOT / "data" / "chroma"))
        from server.store import VectorStore  # type: ignore

        store = VectorStore(persist_path=os.environ.get("CHROMA_PATH"))
        hits = store.search(session, query, top_k=top_k)
        out: list[dict[str, Any]] = []
        for h in hits:
            index_text = (h.get("text") or "").strip()
            cid = _chunk_id(h.get("id"))
            full = _load_chunk_content(cid)
            text = full or index_text
            if not text:
                continue
            out.append({
                "id": cid or h.get("id"),
                "score": round(float(h.get("score", 0.0)), 3),
                "text": text,
                "full_content": bool(full),
            })
        return out
    except Exception:
        return []


def _cbms_block(hits: list[dict[str, Any]], max_chars: int = 700) -> str:
    if not hits:
        return ""
    parts: list[str] = []
    for h in hits:
        snippet = h["text"]
        if len(snippet) > max_chars:
            snippet = snippet[:max_chars] + " […]"
        parts.append(f"[{h.get('id')} | score={h.get('score')}] {snippet}")
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Budowa promptu
# ---------------------------------------------------------------------------

def build_messages(
    user_message: str,
    *,
    system_prompt: str | None = None,
    profile: dict[str, Any] | None = None,
    cbms_hits: list[dict[str, Any]] | None = None,
    history: list[dict[str, str]] | None = None,
    korzeniec_enrich: str | None = None,
) -> list[dict[str, str]]:
    system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
    profile_text = _profile_summary(profile or {})
    cbms_text = _cbms_block(cbms_hits or [])

    context_sections: list[str] = []
    if profile_text:
        context_sections.append("### PROFIL OPERATORA\n" + profile_text)
    if cbms_text:
        context_sections.append("### KONTEKST CBMS (fragmenty pamięci)\n" + cbms_text)
    if korzeniec_enrich:
        context_sections.append("### KORZENIEC (adresy Hangul + codebook)\n" + korzeniec_enrich)

    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    for turn in history or []:
        role = turn.get("role")
        content = turn.get("content")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    if context_sections:
        user_content = (
            "\n\n".join(context_sections)
            + "\n\n### PYTANIE OPERATORA\n"
            + user_message
        )
    else:
        user_content = user_message
    messages.append({"role": "user", "content": user_content})
    return messages


# ---------------------------------------------------------------------------
# Klienci LLM
# ---------------------------------------------------------------------------

def _resolve_model(tier: str) -> str:
    return MODEL_LARGE if tier == "large" else MODEL_SMALL


def _call_ollama(messages: list[dict[str, str]], model: str) -> dict[str, Any]:
    try:
        import httpx  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise LLMError(f"Brak biblioteki httpx w venv AIONS: {exc}") from exc

    url = f"{OLLAMA_HOST}/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"num_predict": NUM_PREDICT},
    }
    try:
        resp = httpx.post(url, json=payload, timeout=REQUEST_TIMEOUT)
    except httpx.ConnectError as exc:
        raise LLMError(
            f"Ollama nie odpowiada pod {OLLAMA_HOST}. Uruchom serwer: `ollama serve`. ({exc})"
        ) from exc
    except httpx.TimeoutException as exc:
        raise LLMError(
            f"Timeout ({REQUEST_TIMEOUT}s) przy modelu '{model}'. "
            "Model może być wolny na CPU/GPU 4GB — zwiększ AIONS_LLM_TIMEOUT."
        ) from exc

    if resp.status_code != 200:
        raise LLMError(f"Ollama HTTP {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    content = (data.get("message") or {}).get("content", "")
    if not content:
        raise LLMError(f"Ollama zwróciło pustą odpowiedź: {json.dumps(data)[:300]}")

    eval_count = data.get("eval_count") or 0
    eval_dur = data.get("eval_duration") or 0
    tok_s = round(eval_count / (eval_dur / 1e9), 2) if eval_dur else None
    return {
        "content": content.strip(),
        "model": model,
        "tokens": eval_count,
        "tok_s": tok_s,
        "total_s": round((data.get("total_duration") or 0) / 1e9, 2),
    }


def _call_openai(messages: list[dict[str, str]], model: str) -> dict[str, Any]:
    try:
        import httpx  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise LLMError(f"Brak biblioteki httpx w venv AIONS: {exc}") from exc

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise LLMError("provider=openai wymaga zmiennej OPENAI_API_KEY.")
    base = _env("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    url = f"{base}/chat/completions"
    payload = {"model": model, "messages": messages}
    try:
        resp = httpx.post(
            url,
            json=payload,
            timeout=REQUEST_TIMEOUT,
            headers={"Authorization": f"Bearer {api_key}"},
        )
    except httpx.HTTPError as exc:
        raise LLMError(f"Błąd połączenia z OpenAI ({base}): {exc}") from exc
    if resp.status_code != 200:
        raise LLMError(f"OpenAI HTTP {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    content = data["choices"][0]["message"]["content"].strip()
    usage = data.get("usage", {})
    return {
        "content": content,
        "model": model,
        "tokens": usage.get("completion_tokens"),
        "tok_s": None,
        "total_s": None,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def chat_full(
    user_message: str,
    tier: str = "small",
    *,
    history: list[dict[str, str]] | None = None,
    top_k: int = 3,
    use_context: bool = True,
    system_prompt: str | None = None,
    korzeniec_enrich: str | None = None,
    force_llm: bool = False,
) -> dict[str, Any]:
    """Zwraca pełny wynik: content + metryki + użyty kontekst.

    tier: "small" -> bielik-aions (szybki, po polsku), "large" -> phi4.
    Gdy AIONS_CBMS_FIRST=1 i force_llm=False, deleguje do cbms_gate (KORZENIEC).
    """
    if not force_llm and _env("AIONS_CBMS_FIRST", "1").lower() in ("1", "true", "on", "yes"):
        from control_plane.cbms_gate import chat_cbms_first_full  # lazy — unikaj cykli importu

        return chat_cbms_first_full(
            user_message,
            tier=tier,
            history=history,
            top_k=top_k,
            force_llm=False,
        )

    provider = PROVIDER
    if provider == "none":
        raise LLMError(
            "AIONS_LLM_PROVIDER=none — warstwa LLM wyłączona. "
            "Ustaw AIONS_LLM_PROVIDER=ollama, aby AIONS mówił."
        )

    profile = load_operator_profile() if use_context else {}
    cbms_hits = cbms_context(user_message, top_k=top_k) if use_context else []
    messages = build_messages(
        user_message,
        system_prompt=system_prompt,
        profile=profile,
        cbms_hits=cbms_hits,
        history=history,
        korzeniec_enrich=korzeniec_enrich,
    )
    model = _resolve_model(tier)

    started = time.time()
    if provider == "ollama":
        result = _call_ollama(messages, model)
    elif provider == "openai":
        result = _call_openai(messages, model)
    else:
        raise LLMError(f"Nieznany AIONS_LLM_PROVIDER='{provider}' (ollama|openai|none).")

    result["provider"] = provider
    result["tier"] = tier
    result["wall_s"] = round(time.time() - started, 2)
    result["cbms_hits"] = cbms_hits
    result["profile_loaded"] = bool(profile)
    return result


def chat(
    user_message: str,
    tier: str = "small",
    *,
    history: list[dict[str, str]] | None = None,
    top_k: int = 3,
    use_context: bool = True,
    system_prompt: str | None = None,
    force_llm: bool = False,
) -> str:
    """Prosty interfejs: pytanie -> odpowiedź (str). CBMS-first gdy AIONS_CBMS_FIRST=1."""
    return chat_full(
        user_message,
        tier=tier,
        history=history,
        top_k=top_k,
        use_context=use_context,
        system_prompt=system_prompt,
        force_llm=force_llm,
    )["content"]


def health() -> dict[str, Any]:
    """Szybki status warstwy LLM (do diagnostyki / system_health)."""
    info: dict[str, Any] = {
        "provider": PROVIDER,
        "ollama_host": OLLAMA_HOST,
        "model_small": MODEL_SMALL,
        "model_large": MODEL_LARGE,
    }
    if PROVIDER != "ollama":
        info["ollama_up"] = None
        return info
    try:
        import httpx  # type: ignore

        r = httpx.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        info["ollama_up"] = r.status_code == 200
        if r.status_code == 200:
            info["models"] = [m.get("name") for m in r.json().get("models", [])]
    except Exception as exc:
        info["ollama_up"] = False
        info["error"] = str(exc)
    return info


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AIONS LLM adapter — szybki test")
    parser.add_argument("message", nargs="?", default="Cześć, kim jesteś?")
    parser.add_argument("--tier", default="small", choices=["small", "large"])
    parser.add_argument("--no-context", action="store_true")
    args = parser.parse_args()

    try:
        out = chat_full(args.message, tier=args.tier, use_context=not args.no_context)
    except LLMError as err:
        print(f"[LLM ERROR] {err}")
        raise SystemExit(1)
    print(out["content"])
    print(
        f"\n-- model={out['model']} tok/s={out.get('tok_s')} "
        f"tokens={out.get('tokens')} wall={out.get('wall_s')}s "
        f"cbms_hits={len(out.get('cbms_hits', []))} profile={out.get('profile_loaded')}"
    )
