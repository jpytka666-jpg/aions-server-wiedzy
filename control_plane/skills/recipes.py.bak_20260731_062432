"""AIONS Skill Engine - learned success recipes.

A recipe is a verified plan for a type of problem, plus WHY it worked (a snapshot
of world state + reasons). Saved only after verify-before-learn passes.

BRIDGE (recipes<->CBMS, 2026-07-16): przy save_recipe intencja + plan sa TEZ
indeksowane semantycznie w always-on Chroma (kolekcja session_aions_recipes),
zeby PARAFRAZA celu (inne slowa, ten sam sens) trafiala w zapisany plan bez
budzenia LLM. find_recipe_semantic() zwraca recipe gdy podobienstwo >= progu.
Zapis do Chromy jest fail-safe: gdy padnie, recipe i tak jest w JSON.
"""
from __future__ import annotations
import hashlib
import json
import os
import sys
from pathlib import Path

from . import world_state

REPO = Path(__file__).resolve().parents[2]
RECIPES_PATH = REPO / "runtime" / "state" / "skill_recipes.json"

# --- BRIDGE recipes<->CBMS ------------------------------------------------
_RECIPE_SESSION = "aions_recipes"  # -> kolekcja Chroma "session_aions_recipes"
_SEM_THRESHOLD_DEFAULT = 0.55
_VS = None  # in-process singleton VectorStore


def _sem_threshold() -> float:
    try:
        return float(os.environ.get("AIONS_RECIPE_SEM_THRESHOLD", _SEM_THRESHOLD_DEFAULT))
    except Exception:
        return _SEM_THRESHOLD_DEFAULT


def _get_vs():
    """Leniwie tworzy VectorStore (HTTP -> always-on Chroma :8000, z fallbackiem
    do embedded). Singleton w procesie. Zwraca None gdy niedostepny."""
    global _VS
    if _VS is not None:
        return _VS
    try:
        if str(REPO) not in sys.path:
            sys.path.insert(0, str(REPO))
        os.environ.setdefault("CHROMA_USE_HTTP", "true")
        from server.store_selector import VectorStore  # type: ignore
        _VS = VectorStore()
        return _VS
    except Exception:
        return None


def _index_recipe_to_cbms(key: str, intent: str, steps) -> bool:
    """Upsert intencji+planu do kolekcji recipes w Chromie. Fail-safe."""
    vs = _get_vs()
    if vs is None:
        return False
    try:
        coll = vs._get_coll(_RECIPE_SESSION)
        meta = {
            "intent": intent,
            "steps_json": json.dumps(steps, ensure_ascii=False),
            "type": "skill_plan",
            "n_steps": len(steps or []),
            "source": "recipe_bridge",
        }
        # deterministyczne id -> upsert (bez duplikatow)
        coll.upsert(ids=[key], documents=[intent], metadatas=[meta])
        return True
    except Exception:
        return False


def find_recipe_semantic(intent: str, threshold: float | None = None):
    """Semantyczne dopasowanie recipe po SENSIE intencji (parafraza).

    Zwraca {"id","intent","steps","score"} gdy najlepszy hit >= progu ORAZ
    ma poprawny plan (steps_json), inaczej None. Sam odczyt planu; walidacja
    skilli wzgledem registry nalezy do wywolawcy (goal_planner) -- tak jak
    dla LLM/CBMS, zero skrotow w bezpieczenstwie.
    """
    vs = _get_vs()
    if vs is None:
        return None
    thr = _sem_threshold() if threshold is None else float(threshold)
    try:
        hits = vs.search(_RECIPE_SESSION, intent, top_k=3)
    except Exception:
        return None
    for h in hits or []:
        score = float(h.get("score") or 0.0)
        if score < thr:
            continue
        meta = h.get("metadata") or {}
        steps_json = meta.get("steps_json")
        if not steps_json:
            continue
        try:
            steps = json.loads(steps_json)
        except Exception:
            continue
        if not isinstance(steps, list) or not steps:
            continue
        return {
            "id": h.get("id"),
            "intent": meta.get("intent") or "",
            "steps": steps,
            "score": score,
        }
    return None


# --- core recipes storage -------------------------------------------------


def _load():
    if RECIPES_PATH.exists():
        try:
            return json.loads(RECIPES_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save(d):
    RECIPES_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECIPES_PATH.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def _key(intent):
    return "recipe_" + hashlib.sha1(intent.lower().strip().encode("utf-8")).hexdigest()[:10]


def save_recipe(intent, steps, why=None):
    d = _load()
    k = _key(intent)
    d[k] = {
        "id": k,
        "type": "recipe",
        "intent": intent,
        "steps": steps,
        "why": why or [],
        "world": world_state.load(),
        "uses": d.get(k, {}).get("uses", 0),
    }
    _save(d)
    # BRIDGE: indeksuj tez semantycznie w CBMS/Chroma (fail-safe -- nie psuje
    # zapisu JSON gdy Chroma padnie).
    try:
        _index_recipe_to_cbms(k, intent, steps)
    except Exception:
        pass
    return k


def find_recipe(intent):
    return _load().get(_key(intent))


def mark_used(k):
    d = _load()
    if k in d:
        d[k]["uses"] = d[k].get("uses", 0) + 1
        _save(d)
