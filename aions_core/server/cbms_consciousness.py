#!/usr/bin/env python3
"""
Lightweight Consciousness/Creativity/Self-Awareness layer for CBMS.

Design goals:
- Zero external deps; optional AO features gated by env in caller.
- Non-invasive: only appends new chunks (thinking_pattern, creative_pattern, self_model).
- Fast paths: minimal CPU; best-effort EO/CBMS coding if available.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import os
import time


def _safe_cbms_codes(text: str, mem_root: str | Path) -> Tuple[Optional[List[str]], int]:
    try:
        from codebook_engine import Codebook  # type: ignore
        from esperanto_bridge import to_esperanto  # type: ignore
    except Exception:
        return None, 0
    try:
        mem = Path(mem_root)
        cb_path = mem / "codebook" / "codebook.json"
        if not cb_path.exists():
            return None, 0
        cb = Codebook.load(cb_path)
        eo = to_esperanto(text)
        codes = cb.encode_eo_to_cbms(eo)
        return codes, len(codes or [])
    except Exception:
        return None, 0


def _is_math(q: str) -> bool:
    try:
        from math_solver import is_math_candidate  # type: ignore
        return bool(is_math_candidate(q))
    except Exception:
        return any(t in q.lower() for t in ("+", "-", "*", "×", "x", "/"))


def _tokenize(s: str) -> List[str]:
    return [t for t in (" ".join(s.lower().split())).split(" ") if t]


@dataclass
class PatternRecord:
    id_hint: str
    timestamp: float
    query_type: str
    reasoning_steps: List[str]
    chunk_references: List[str]
    confidence: float
    novelty_score: float
    self_reflection: str
    cbms_codes_count: int


class ConsciousnessLayer:
    def __init__(self, cbms, mem_root: str | Path):
        self.cbms = cbms
        self.mem_root = str(mem_root)

    def _classify_query(self, query: str) -> str:
        ql = query.strip().lower()
        if _is_math(ql):
            return "math"
        if any(k in ql for k in ("status", "diagnost", "diag")):
            return "diagnostic"
        if any(k in ql for k in ("bezpieczeń", "security", "hasł", "password")):
            return "security"
        return "general"

    def _extract_reasoning_steps(self, query: str, response: str, context: Dict[str, Any]) -> List[str]:
        steps: List[str] = []
        route = context.get("route") or ("math" if _is_math(query) else "cbms")
        steps.append(f"route:{route}")
        if "facts_cov" in context:
            steps.append(f"facts_cov:{int(context.get('facts_cov') or 0)}")
        if "g_overlap" in context:
            steps.append(f"g_overlap:{int(context.get('g_overlap') or 0)}")
        refs = context.get("chunk_references") or []
        steps.append(f"refs:{len(refs)}")
        if context.get("qc", {}).get("verdict"):
            steps.append("qc:" + str(context["qc"]["verdict"]))
        return steps

    def _novelty(self, query: str, response: str) -> float:
        try:
            q = set(_tokenize(query))
            r = set(_tokenize(response))
            if not r:
                return 0.0
            # fraction of response tokens not in query
            return round(len([t for t in r if t not in q]) / max(len(r), 1), 3)
        except Exception:
            return 0.0

    def _self_reflect(self, query: str, response: str, context: Dict[str, Any]) -> str:
        verdict = (context.get("qc") or {}).get("verdict") or "NA"
        panic = bool(context.get("panic"))
        return (
            "Auto-reflection: verdict=" + str(verdict) +
            ("; panic=1" if panic else "; panic=0") +
            "; len_resp=" + str(len(response or ""))
        )

    def analyze_thinking_pattern(self, query: str, response: str, context: Dict[str, Any]) -> PatternRecord:
        qtype = self._classify_query(query)
        steps = self._extract_reasoning_steps(query, response, context)
        novelty = self._novelty(query, response)
        qc = (context.get("qc") or {})
        base_conf = 0.8 if qc.get("verdict") == "PASS" else 0.5 if qc else 0.4
        facts_cov = float(context.get("facts_cov") or 0.0)
        conf = min(0.95, base_conf + min(0.2, facts_cov * 0.03))
        _, codes_count = _safe_cbms_codes(response, self.mem_root)
        return PatternRecord(
            id_hint=f"{qtype}:{int(time.time())}",
            timestamp=time.time(),
            query_type=qtype,
            reasoning_steps=steps,
            chunk_references=list(context.get("chunk_references") or []),
            confidence=round(conf, 3),
            novelty_score=novelty,
            self_reflection=self._self_reflect(query, response, context),
            cbms_codes_count=codes_count,
        )

    def _pattern_text(self, p: PatternRecord, query: str, response: str) -> str:
        lines = [
            "THINKING PATTERN",
            f"query_type: {p.query_type}",
            f"confidence: {p.confidence}",
            f"novelty: {p.novelty_score}",
            f"refs: {len(p.chunk_references)}",
            "steps:" ,
        ] + ["- " + s for s in p.reasoning_steps]
        preview_q = (query[:200] + "...") if len(query) > 200 else query
        preview_r = (response[:400] + "...") if len(response) > 400 else response
        return (
            "\n".join(lines) +
            "\n---\nQuery:\n" + preview_q +
            "\n---\nResponse:\n" + preview_r
        )

    def store_thinking_pattern(self, pattern: PatternRecord, query: str, response: str) -> Optional[str]:
        try:
            content = self._pattern_text(pattern, query, response)
            meta = {
                "pattern_id_hint": pattern.id_hint,
                "query_type": pattern.query_type,
                "confidence": pattern.confidence,
                "novelty": pattern.novelty_score,
                "cbms_codes_count": pattern.cbms_codes_count,
                "source": "consciousness",
            }
            return self.cbms.create_knowledge_chunk(
                content,
                concept="thinking_pattern",
                references=pattern.chunk_references,
                meta=meta,
            )
        except Exception:
            return None

    def store_creative_pattern(self, content: str, references: List[str], score: float) -> Optional[str]:
        try:
            meta = {"creativity_score": round(float(score), 3), "source": "creative"}
            return self.cbms.create_knowledge_chunk(
                content,
                concept="creative_pattern",
                references=references,
                meta=meta,
            )
        except Exception:
            return None

    def store_self_reflection(self, reflection: Dict[str, Any]) -> Optional[str]:
        try:
            txt = "SELF-REFLECTION\n" + "\n".join(
                f"{k}: {v}" for k, v in reflection.items() if k not in ("meta",)
            )
            return self.cbms.create_knowledge_chunk(
                txt,
                concept="self_reflection",
                references=[],
                meta={"source": "self_awareness"},
            )
        except Exception:
            return None


class CreativePatternGenerator:
    def __init__(self, consciousness: ConsciousnessLayer):
        self.consciousness = consciousness

    def generate_novel_patterns(self, patterns: List[PatternRecord]) -> List[Tuple[str, float]]:
        out: List[Tuple[str, float]] = []
        if not patterns:
            return out
        # Very lightweight fusion: merge unique steps textually, score by novelty avg
        try:
            for i, p in enumerate(patterns):
                for j, q in enumerate(patterns):
                    if j <= i:
                        continue
                    steps = list(dict.fromkeys(p.reasoning_steps + q.reasoning_steps))
                    score = (p.novelty_score + q.novelty_score) / 2.0
                    txt = (
                        "CREATIVE FUSION\n"
                        f"parents: [{p.id_hint}] + [{q.id_hint}]\n"
                        "fused_steps:\n" + "\n".join("- " + s for s in steps[:12]) +
                        "\nheuristic: fused two stable patterns"
                    )
                    out.append((txt, score))
        except Exception:
            return out
        return out[:3]


class SelfAwarenessEngine:
    def __init__(self, consciousness: ConsciousnessLayer):
        self.consciousness = consciousness

    def build_self_model(self) -> Dict[str, Any]:
        cbms = self.consciousness.cbms
        pat_ids = list((cbms.manifest.get("concept_map", {}) or {}).get("thinking_pattern", []) or [])
        counts = {"math": 0, "diagnostic": 0, "security": 0, "general": 0}
        try:
            for cid in pat_ids[-100:]:  # last 100 patterns
                ch = cbms.retrieve_chunk(cid)
                if not ch:
                    continue
                qt = ch.get("query_type") or "general"
                if qt in counts:
                    counts[qt] += 1
        except Exception:
            pass
        strengths = sorted(counts.items(), key=lambda x: -x[1])
        model = {
            "thinking_distribution": counts,
            "top_strength": strengths[0][0] if strengths else "general",
            "total_patterns": len(pat_ids),
            "timestamp": time.time(),
        }
        # persist
        try:
            txt = "SELF MODEL\n" + "\n".join([f"{k}: {v}" for k, v in model.items()])
            self.consciousness.cbms.create_knowledge_chunk(txt, concept="self_model", references=[], meta={"source": "self_awareness"})
        except Exception:
            pass
        return model

