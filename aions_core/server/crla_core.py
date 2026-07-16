import json
import time
import random
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Tuple


REFUSAL_TEXT = "NIE WIEM / BRAK DANYCH CBMS-KR."


@dataclass
class Candidate:
    candidate_id: str
    min_hits: int
    max_steps: int
    window_size: int
    style_strength: float = 0.0  # placeholder; stylist is optional/passive


@dataclass
class CandidateResult:
    candidate_id: str
    refused: bool
    score: float
    f1_facts: float
    f2_determinism: float
    f3_latency: float
    f4_policies: float
    f5_trace: float
    f6_hygiene: float
    latency_ms: float
    chunk_ids: List[str]
    answer_preview: str
    warnings: List[str]


def _normalize_latency_ms(latency_ms: float, target_ms: float = 150.0) -> float:
    # 1.0 is best (fast), 0.0 worst (very slow); linear clamp
    return max(0.0, min(1.0, 1.0 - (latency_ms / (2.0 * target_ms))))


def _compact_trace_score(trace: List[str]) -> float:
    # Prefer short, clean traces; simple heuristic
    if not trace:
        return 1.0
    ln = len(trace)
    return max(0.0, min(1.0, 1.0 / (1.0 + ln / 8.0)))


def _hygiene_score(text: str) -> float:
    # Very light check: ensure str, not too long, printable ratio
    if not isinstance(text, str):
        return 0.0
    if len(text) > 10000:
        return 0.5
    # Count non-printable as penalty
    bad = sum(1 for ch in text if ord(ch) < 9)
    return max(0.0, 1.0 - (bad / max(1, len(text))))


def generate_candidates(seed: int, n: int = 8) -> List[Candidate]:
    rng = random.Random(seed)
    cands: List[Candidate] = []
    for i in range(n):
        min_hits = rng.choice([1, 2, 3])
        max_steps = rng.choice([4, 6])
        window_size = rng.choice([5, 7])
        style_strength = rng.choice([0.0])  # stylist disabled by default
        cands.append(Candidate(
            candidate_id=f"C{i:02d}",
            min_hits=min_hits,
            max_steps=max_steps,
            window_size=window_size,
            style_strength=style_strength,
        ))
    return cands


def simulate_candidate(cbms, query: str, cand: Candidate) -> Tuple[Dict[str, Any], float]:
    # Use CBMS memory engine to think; measure latency
    start = time.time()
    result = cbms.cbms_think(query)
    latency_ms = (time.time() - start) * 1000.0
    return result, latency_ms


def score_candidate(query: str, cand: Candidate, sim: Dict[str, Any], latency_ms: float) -> CandidateResult:
    answer = sim.get("answer", "") or ""
    chunks = sim.get("chunk_references", []) or []
    trace = sim.get("thinking_trace", []) or []
    warnings: List[str] = []

    # F1: facts coverage via number of chunks (heuristic)
    f1 = min(1.0, len(chunks) / max(1, cand.window_size))

    # F2: determinism (assume 1.0 for current deterministic pipeline)
    f2 = 1.0

    # F3: latency (normalize around ~150ms)
    f3 = _normalize_latency_ms(latency_ms, target_ms=150.0)

    # F4: policies (refusal if below min_hits; otherwise OK)
    refused = False
    if len(chunks) < cand.min_hits or not answer.strip():
        refused = True
        f4 = 1.0  # refusing correctly is OK
    else:
        f4 = 1.0

    # F5: compact trace (prefer short)
    f5 = _compact_trace_score(trace)

    # F6: hygiene (UTF-8/printable heuristic)
    f6 = _hygiene_score(answer)

    # Weighted sum
    score = (
        0.45 * f1 +
        0.15 * f2 +
        0.10 * f3 +
        0.20 * f4 +
        0.05 * f5 +
        0.05 * f6
    )

    return CandidateResult(
        candidate_id=cand.candidate_id,
        refused=refused,
        score=round(float(score), 6),
        f1_facts=round(float(f1), 6),
        f2_determinism=round(float(f2), 6),
        f3_latency=round(float(f3), 6),
        f4_policies=round(float(f4), 6),
        f5_trace=round(float(f5), 6),
        f6_hygiene=round(float(f6), 6),
        latency_ms=round(float(latency_ms), 3),
        chunk_ids=[str(x) for x in chunks],
        answer_preview=answer[:240],
        warnings=warnings,
    )


def _pairwise_tournament(results: List[CandidateResult]) -> CandidateResult:
    # Simple single-elimination on score; tie-breakers by latency then id
    pool = results[:]
    while len(pool) > 1:
        nxt: List[CandidateResult] = []
        for i in range(0, len(pool), 2):
            if i + 1 >= len(pool):
                nxt.append(pool[i])
                break
            a = pool[i]
            b = pool[i + 1]
            # Compare
            if a.score != b.score:
                winner = a if a.score > b.score else b
            elif a.latency_ms != b.latency_ms:
                winner = a if a.latency_ms < b.latency_ms else b
            else:
                winner = a if a.candidate_id < b.candidate_id else b
            nxt.append(winner)
        pool = nxt
    return pool[0]


def run_crla(cbms, query: str, seed: int = 123, n_candidates: int = 8) -> Dict[str, Any]:
    candidates = generate_candidates(seed=seed, n=n_candidates)
    cand_results: List[CandidateResult] = []
    for cand in candidates:
        sim, lat = simulate_candidate(cbms, query, cand)
        cand_results.append(score_candidate(query, cand, sim, lat))

    # Sort primarily by score desc, then latency asc, then id
    ranked = sorted(cand_results, key=lambda r: (-r.score, r.latency_ms, r.candidate_id))
    winner = _pairwise_tournament(ranked)

    # Winner answer decision
    if winner.refused:
        final_answer = REFUSAL_TEXT
    else:
        # Take answer from best simulated candidate (matching id)
        # Re-run once to emit consistent preview (cheap)
        sim, _ = simulate_candidate(cbms, query, Candidate(winner.candidate_id, 2, 6, 7))
        final_answer = sim.get("answer", "") or REFUSAL_TEXT

    scoreboard = [asdict(r) for r in ranked]
    out = {
        "query": query,
        "seed": seed,
        "winner": asdict(winner),
        "answer": final_answer,
        "scoreboard": scoreboard,
        "ts": time.time(),
    }
    return out

