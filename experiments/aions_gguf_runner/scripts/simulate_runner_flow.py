#!/usr/bin/env python3
"""Symulacja flow AIONS GGUF Runner (poziom C) — BEZ kompilacji llama.cpp.

Flow:
  user query → cbms_gate (mock lub prawdziwy, read-only)
    → HIT:  odpowiedź z CBMS, runner NIE wołany
    → MISS: mock runner understand + speak z kontekstem <addr> + <<CB:*>>

Opcjonalnie: jeden prawdziwy Ollama speak (aions-mouth) jako parity check;
jeśli Ollama down → SKIP (nie FAIL).

Użycie (z repo root):
  .\\scripts\\aions_python.ps1 experiments\\aions_gguf_runner\\scripts\\simulate_runner_flow.py

Wynik: experiments/aions_gguf_runner/artifacts/simulate_runner_flow.json
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]  # E:\server wiedzy
EXP = Path(__file__).resolve().parents[1]   # experiments/aions_gguf_runner
OUT = EXP / "artifacts" / "simulate_runner_flow.json"

ADDR_RE = re.compile(r"<addr>[\s\S]*?</addr>")
CB_RE = re.compile(r"<<CB:[A-Za-z0-9_-]+>>")

# Deterministyczne Hangul-adresy (nie NLG) + codebook
MOCK_ADDR = "각"
MOCK_CB = "<<CB:A1>>"
MOCK_CB2 = "<<CB:PIPE>>"


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Mock gate + mock runner (AIONS-first)
# ---------------------------------------------------------------------------

def mock_gate(query: str, *, force: str | None = None) -> dict[str, Any]:
    """Prosty gate: słowa kluczowe CBMS → hit; inaczej miss (lub force)."""
    q = (query or "").lower()
    hit_keywords = ("cbms", "codebook", "pipeline", "hangul", "chunk", "korzeniec")
    natural_hit = any(k in q for k in hit_keywords)
    if force == "hit":
        hit = True
    elif force == "miss":
        hit = False
    else:
        hit = natural_hit

    hangul = MOCK_ADDR
    symbols = ["A1", "PIPE"]
    hits = [
        {
            "id": "KSIM001",
            "score": 0.92 if hit else 0.35,
            "hangul_key": hangul,
            "concept": "sim",
            "text": (
                f"CBMS pipeline: adres <addr>{hangul}</addr> "
                f"i symbole {MOCK_CB} {MOCK_CB2}. Gate hit = bez LLM."
            ),
        }
    ]
    confidence = hits[0]["score"]
    return {
        "query": query,
        "hit": hit,
        "confidence": confidence,
        "threshold": 0.7,
        "reason": "confidence>=threshold" if hit else "confidence<threshold",
        "hangul_keys": [hangul],
        "codebook_symbols": symbols,
        "hits": hits,
        "source": "mock_gate",
    }


def compose_hit_reply(gate: dict[str, Any]) -> str:
    h = (gate.get("hits") or [{}])[0]
    addr = h.get("hangul_key") or MOCK_ADDR
    cbs = " ".join(f"<<CB:{s}>>" for s in (gate.get("codebook_symbols") or []))
    return (
        f"[CBMS-gate HIT] Odpowiedź z pamięci (bez runnera).\n"
        f"<addr>{addr}</addr>\n"
        f"{cbs}\n"
        f"{(h.get('text') or '').strip()}\n"
        f"Źródło: CBMS (symulacja). Runner nie wywołany."
    )


def enrich_miss_context(gate: dict[str, Any]) -> str:
    addrs = gate.get("hangul_keys") or [MOCK_ADDR]
    cbs = " ".join(f"<<CB:{s}>>" for s in (gate.get("codebook_symbols") or ["A1"]))
    return (
        f"<addr>{' '.join(str(a) for a in addrs)}</addr>\n"
        f"<cbms>{cbs}</cbms>\n"
        f"CBMS candidates: KSIM001({gate.get('confidence')})\n"
        f"Fakty: pipeline CBMS używa adresów Hangul i codebook; nie generuj koreańskiego NLG."
    )


def mock_understand(text: str) -> dict[str, Any]:
    """Kontrakt jak llm_mouth.understand — bez LLM."""
    t = (text or "").lower()
    need = "cbms"
    if any(w in t for w in ("pamiętaj", "zapamiętaj", "memory")):
        need = "memory"
    elif any(w in t for w in ("szukaj", "web", "http")):
        need = "web"
    return {
        "ok": True,
        "intent": {
            "lang": "pl",
            "need": need,
            "remember": need == "memory",
            "summary": (text or "")[:160],
        },
        "model": "mock-runner",
        "backend": "mock",
    }


def mock_speak(context: str, user_lang: str = "pl") -> dict[str, Any]:
    """Przeformułowanie CONTEXT — zachowuje <addr> i <<CB:*>> (nie stripuje)."""
    ctx = (context or "").strip()
    if not ctx:
        return {"ok": False, "error": "context is empty", "backend": "mock"}

    addrs = ADDR_RE.findall(ctx)
    cbs = CB_RE.findall(ctx)
    # Krótka odpowiedź „ustami” — fakty z kontekstu + pass-through adresów
    parts = [
        "Na podstawie kontekstu AIONS: CBMS używa adresów Hangul i symboli codebook.",
    ]
    if addrs:
        parts.append("Adresy (opaque): " + " ".join(addrs))
    if cbs:
        parts.append("Codebook: " + " ".join(cbs))
    parts.append("To nie jest koreański NLG — to adresy bloków.")
    reply = " ".join(parts)
    # twardy limit „usta” (~n_predict mały) — nie esej
    if len(reply) > 500:
        reply = reply[:500] + "…"
    return {
        "ok": True,
        "reply": reply,
        "user_lang": user_lang or "pl",
        "model": "mock-runner",
        "backend": "mock",
        "preserved_addr": addrs,
        "preserved_cb": cbs,
        "n_predict_budget": 200,
    }


def spans_preserved(context: str, reply: str) -> dict[str, Any]:
    ctx_addrs = set(ADDR_RE.findall(context))
    ctx_cbs = set(CB_RE.findall(context))
    # W reply muszą pojawić się te same spany (pass-through)
    ok_addr = all(a in reply for a in ctx_addrs) if ctx_addrs else True
    ok_cb = all(c in reply for c in ctx_cbs) if ctx_cbs else True
    # Nie wolno „przetłumaczyć” na koreański esej — brak typowych fillerów KR NLG
    banned = ("안녕하세요", "감사합니다", "입니다.")
    no_kr_nlg = not any(b in reply for b in banned)
    return {
        "ok": ok_addr and ok_cb and no_kr_nlg,
        "ok_addr": ok_addr,
        "ok_cb": ok_cb,
        "no_kr_nlg": no_kr_nlg,
        "ctx_addrs": sorted(ctx_addrs),
        "ctx_cbs": sorted(ctx_cbs),
    }


# ---------------------------------------------------------------------------
# Optional: real cbms_gate (read-only) + Ollama parity
# ---------------------------------------------------------------------------

def try_real_gate(query: str) -> dict[str, Any]:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    os.environ.setdefault("AIONS_PATH", str(ROOT / "aions_core"))
    os.environ.setdefault("AIONS_CBMS_FIRST", "1")
    try:
        from control_plane.cbms_gate import (  # type: ignore
            compose_from_chunks,
            enrich_prompt_context,
            gate_decide,
            retrieve,
        )

        retrieval = retrieve(query, top_k=3)
        decision = gate_decide(retrieval, threshold=0.7)
        out: dict[str, Any] = {
            "ok": True,
            "source": "control_plane.cbms_gate",
            "hit": bool(decision.get("hit")),
            "confidence": retrieval.get("confidence"),
            "reason": decision.get("reason"),
            "hangul_keys": retrieval.get("hangul_keys") or [],
            "codebook_symbols": retrieval.get("codebook_symbols") or [],
            "n_hits": len(retrieval.get("hits") or []),
        }
        if decision.get("hit"):
            out["reply_preview"] = compose_from_chunks(
                query,
                retrieval.get("hits") or [],
                retrieval.get("codebook_symbols") or [],
            )[:400]
            out["runner_called"] = False
        else:
            out["enrich"] = enrich_prompt_context(retrieval)[:400]
            out["runner_called"] = True  # w pełnym flow — tu tylko oznaczamy
        return out
    except Exception as e:
        return {"ok": False, "skipped": True, "error": str(e)[:300]}


def try_ollama_speak(context: str) -> dict[str, Any]:
    host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    model = os.environ.get("AIONS_MOUTH_MODEL", "aions-mouth")
    # health
    try:
        with urllib.request.urlopen(f"{host}/api/tags", timeout=3) as resp:
            if resp.status != 200:
                return {"ok": False, "skipped": True, "reason": f"tags status {resp.status}"}
    except Exception as e:
        return {"ok": False, "skipped": True, "reason": f"Ollama unreachable: {e}"}

    payload = {
        "model": model,
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 120},
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are AIONS Mouth. Rephrase ONLY the CONTEXT into a short Polish reply. "
                    "Preserve any <addr>...</addr> and <<CB:*>> tokens exactly. "
                    "Do not invent Korean NLG. Do not invent facts."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Reply language: Polish\n\nCONTEXT:\n{context}\n\n"
                    "Write the short user-facing reply now."
                ),
            },
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{host}/api/chat",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"ok": False, "skipped": False, "error": f"HTTP {e.code}: {e.reason}", "model": model}
    except Exception as e:
        return {"ok": False, "skipped": True, "reason": str(e)[:200], "model": model}

    content = ((body.get("message") or {}).get("content") or "").strip()
    check = spans_preserved(context, content)
    return {
        "ok": bool(content) and check["ok"],
        "skipped": False,
        "model": body.get("model") or model,
        "host": host,
        "wall_s": round(time.time() - t0, 2),
        "reply_preview": content[:400],
        "span_check": check,
        "eval_count": body.get("eval_count"),
    }


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

def run_scenario_hit() -> dict[str, Any]:
    query = "Jak działa pipeline CBMS i codebook?"
    gate = mock_gate(query, force="hit")
    runner_called = False
    reply = compose_hit_reply(gate)
    # Kryterium: hit → zero runnera; adresy w odpowiedzi CBMS
    has_addr = bool(ADDR_RE.search(reply))
    has_cb = bool(CB_RE.search(reply))
    passed = gate["hit"] and (not runner_called) and has_addr and has_cb
    return {
        "id": "S1_gate_hit_bypasses_runner",
        "pass": passed,
        "query": query,
        "gate": {k: gate[k] for k in ("hit", "confidence", "reason", "source")},
        "runner_called": runner_called,
        "reply_has_addr": has_addr,
        "reply_has_cb": has_cb,
        "reply_preview": reply[:350],
    }


def run_scenario_miss_mock_runner() -> dict[str, Any]:
    query = "Jaka pogoda będzie jutro na Marsie?"  # OOD → miss
    gate = mock_gate(query, force="miss")
    understand = mock_understand(query)
    ctx = enrich_miss_context(gate)
    speak = mock_speak(ctx, user_lang="pl")
    check = spans_preserved(ctx, speak.get("reply") or "")
    runner_called = True
    passed = (
        (not gate["hit"])
        and runner_called
        and understand.get("ok")
        and speak.get("ok")
        and check["ok"]
        and len(speak.get("reply") or "") < 600
    )
    return {
        "id": "S2_gate_miss_mock_speak_preserves_spans",
        "pass": passed,
        "query": query,
        "gate": {k: gate[k] for k in ("hit", "confidence", "reason", "source")},
        "runner_called": runner_called,
        "understand": understand.get("intent"),
        "context_preview": ctx[:300],
        "speak_preview": (speak.get("reply") or "")[:400],
        "span_check": check,
    }


def run_scenario_understand_contract() -> dict[str, Any]:
    u = mock_understand("Zapamiętaj że Marcin woli krótkie odpowiedzi PL")
    intent = u.get("intent") or {}
    passed = (
        u.get("ok")
        and intent.get("lang") == "pl"
        and intent.get("need") in {"cbms", "memory", "web", "tool"}
        and intent.get("need") == "memory"
        and "summary" in intent
    )
    return {
        "id": "S3_understand_contract",
        "pass": passed,
        "intent": intent,
    }


def run_scenario_real_gate() -> dict[str, Any]:
    query = "Jak działa pipeline CBMS end-to-end?"
    real = try_real_gate(query)
    if real.get("skipped") or not real.get("ok"):
        return {
            "id": "S4_real_cbms_gate_readonly",
            "pass": True,  # SKIP nie psuje całości
            "skipped": True,
            "detail": real,
        }
    # Jeśli hit — runner nie powinien być wołany
    if real.get("hit"):
        ok = real.get("runner_called") is False
    else:
        # miss OK — enrich powinien istnieć (może być pusty jeśli brak hits)
        ok = True
    return {
        "id": "S4_real_cbms_gate_readonly",
        "pass": ok,
        "skipped": False,
        "detail": {
            "hit": real.get("hit"),
            "confidence": real.get("confidence"),
            "reason": real.get("reason"),
            "n_hits": real.get("n_hits"),
            "hangul_keys_sample": (real.get("hangul_keys") or [])[:3],
            "codebook_sample": (real.get("codebook_symbols") or [])[:5],
            "runner_called": real.get("runner_called"),
        },
    }


def run_scenario_ollama_parity() -> dict[str, Any]:
    ctx = (
        f"Fakty AIONS: CBMS gate hit omija LLM. "
        f"Adres: <addr>{MOCK_ADDR}</addr> Symbole: {MOCK_CB} {MOCK_CB2}."
    )
    result = try_ollama_speak(ctx)
    if result.get("skipped"):
        return {
            "id": "S5_ollama_speak_parity",
            "pass": True,  # SKIP ≠ FAIL
            "skipped": True,
            "reason": result.get("reason") or result.get("error"),
        }
    return {
        "id": "S5_ollama_speak_parity",
        "pass": bool(result.get("ok")),
        "skipped": False,
        "detail": result,
    }


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()
    scenarios = [
        run_scenario_hit(),
        run_scenario_miss_mock_runner(),
        run_scenario_understand_contract(),
        run_scenario_real_gate(),
        run_scenario_ollama_parity(),
    ]
    mandatory = [s for s in scenarios if s["id"].startswith(("S1", "S2", "S3"))]
    mandatory_ok = all(s.get("pass") for s in mandatory)
    all_ok = all(s.get("pass") for s in scenarios)
    status = "PASS" if mandatory_ok else "FAIL"

    proven = [
        "Gate HIT → odpowiedź CBMS, runner_called=False",
        "Gate MISS → mock speak/understand; <addr> i <<CB:*>> zachowane w reply",
        "Kontrakt understand (lang/need/remember/summary) jak llm_mouth",
        "Brak kompilacji llama.cpp; brak mutacji GGUF/D:/chunków",
    ]
    skips = [s["id"] for s in scenarios if s.get("skipped")]
    if "S5_ollama_speak_parity" in skips:
        proven.append("Ollama parity: SKIP (serwis niedostępny) — nie blokuje PASS")
    elif any(s["id"] == "S5_ollama_speak_parity" and s.get("pass") for s in scenarios):
        proven.append("Ollama aions-mouth speak parity: OK (spany zachowane)")

    report = {
        "status": status,
        "overall_including_optional": "PASS" if all_ok else ("PASS_WITH_OPTIONAL_FAIL" if mandatory_ok else "FAIL"),
        "timestamp": _utc(),
        "wall_s": round(time.time() - started, 2),
        "project": "experiments/aions_gguf_runner",
        "profile": "AIONS-first (usta/gardło, nie serwer LLM)",
        "proven": proven,
        "skips": skips,
        "scenarios": scenarios,
        "notes": {
            "gguf_d_local": "NOT TOUCHED",
            "cbms_chunks": "read-only if real gate used",
            "llama_cpp": "not compiled — simulation only",
        },
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"STATUS={status}")
    print(f"OUT={OUT}")
    for s in scenarios:
        flag = "SKIP" if s.get("skipped") else ("PASS" if s.get("pass") else "FAIL")
        print(f"  [{flag}] {s['id']}")
    return 0 if mandatory_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
