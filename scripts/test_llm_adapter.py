#!/usr/bin/env python3
"""Test funkcjonalny warstwy "usta" AIONS (control_plane/llm_adapter.py).

Dowód, że LLM (Bielik przez Ollamę) NAPRAWDĘ odpowiada po polsku
oraz Z WYKORZYSTANIEM wstrzykniętego kontekstu (profil operatora + CBMS),
a nie generyczną pustką.

Uruchom przez venv AIONS:
    scripts\\aions_python.ps1 scripts\\test_llm_adapter.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from control_plane.llm_adapter import LLMError, chat_full, health  # noqa: E402

# Pytania testowe + słowa-klucze, które dowodzą, że kontekst został użyty.
QUESTIONS = [
    {
        "q": "Kim jestem i co studiuję?",
        "tier": "small",
        # profil operatora: identity.name = Marcin
        "context_markers": ["marcin"],
        "note": "sprawdza wstrzyknięcie operator_profile.json",
    },
    {
        "q": "Co to CBMS w moim systemie?",
        "tier": "small",
        "context_markers": ["cbms", "code book", "chunk", "pamię", "wiedz"],
        "note": "sprawdza wstrzyknięcie fragmentów CBMS (Chroma)",
    },
]

# Heurystyka "czy to polski": obecność polskich znaków lub częstych słów.
_PL_HINTS = ["ą", "ę", "ó", "ł", "ż", "ź", "ć", "ń", "ś", " jest", " jestem", " oraz", " który"]


def _looks_polish(text: str) -> bool:
    low = text.lower()
    return any(h in low for h in _PL_HINTS)


def _uses_context(text: str, markers: list[str]) -> bool:
    low = text.lower()
    return any(m in low for m in markers)


def main() -> int:
    print("=" * 72)
    print("AIONS — TEST WARSTWY 'USTA' (llm_adapter)")
    print("=" * 72)

    hp = health()
    print(f"Provider:    {hp.get('provider')}")
    print(f"Ollama host: {hp.get('ollama_host')}  up={hp.get('ollama_up')}")
    print(f"Model small: {hp.get('model_small')}   large: {hp.get('model_large')}")
    if hp.get("models"):
        print(f"Dostępne:    {', '.join(hp['models'])}")
    if hp.get("provider") == "ollama" and hp.get("ollama_up") is False:
        print("\n[FAIL] Ollama nie odpowiada — uruchom `ollama serve` i spróbuj ponownie.")
        return 1

    overall_ok = True
    for i, item in enumerate(QUESTIONS, 1):
        print("\n" + "-" * 72)
        print(f"[{i}] PYTANIE: {item['q']}")
        print(f"    (test: {item['note']})")
        try:
            out = chat_full(item["q"], tier=item["tier"], top_k=3)
        except LLMError as err:
            print(f"    [FAIL] LLMError: {err}")
            overall_ok = False
            continue

        answer = out["content"]
        hits = out.get("cbms_hits", [])
        print(f"\n    KONTEKST WSTRZYKNIĘTY: profil={out.get('profile_loaded')}, "
              f"CBMS fragmentów={len(hits)}")
        for h in hits:
            preview = h["text"].replace("\n", " ")[:110]
            print(f"      - {h.get('id')} (score={h.get('score')}): {preview}…")

        print("\n    ODPOWIEDŹ BIELIKA:")
        for line in answer.splitlines():
            print(f"      {line}")

        pl = _looks_polish(answer)
        ctx = _uses_context(answer, item["context_markers"])
        tok_s = out.get("tok_s")
        print(f"\n    METRYKI: model={out.get('model')} tok/s={tok_s} "
              f"tokens={out.get('tokens')} wall={out.get('wall_s')}s")
        verdict = "PASS" if (pl and ctx) else "FAIL"
        if verdict == "FAIL":
            overall_ok = False
        print(f"    OCENA: polski={pl}  używa_kontekstu={ctx}  ->  {verdict}")

    print("\n" + "=" * 72)
    print(f"WYNIK KOŃCOWY: {'PASS — AIONS gada po polsku z kontekstem' if overall_ok else 'FAIL — patrz wyżej'}")
    print("=" * 72)
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
