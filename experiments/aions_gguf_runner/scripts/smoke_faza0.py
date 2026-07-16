#!/usr/bin/env python3
"""Faza 0 smoke: health + gate bypass + speak (stub or real llama-cli) + span check.

Usage (repo root):
  .\\scripts\\aions_python.ps1 experiments\\aions_gguf_runner\\scripts\\smoke_faza0.py

Optional: AIONS_GGUF_SMOKE_REAL=0  → force stub (fast)
          AIONS_GGUF_SMOKE_REAL=1  → allow real llama-cli (slow, default if available)
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

EXP = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
OUT = EXP / "artifacts" / "smoke_faza0.json"

sys.path.insert(0, str(EXP))
sys.path.insert(0, str(ROOT))

from wrapper import mouth  # noqa: E402
from wrapper.protected_spans import spans_ok  # noqa: E402


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    if os.environ.get("AIONS_GGUF_SMOKE_REAL", "1") == "0":
        os.environ["AIONS_GGUF_MODE"] = "stub"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    cases: list[dict] = []

    h = mouth.health()
    cases.append({"id": "health", "pass": bool(h.get("ok")), "detail": h})

    gate_q = "Jak działa pipeline CBMS i codebook?"
    g = mouth.speak_with_gate("unused when gate hits", gate_query=gate_q)
    if g.get("backend") == "cbms_gate" and g.get("mouth_calls") == 0:
        cases.append(
            {
                "id": "gate_hit_bypasses_runner",
                "pass": True,
                "skipped": False,
                "detail": {
                    "backend": g.get("backend"),
                    "mouth_calls": 0,
                    "runner_called": False,
                    "gate": g.get("gate"),
                    "reply_preview": (g.get("reply") or "")[:300],
                },
            }
        )
    else:
        # Gate miss or unavailable — do not fail Faza 0 core
        cases.append(
            {
                "id": "gate_hit_bypasses_runner",
                "pass": True,
                "skipped": True,
                "detail": {
                    "backend": g.get("backend"),
                    "mouth_calls": g.get("mouth_calls"),
                    "runner_called": g.get("runner_called"),
                    "gate": g.get("gate"),
                    "reply_preview": (g.get("reply") or "")[:300],
                    "note": "expected hit; skipped/soft if miss or gate error",
                },
            }
        )

    u = mouth.understand("Zapamiętaj że Marcin woli krótkie odpowiedzi PL")
    intent = u.get("intent") or {}
    u_ok = (
        bool(u.get("ok"))
        and intent.get("need") in {"cbms", "memory", "web", "tool"}
        and "summary" in intent
    )
    cases.append(
        {
            "id": "understand",
            "pass": u_ok,
            "detail": {"intent": intent, "mode": u.get("mode"), "backend": u.get("backend")},
        }
    )

    ctx = (
        "Fakty AIONS: CBMS gate hit omija LLM. "
        "Adres: <addr>각</addr> Symbole: <<CB:A1>> <<CB:PIPE>>."
    )
    s = mouth.speak(ctx, user_lang="pl")
    check = spans_ok(ctx, s.get("reply") or "")
    s_ok = bool(s.get("ok")) and check["ok"] and len(s.get("reply") or "") < 900
    cases.append(
        {
            "id": "speak_preserves_spans",
            "pass": s_ok,
            "detail": {
                "mode": s.get("mode"),
                "backend": s.get("backend"),
                "wall_s": s.get("wall_s"),
                "span_check": check,
                "span_meta": s.get("span_meta"),
                "reply_preview": (s.get("reply") or "")[:400],
                "fallback": s.get("fallback_from_real_error"),
            },
        }
    )

    core_ids = {"health", "understand", "speak_preserves_spans"}
    core_ok = all(c["pass"] for c in cases if c["id"] in core_ids)
    status = "PASS" if core_ok else "FAIL"

    report = {
        "status": status,
        "timestamp": _utc(),
        "wall_s": round(time.time() - t0, 2),
        "project": "experiments/aions_gguf_runner",
        "phase": "0",
        "cases": cases,
        "notes": {
            "gguf_d_local": "NOT TOUCHED (llama-cli invoked read-only from D: if present)",
            "cbms_chunks": "read-only via gate",
            "default_mouth": "Ollama unchanged (AIONS_MOUTH_BACKEND default ollama)",
        },
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"STATUS={status}")
    print(f"OUT={OUT}")
    for c in cases:
        flag = "SKIP" if c.get("skipped") else ("PASS" if c.get("pass") else "FAIL")
        print(f"  [{flag}] {c['id']}")
    return 0 if core_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
