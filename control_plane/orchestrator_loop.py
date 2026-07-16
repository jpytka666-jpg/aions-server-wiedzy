"""Minimal local understand → act → remember loop (no SaaS).

Flow:
  1) llm_mouth.understand  (intent JSON)
  2) cbms_gate.retrieve / compose  (local CBMS)
  3) llm_mouth.speak  (reply from CONTEXT only)
  4) optional Chroma memory_store via server.store (best-effort)

Usage:
  scripts/aions_python.ps1 control_plane/orchestrator_loop.py "co to jest CBMS"
  scripts/aions_python.ps1 control_plane/orchestrator_loop.py --mcp-smoke
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
MCP_SRC = REPO / "mcpServers" / "VS_CODE_MCP_CODEX" / "src"


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_paths() -> None:
    for p in (str(REPO), str(MCP_SRC), str(REPO / "server")):
        if p not in sys.path:
            sys.path.insert(0, p)


def run_local(query: str, store_memory: bool = True) -> dict[str, Any]:
    """Run thin loop using in-process mouth + CBMS gate."""
    _ensure_paths()
    import llm_mouth  # type: ignore
    from control_plane import cbms_gate

    t0 = time.perf_counter()
    understand = llm_mouth.understand(query)
    intent = (understand or {}).get("intent") or {}

    retrieval = cbms_gate.retrieve(query)
    decision = cbms_gate.gate_decide(retrieval)
    hits = list(retrieval.get("hits") or [])
    if decision.get("hit"):
        facts = cbms_gate.compose_from_chunks(
            query, hits, symbols=list(retrieval.get("codebook_symbols") or [])
        )
        act = {"path": "cbms_hit", "confidence": retrieval.get("confidence")}
    else:
        facts = (
            f"CBMS miss (confidence={retrieval.get('confidence')}). "
            f"Top hits: {hits[:3]}"
        )
        act = {"path": "cbms_miss", "confidence": retrieval.get("confidence")}

    context = (
        f"USER: {query}\n"
        f"INTENT: {json.dumps(intent, ensure_ascii=False)}\n"
        f"FACTS:\n{facts}\n"
    )
    spoken = llm_mouth.speak(context, user_lang=str(intent.get("lang") or "pl"))

    memory_doc_id = None
    if store_memory and intent.get("remember"):
        try:
            from server import store as chroma_store  # type: ignore

            text = (
                f"[orchestrator] {_utc()} q={query!r} "
                f"reply={(spoken or {}).get('reply', '')[:400]}"
            )
            # Best-effort; API shapes differ across store helpers.
            if hasattr(chroma_store, "add_memory"):
                memory_doc_id = chroma_store.add_memory(  # type: ignore[attr-defined]
                    "claude_marcin_main", text
                )
            elif hasattr(chroma_store, "Store"):
                memory_doc_id = "store_class_present_skip"
            else:
                memory_doc_id = "no_store_helper"
        except Exception as exc:  # pragma: no cover
            memory_doc_id = f"store_error:{exc}"

    out = {
        "ok": bool((understand or {}).get("ok")) and bool((spoken or {}).get("ok")),
        "ts": _utc(),
        "query": query,
        "understand": understand,
        "act": act,
        "speak": spoken,
        "memory_doc_id": memory_doc_id,
        "elapsed_s": round(time.perf_counter() - t0, 3),
        "backend": {
            "mouth": getattr(llm_mouth, "mouth_backend", lambda: "?")(),
            "cbms_first": cbms_gate.gate_enabled(),
        },
    }
    return out


def run_mcp_smoke_note() -> dict[str, Any]:
    """Document MCP-tool smoke order (executed by agent via MCP, not here)."""
    return {
        "ok": True,
        "mode": "mcp_smoke_protocol",
        "steps": [
            "llm_understand(text)",
            "cbms_search(query) or cbms_gate via control_plane",
            "llm_speak(context)",
            "memory_store(session_id, text)",
        ],
        "note": "Zero SaaS — only user-aions-context / local GGUF / CBMS / Chroma",
        "ts": _utc(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AIONS local orchestrator loop")
    parser.add_argument("query", nargs="?", default="co to jest CBMS")
    parser.add_argument("--mcp-smoke", action="store_true")
    parser.add_argument("--no-store", action="store_true")
    parser.add_argument(
        "--out",
        default=str(REPO / "runtime" / "docs" / "orchestrator_smoke.json"),
    )
    args = parser.parse_args(argv)

    if args.mcp_smoke:
        result = run_mcp_smoke_note()
    else:
        result = run_local(args.query, store_memory=not args.no_store)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\n[wrote] {out_path}", file=sys.stderr)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
