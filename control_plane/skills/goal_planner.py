"""AIONS Skill Engine -- goal-planner z malym LLM w petli (jadro decyzyjne).

Architektura (decyzja wlasciciela projektu): maly lokalny model (Phi-4-mini
przez llama.cpp) wybiera lancuch skilli Z KATALOGU (constrained choice, NIE
wolna generacja). Model nigdy nie wykonuje niczego sam i nigdy nie wymysla
skilli spoza dostarczonej listy kandydatow -- to deterministyczna walidacja
w tym pliku pilnuje twardo. Wykonanie i weryfikacja sa w 100% deterministyczne
(control_plane.skills.executor.run_chain, ktory przechodzi przez bramke
ryzyka gate.py). Eskalacja do duzego modelu jest tu tylko FLAGA w wyniku
({"status": "escalate", ...}) -- ten modul sam niczego nie eskaluje dalej.

Ten plik NIE modyfikuje planner.py / recipes.py / mouth.py / executor.py /
gate.py -- tylko je importuje i uzywa istniejacego API:
  - planner.plan(registry, intent)      -> recipe-first exact match
  - registry.search(query, top_k, types) -> lexical retrieval kandydatow
  - executor.run_chain(registry, steps, ctx) -> wykonanie przez bramke
  - recipes.save_recipe(intent, steps, why) -> verify-before-learn

Usta LLM: ten sam mechanizm co control_plane/operator/mouth.py (wrapper
generate.py z experiments/aions_gguf_runner, Phi-4-mini Q4 przez llama-cli,
brak Ollamy, subprocess in-process, pelny graceful fallback -- nigdy wyjatek
na zewnatrz z _call_llm).

Kontrakt:
    plan_goal(goal: str, registry, max_steps=5) -> dict
    execute_goal(goal: str, registry, ctx, learn=True) -> dict

CLI:
    python -m control_plane.skills.goal_planner "cel po polsku" [--dry-run] [--no-learn] [--no-cbms]

Notatka z live testow v1.0 (Bielik-4.5B Q4, prompt z 12 kandydatami): model
poprawnie wybiera skille z listy (0 halucynacji ID w obserwowanych probach),
ale czasem wypelnia opcjonalny input (np. host_alias) wartoscia-placeholderem
typu "<host_name>" zamiast go pominac. Taka wartosc przechodzi walidacje
kluczy (klucz jest poprawny), ale psuje wykonanie (np. SSH probuje polaczyc
sie z hostem o nazwie "<host_name>"). _looks_like_placeholder() ponizej
odrzuca takie wartosci na etapie walidacji, zeby skill dostal swoj wlasny,
bezpieczny default zamiast halucynowanego placeholdera.

WNIOSKI Z TESTOW v1.0 -> ZMIANY v1.1 (tuning):
  1. Bielik potrzebowal ~130s na prompt z 12 kandydatami, przy stalym limicie
     90s dawalo to wieczna eskalacje (llm_unavailable/timeout). Timeout jest
     teraz konfigurowalny przez env AIONS_PLANNER_TIMEOUT (default 240s).
  2. Model wstawial placeholdery typu "<host_name>", ale takze "gole" nazwy-
     -placeholdery bez nawiasow (np. "remote_host"). Filtr placeholderow
     rozszerzony o dopasowanie tekstowe (patrz _PLACEHOLDER_TOKENS) i o
     dowolne wystapienie '<'/'>' w srodku wartosci, oraz o puste stringi.
  3. KRYTYCZNE: handler skilla moze zwrocic {"ok": False, ...} BEZ wyjatku --
     executor.run_chain widzi to jako krok status="ok" (bo nie bylo
     wyjatku) i chain_result["verified"] wychodzi True, wiec wadliwa recipe
     zapisywala sie jako "zweryfikowana". execute_goal() ma teraz osobny
     GUARD OK-FALSE: kazdy krok z jawnym outputs["ok"] is False wymusza
     status="failed" na calosci i blokuje zapis recipe, niezaleznie od tego
     co zwrocil run_chain (patrz _step_explicit_ok_false / execute_goal).
  4. n_predict=200 ucinal JSON w polowie generacji przy planach 3-krokowych
     -> podniesiony do 300. Prompt jednoczesnie skrocony (top 6 kandydatow
     zamiast 12, opisy obciete do 80 znakow, w schemacie inputs pokazywane
     sa tylko nazwy pol WYMAGANYCH), zeby skrocic czas generacji mimo
     wiekszego n_predict.

v2.0 (decyzja wlasciciela projektu, podmiana produkcyjna): Bielik skasowany
z dysku, Phi-4-mini jest teraz JEDYNYM lokalnym modelem (2.2x szybszy w
testach A/B, 0 halucynacji obserwowanych). System prompt ponizej jest teraz
PO ANGIELSKU (Phi rozumie angielskie instrukcje lepiej/szybciej), user
prompt pozostaje dwujezyczny (cel moze byc po polsku, instrukcje/etykiety po
angielsku). Klient HTTP (control_plane/llm/server_client.py) korzysta teraz
z /v1/chat/completions + natywnego szablonu czatu Phi (--jinja po stronie
serwera) zamiast recznie budowanego ChatML.

v2.1 (Faza 3, KORZENIEC cache-layer, "zanim zapytasz Phi, sprawdz czy
odpowiedz nie lezy juz w pamieci CBMS/recipes"): plan_goal() dostal DRUGI
poziom cache'a PRZED wywolaniem LLM (recipe exact-match z planner.plan() byl
juz pierwszym poziomem i zostaje bez zmian). Nowy krok: cbms_gate.evaluate
(goal) -- jesli gate ma HIT (confidence >= threshold) I da sie z hitu
zbudowac WALIDNY, wykonywalny lancuch skilli (patrz _steps_from_cbms_hit),
uzywamy go zamiast wolac Phi (source="cbms_cache"). CBMS chunks sa w
wiekszosci WIEDZA TEKSTOWA, nie gotowymi planami skilli -- gdy hit istnieje
ale nie da sie z niego zbudowac wykonywalnego lancucha, to nadal MISS dla
PLANU (mimo ze CBMS "cos wiedzial") i lecimy normalnie do LLM. Kazda decyzja
cache'a jest logowana do runtime/state/cbms_planner_log.jsonl. Flaga env
AIONS_CBMS_CACHE (domyslnie ON) i CLI --no-cbms pozwalaja to wylaczyc. Wynik
plan_goal() ma teraz zawsze pole "cache": {"checked", "hit", "confidence",
"source"}. cbms_gate.py, llm_adapter.py, orchestrator_loop.py, server_client.py,
executor.py, gate.py NIE zostaly ruszone poza samym cbms_gate.py (rezydentny
cache retrieve(), patrz cbms_gate.py naglowek) -- ten modul tylko IMPORTUJE
cbms_gate.evaluate/confidence_threshold, tak jak juz importuje planner/
recipes/executor.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Optional

from . import executor, planner, recipes

# control_plane/skills/goal_planner.py -> parents[2] == repo root (tak samo
# jak w recipes.py / gate.py).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_RUNNER_DIR = _REPO_ROOT / "experiments" / "aions_gguf_runner"

# v2.1: log decyzji CBMS-first cache'a dla PLANU (hit/miss/error), osobny od
# runtime/state/cbms_cache.json (ktory jest w cbms_gate.py i cache'uje surowy
# retrieve(), niezaleznie od tego czy da sie z niego zbudowac plan skilli).
_CBMS_LOG_PATH = _REPO_ROOT / "runtime" / "state" / "cbms_planner_log.jsonl"

# v2.1 (backlog): fallback CLI naprawiony -- AIONS_LLAMA_CLI wskazuje teraz
# na zabezpieczona kopie binarki (E:\LOCAL LLM MODELS\llama-runtime\) zamiast
# na skasowana sciezke Bielika. Model docelowy to Phi-4-mini, wiec szablon
# czatu MUSI pasowac -- uzywamy --jinja (natywny szablon z metadanych GGUF,
# identycznie jak rezydentny serwer :8877), NIE --chat-template chatml (dawalo
# to halucynowane dopiski w stylu <|im_end|>/kolejne fikcyjne tury -- Phi-4
# nie jest modelem ChatML). Zweryfikowane na binarce: --jinja daje czysta,
# poprawna odpowiedz; chatml -- smieci po pierwszym tokenie.
_DEFAULT_GGUF = r"E:\LOCAL LLM MODELS\Phi-4-mini\Phi-4-mini-instruct-Q4_K_M.gguf"
_DEFAULT_LLAMA_CLI = r"E:\LOCAL LLM MODELS\llama-runtime\llama-cli.exe"
_DEFAULT_CHAT_TEMPLATE = "jinja"

# v1.1: bylo na sztywno "90" (zadanie v1.0: timeout <= 90s). Live testy
# pokazaly ~130s na prompt z 12 kandydatami -> wieczna eskalacja. Teraz
# konfigurowalne przez env AIONS_PLANNER_TIMEOUT, default 240s.
_DEFAULT_TIMEOUT_S = "240"

_MAX_N_PREDICT = 300  # v1.1: bylo 200 -- ucinalo JSON przy 3-krokowych planach

_TOP_K_CANDIDATES = 6  # v1.1: bylo 12 -- krotszy prompt = szybsza generacja
_MAX_DESC_LEN = 80  # v1.1: opisy skilli w promptcie obciete do tylu znakow

# v2.0: system prompt po angielsku (Phi-4-mini, decyzja wlasciciela projektu).
# Semantyka bez zmian: wybor TYLKO z listy, JSON only, puste inputs {},
# zakaz wymyslania wartosci.
_SYSTEM_PROMPT = (
    'You are the AIONS planner. Choose 1-5 skills from the LIST below and '
    'put them in order. Reply with ONLY JSON: {"steps":[{"skill":"<id from '
    'list>","inputs":{}}],"why":"1 sentence"}. Do not invent skills outside '
    'the list. If a skill needs no inputs, give an empty object {}. Do NOT '
    'invent input values.'
)

# v1.1: rozszerzone o "gole" nazwy-placeholdery obserwowane live (bez < >),
# np. model wpisywal literalnie "remote_host" jako wartosc host_alias.
_PLACEHOLDER_TOKENS = {
    "todo", "tbd", "n/a", "none", "null", "placeholder", "...", "?", "xxx",
    "remote_host", "hostname", "host_name", "example",
}


def _ensure_env_defaults() -> None:
    """Uzupelnia braki w env TYLKO jesli nikt ich wczesniej nie ustawil
    (identyczna zasada jak w mouth.py -- nigdy nie nadpisujemy istniejacej
    konfiguracji). v1.1: AIONS_PLANNER_TIMEOUT pozwala nadpisac domyslny
    limit czasu planera (240s) bez zmiany kodu; wartosc jest przekladana na
    AIONS_MOUTH_TIMEOUT, ktory faktycznie czyta wrapper/generate.py."""
    if not os.environ.get("AIONS_GGUF_PATH") and Path(_DEFAULT_GGUF).is_file():
        os.environ["AIONS_GGUF_PATH"] = _DEFAULT_GGUF
    if not os.environ.get("AIONS_LLAMA_CLI") and Path(_DEFAULT_LLAMA_CLI).is_file():
        os.environ["AIONS_LLAMA_CLI"] = _DEFAULT_LLAMA_CLI
    os.environ.setdefault("AIONS_CHAT_TEMPLATE", _DEFAULT_CHAT_TEMPLATE)
    planner_timeout = os.environ.get("AIONS_PLANNER_TIMEOUT", _DEFAULT_TIMEOUT_S)
    os.environ.setdefault("AIONS_MOUTH_TIMEOUT", planner_timeout)


def _call_llm(system: str, user: str, n_predict: int = _MAX_N_PREDICT) -> dict:
    """Wola istniejacy mechanizm ust llama.cpp (wrapper/generate.py), z
    twardym firewallem: KAZDY problem (brak modulu, brak binarki/GGUF,
    tryb stub, timeout, wyjatek, pusta odpowiedz) konczy sie
    {"available": False, "reason": ...} -- nigdy wyjatkiem na zewnatrz."""
    try:
        n_predict = min(_MAX_N_PREDICT, int(n_predict))
        _ensure_env_defaults()

        runner_dir = str(_RUNNER_DIR)
        if runner_dir not in sys.path:
            sys.path.insert(0, runner_dir)

        try:
            from wrapper import generate as gguf_generate  # type: ignore
            from wrapper import config as gguf_config  # type: ignore
        except Exception as e:
            return {"available": False, "reason": f"import_failed: {e}"}

        try:
            mode = gguf_config.backend_mode()
        except Exception as e:
            return {"available": False, "reason": f"backend_mode_failed: {e}"}

        if mode != "real":
            return {"available": False, "reason": "backend_stub (brak llama-cli.exe lub GGUF)"}

        # v1.2: rezydentny llama-server pierwszy -- "result" ma identyczny
        # ksztalt jak zwrot gguf_generate.generate(), wiec cala walidacja
        # ponizej dziala bez zmian. Fallback do llama-cli przy KAZDYM
        # problemie (serwer wylaczony, timeout, blad polaczenia itp.).
        try:
            from ..llm import server_client  # type: ignore
            srv = server_client.generate_http(system, user, n_predict=n_predict, timeout=90.0)
        except Exception as e:
            srv = {"ok": False, "error": str(e)}

        if srv.get("ok"):
            result = {
                "ok": True,
                "content": srv.get("content", ""),
                "backend": "llamacpp",
                "mode": "real",
                "wall_s": srv.get("wall_s"),
            }
        else:
            try:
                result = gguf_generate.generate(system, user, kind="speak", n_predict=n_predict)
            except Exception as e:
                return {"available": False, "reason": f"generate_exception: {e}"}

        if not isinstance(result, dict) or not result.get("ok"):
            err = result.get("error") if isinstance(result, dict) else result
            return {"available": False, "reason": f"generate_not_ok: {err}"}

        # generate() moze po cichu spasc na deterministyczny stub (timeout,
        # brak binarki w trakcie itp.) -- to NIE jest realna odpowiedz modelu.
        if (
            result.get("mode") != "real"
            or result.get("backend") != "llamacpp"
            or result.get("fallback_from_real_error")
        ):
            return {
                "available": False,
                "reason": (
                    "fallback_to_stub "
                    f"(mode={result.get('mode')}, backend={result.get('backend')}, "
                    f"fallback_error={result.get('fallback_from_real_error')})"
                ),
            }

        content = (result.get("content") or "").strip()
        for marker in ("[end of text]", "[koniec tekstu]"):
            if content.lower().endswith(marker):
                content = content[: -len(marker)].rstrip()

        if not content:
            return {"available": False, "reason": "empty_response"}

        return {"available": True, "content": content, "wall_s": result.get("wall_s")}
    except Exception as e:  # pragma: no cover -- twardy firewall na wyjatki
        return {"available": False, "reason": f"unexpected_exception: {e}"}


def _extract_json(text: str) -> Optional[dict]:
    """Wyciaga pierwszy poprawny blok JSON (obiekt) z dowolnego tekstu,
    nawet jesli model dokleil komentarze/smieci przed lub po. Skanuje
    kazde wystapienie '{' i probuje dopasowac je do zamykajacego '}' przez
    liczenie nawiasow; pierwszy fragment ktory parsuje sie jako JSON obiekt
    wygrywa."""
    if not text:
        return None
    start = text.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(text)):
            ch = text[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start : i + 1]
                    try:
                        parsed = json.loads(candidate)
                    except json.JSONDecodeError:
                        break
                    if isinstance(parsed, dict):
                        return parsed
                    break
        start = text.find("{", start + 1)
    return None


def _looks_like_placeholder(v: Any) -> bool:
    """True jesli `v` wyglada na niewypelniony placeholder wygenerowany
    przez model (np. "<host_name>", "{value}", "TODO", "remote_host")
    zamiast prawdziwej wartosci. Takie wartosci sa gorsze niz brak wartosci
    -- skill ma wlasny, bezpieczny default (patrz DESIGN.md skilli:
    `host_alias` opcjonalny -> domyslnie "aions-node-1"), a halucynowany
    placeholder go nadpisuje i psuje wykonanie (zaobserwowane live: SSH
    "hostname contains invalid characters" dla host_alias="<host_name>").

    v1.1 (wniosek z testow v1.0): filtr lapal tylko wartosci opakowane w
    "<...>". Rozszerzony o:
      - dowolne wystapienie '<' lub '>' w srodku wartosci (nie tylko na
        brzegach),
      - dopasowanie tekstowe do znanych "golych" nazw-placeholderow (bez
        nawiasow), np. "remote_host", "hostname", "host_name", "example",
      - puste stringi (brak wartosci == placeholder, nie realna wartosc).
    """
    if not isinstance(v, str):
        return False
    s = v.strip()
    if not s:
        return True  # pusty string -> brak realnej wartosci
    if "<" in s or ">" in s:
        return True
    if s.startswith("{") and s.endswith("}"):
        return True
    if re.fullmatch(r"\[.*\]", s) and len(s) < 60:
        return True
    if s.lower() in _PLACEHOLDER_TOKENS:
        return True
    return False


def _truncate_desc(desc: Any, limit: int = _MAX_DESC_LEN) -> str:
    """Obcina opis skilla do `limit` znakow (v1.1: krotszy prompt -> szybsza
    generacja)."""
    d = desc.strip() if isinstance(desc, str) else str(desc or "")
    if len(d) <= limit:
        return d
    return d[: max(0, limit - 3)].rstrip() + "..."


def _candidate_text(cand_objs) -> str:
    """v1.1: opisy obciete do _MAX_DESC_LEN znakow, a w schemacie inputs
    pokazujemy modelowi TYLKO nazwy pol wymaganych (nie caly schemat z
    opcjonalnymi) -- krotszy prompt, mniej okazji do wymyslania wartosci
    dla pol ktorych i tak nie musi wypelniac."""
    lines = []
    for obj in cand_objs:
        required_names = [i.get("name") for i in (obj.inputs or []) if i.get("required")]
        inputs_desc = ", ".join(n for n in required_names if n) or "brak"
        lines.append(
            f"- {obj.id}: {_truncate_desc(obj.description)} | wymagane inputs: {inputs_desc}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# v2.1 -- CBMS-first cache PRZED wywolaniem LLM (Faza 3, KORZENIEC).
# ---------------------------------------------------------------------------
def _cbms_cache_enabled() -> bool:
    """Env AIONS_CBMS_CACHE, domyslnie ON. CLI --no-cbms (main()) ustawia te
    zmienna na "0" przed wywolaniem plan_goal/execute_goal."""
    val = os.environ.get("AIONS_CBMS_CACHE", "1")
    return str(val).strip().lower() not in ("0", "false", "off", "no")


def _log_cbms_decision(goal: str, decision: dict) -> None:
    """Best-effort append do runtime/state/cbms_planner_log.jsonl -- kazda
    decyzja CBMS-first cache'a dla PLANU (hit / miss / miss_plan_only_
    knowledge / error). Nigdy nie rzuca wyjatku na zewnatrz (identyczny
    firewall-styl jak _call_llm)."""
    try:
        _CBMS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        rec = {"ts": time.time(), "goal": goal, **decision}
        with open(_CBMS_LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass


def _steps_from_cbms_hit(retrieval: dict, registry) -> Optional[list]:
    """Probuje zbudowac WYKONYWALNY lancuch skilli z hitow CBMS (retrieval
    zwrocony przez cbms_gate.evaluate()).

    Uczciwa ocena: chunki CBMS sa w WIEKSZOSCI wiedza tekstowa (dokumentacja,
    opisy koncepcji), nie gotowymi planami skilli. Ten cache trafia
    realistycznie tylko gdy tresc hita zawiera:
      (a) osadzony JSON z polem "steps" (np. gdy jakas recipe zostala kiedys
          tez zaindeksowana jako chunk CBMS), lub
      (b) literalne ID skilli ktore istnieja w registry (np. dokumentacja
          wymieniajaca "linux.memory.info" po nazwie).
    Kazdy kandydujacy step przechodzi DOKLADNIE TA SAMA walidacje anty-
    -halucynacyjna co plan z LLM (skill musi byc w registry, inputs
    filtrowane do schematu skilla, wartosci-placeholdery odrzucane) -- zero
    skrotow w bezpieczenstwie tylko dlatego, ze zrodlem jest cache.

    Zwraca None (cache miss DLA PLANU) jesli zaden hit nie daje
    wykonywalnego lancucha -- nawet jesli CBMS mial wysoka confidence, bo
    wtedy to tylko WIEDZA, nie PLAN, i wywolawca (plan_goal) ma isc do LLM.
    """
    hits = retrieval.get("hits") or []
    for h in hits:
        blob = f"{h.get('concept') or ''}\n{h.get('text') or ''}"

        raw_steps = None
        parsed = _extract_json(blob)
        if isinstance(parsed, dict) and isinstance(parsed.get("steps"), list):
            raw_steps = parsed["steps"]

        if not raw_steps:
            found_ids = []
            for tok in re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z0-9_]+)+", blob):
                if tok not in found_ids and registry.get(tok) is not None:
                    found_ids.append(tok)
            if found_ids:
                raw_steps = [{"skill": sid, "inputs": {}} for sid in found_ids]

        if not raw_steps:
            continue

        valid_steps = []
        for step in raw_steps:
            if not isinstance(step, dict):
                continue
            skill_id = step.get("skill")
            if not isinstance(skill_id, str):
                continue
            obj = registry.get(skill_id)
            if obj is None:
                continue  # nie istnieje w registry -> odrzuc
            allowed_keys = {i.get("name") for i in (obj.inputs or [])}
            raw_inputs = step.get("inputs")
            inputs = {}
            if isinstance(raw_inputs, dict):
                for k, v in raw_inputs.items():
                    if k not in allowed_keys:
                        continue
                    if _looks_like_placeholder(v):
                        continue
                    inputs[k] = v
            valid_steps.append({"skill": skill_id, "inputs": inputs})

        if valid_steps:
            return valid_steps
    return None


def plan_goal(goal: str, registry, max_steps: int = 5) -> dict:
    """Zwraca plan dla `goal`:

    1. planner.plan(registry, goal) -- jesli trafia w istniejaca, zweryfikowana
       recipe (exact-match na intent), zwracamy jej kroki bez wolania LLM.
    2. v2.1 NOWE: cbms_gate.evaluate(goal) -- jesli gate ma HIT (confidence
       >= threshold) I da sie z hitu zbudowac WALIDNY, wykonywalny lancuch
       skilli (patrz _steps_from_cbms_hit), uzywamy go zamiast wolac LLM
       (source="cbms_cache"). Jesli hit jest tylko wiedza tekstowa bez
       wykonywalnego lancucha -- to nadal MISS dla PLANU, lecimy do LLM.
       Wylaczalne przez env AIONS_CBMS_CACHE=0 / CLI --no-cbms.
    3. Inaczej: retrieval registry.search(goal) -> top 6 kandydatow-skilli
       (v1.1: bylo 12, patrz _TOP_K_CANDIDATES).
    4. Maly LLM (Phi-4-mini) wybiera 1-5 skilli WYLACZNIE z listy kandydatow.
    5. Twarda walidacja anty-halucynacyjna: kazdy step.skill musi istniec w
       registry ORAZ byc w liscie kandydatow; inputs sa filtrowane do kluczy
       zdefiniowanych w schemacie skilla, a wartosci-placeholdery (np.
       "<host_name>", "remote_host") sa odrzucane (patrz _looks_like_placeholder).
       Nieznane skille sa odrzucane. 0 poprawnych krokow ->
       {"status": "escalate", ...}.
    6. Sukces -> {"status": "planned", "steps": [...], "source": "llm_compose", "why": ...}.

    Kazdy zwrocony slownik ma pole "cache": {"checked": bool, "hit": bool,
    "confidence": float, "source": "cbms_cache"|"llm_compose"|"recipe"|None}
    opisujace co sie stalo z CBMS-first cache dla TEGO wywolania.
    """
    cache_info: dict = {"checked": False, "hit": False, "confidence": 0.0, "source": None}

    plan_result = planner.plan(registry, goal)
    if plan_result.get("source") == "recipe" and plan_result.get("steps"):
        cache_info["source"] = "recipe"
        return {
            "status": "planned",
            "steps": plan_result["steps"],
            "source": "recipe",
            "why": "recipe replay (exact intent match)",
            "cache": cache_info,
        }

    # --- BRIDGE: semantyczne dopasowanie recipe (parafraza) PRZED CBMS/LLM
    # Reuzywa _steps_from_cbms_hit -> TA SAMA walidacja anty-halucynacyjna.
    if os.environ.get("AIONS_RECIPE_SEMANTIC", "1") != "0":
        try:
            sem = recipes.find_recipe_semantic(goal)
            if sem and sem.get("steps"):
                _fake = {"hits": [{"concept": "", "text": json.dumps({"steps": sem["steps"]}, ensure_ascii=False)}]}
                _sem_steps = _steps_from_cbms_hit(_fake, registry)
                if _sem_steps:
                    cache_info["checked"] = True
                    cache_info["hit"] = True
                    cache_info["confidence"] = float(sem.get("score") or 0.0)
                    cache_info["source"] = "recipe_semantic"
                    return {
                        "status": "planned",
                        "steps": _sem_steps,
                        "source": "recipe_semantic",
                        "why": "recipe semantic match score=%.2f intent='%s'" % (float(sem.get("score") or 0.0), sem.get("intent") or ""),
                        "cache": cache_info,
                    }
        except Exception:
            pass

    # --- v2.1: CBMS-first cache PRZED wywolaniem LLM --------------------
    if _cbms_cache_enabled():
        cache_info["checked"] = True
        try:
            from .. import cbms_gate  # type: ignore

            retrieval = cbms_gate.evaluate(goal)
            thr = cbms_gate.confidence_threshold()
            conf = float(retrieval.get("confidence") or 0.0)
            cache_info["confidence"] = conf
            gate_hit = bool(retrieval.get("hit"))

            if gate_hit:
                cbms_steps = _steps_from_cbms_hit(retrieval, registry)
                if cbms_steps:
                    cache_info["hit"] = True
                    cache_info["source"] = "cbms_cache"
                    _log_cbms_decision(goal, {
                        "decision": "hit",
                        "confidence": conf,
                        "threshold": thr,
                        "n_steps": len(cbms_steps),
                    })
                    return {
                        "status": "planned",
                        "steps": cbms_steps,
                        "source": "cbms_cache",
                        "why": "cbms gate hit: reused validated skill chain from CBMS memory (no LLM call)",
                        "cache": cache_info,
                    }
                _log_cbms_decision(goal, {
                    "decision": "miss_plan_only_knowledge",
                    "confidence": conf,
                    "threshold": thr,
                    "reason": "cbms_hit_is_textual_knowledge_without_executable_chain",
                })
            else:
                _log_cbms_decision(goal, {
                    "decision": "miss",
                    "confidence": conf,
                    "threshold": thr,
                    "reason": retrieval.get("reason"),
                })
        except Exception as e:
            # firewall: cache PRZED LLM nigdy nie blokuje sciezki do LLM.
            _log_cbms_decision(goal, {"decision": "error", "error": str(e)})
    # --- koniec CBMS-first cache; cache_info["hit"] == False -> idziemy do LLM

    candidates = registry.search(goal, top_k=_TOP_K_CANDIDATES, types=("skill",))
    if not candidates:
        return {"status": "escalate", "reason": "no_candidates", "steps": [], "cache": cache_info}

    cand_objs = [o for o in (registry.get(c["id"]) for c in candidates) if o is not None]
    if not cand_objs:
        return {"status": "escalate", "reason": "no_candidates", "steps": [], "cache": cache_info}

    candidate_ids = {obj.id for obj in cand_objs}
    user_prompt = f"Goal: {goal}\n\nCandidate list:\n{_candidate_text(cand_objs)}"

    llm = _call_llm(_SYSTEM_PROMPT, user_prompt, n_predict=_MAX_N_PREDICT)
    if not llm.get("available"):
        return {
            "status": "escalate",
            "reason": "llm_unavailable",
            "detail": llm.get("reason"),
            "steps": [],
            "cache": cache_info,
        }

    raw_content = llm["content"]
    parsed = _extract_json(raw_content)
    if parsed is None:
        return {
            "status": "escalate",
            "reason": "llm_parse_failed",
            "raw_llm": raw_content,
            "steps": [],
            "cache": cache_info,
        }

    valid_steps = []
    raw_steps = parsed.get("steps")
    if isinstance(raw_steps, list):
        for step in raw_steps[:max_steps]:
            if not isinstance(step, dict):
                continue
            skill_id = step.get("skill")
            if not isinstance(skill_id, str) or skill_id not in candidate_ids:
                continue  # nie ma w liscie kandydatow -> halucynacja, odrzuc
            obj = registry.get(skill_id)
            if obj is None:
                continue  # nie istnieje w registry -> odrzuc
            allowed_keys = {i.get("name") for i in (obj.inputs or [])}
            raw_inputs = step.get("inputs")
            inputs = {}
            if isinstance(raw_inputs, dict):
                for k, v in raw_inputs.items():
                    if k not in allowed_keys:
                        continue  # klucz spoza schematu -> odrzuc
                    if _looks_like_placeholder(v):
                        continue  # halucynowany placeholder -> pomin, niech dziala default skilla
                    inputs[k] = v
            valid_steps.append({"skill": skill_id, "inputs": inputs})

    if not valid_steps:
        return {
            "status": "escalate",
            "reason": "no_valid_steps_after_validation",
            "raw_llm": raw_content,
            "steps": [],
            "cache": cache_info,
        }

    why = parsed.get("why")
    cache_info["source"] = "llm_compose"
    return {
        "status": "planned",
        "steps": valid_steps,
        "source": "llm_compose",
        "why": why if isinstance(why, str) else "",
        "raw_llm": raw_content,
        "cache": cache_info,
    }


def _step_explicit_ok_false(step_result: dict) -> bool:
    """True jesli krok wykonal sie bez wyjatku (executor go oznaczyl jako
    status=="ok"), ale handler JAWNIE zwrocil {"ok": False, ...} w outputs.

    v1.1 GUARD OK-FALSE (krytyczny wniosek z testow v1.0): run_chain patrzy
    tylko na to, czy handler rzucil wyjatek -- nie na semantyczna trese
    outputs. Handler ktory po cichu sygnalizuje porazke zwracajac slownik z
    "ok": False (zamiast rzucic wyjatek) przechodzil wiec niezauwazony, a
    chain_result["verified"] wychodzilo True, wiec wadliwa recipe zapisywala
    sie jako "zweryfikowana". Liczy sie TYLKO jawne outputs["ok"] is False --
    skille ktore w ogole nie zwracaja klucza "ok" (wiekszosc) nie sa tym
    dotkniete.
    """
    outputs = step_result.get("outputs")
    return isinstance(outputs, dict) and outputs.get("ok") is False


def execute_goal(goal: str, registry, ctx: dict, learn: bool = True) -> dict:
    """plan_goal(goal) -> jesli planned: run_chain (przez bramke ryzyka) ->
    jesli verified i learn: recipes.save_recipe(goal, steps).

    v1.1: przed decyzja o zapisie recipe sprawdzamy outputs KAZDEGO kroku
    pod katem jawnego {"ok": False} (patrz _step_explicit_ok_false). Jesli
    ktorykolwiek krok tak zglasza porazke, status calosci to zawsze
    "failed", recipe NIE zapisuje sie (nawet jesli run_chain zwrocil
    verified=True), a szczegoly trafiaja do wyniku jako "failed_steps".

    v2.1: plan_result (zwrocony przez plan_goal) niesie teraz pole "cache" --
    execute_goal go nie modyfikuje, tylko przekazuje dalej w kluczu "plan"
    (result["plan"]["cache"]), zeby wywolawca widzial czy/jak trafil cache
    PRZED ewentualnym wykonaniem.

    Zwraca {"status": done|failed|escalate|approval_required,
             "plan": <wynik plan_goal>, "steps_results": [...],
             "recipe_saved": bool, "failed_steps": [...] (obecne tylko gdy
             > 0 krokow zglosilo jawne ok=False)}.
    """
    plan_result = plan_goal(goal, registry)
    if plan_result.get("status") != "planned":
        return {
            "status": plan_result.get("status", "escalate"),
            "plan": plan_result,
            "steps_results": [],
            "recipe_saved": False,
        }

    chain_result = executor.run_chain(registry, plan_result["steps"], ctx)
    steps_results = chain_result["steps"]

    failed_steps = [
        {"skill": r.get("skill"), "outputs": r.get("outputs")}
        for r in steps_results
        if _step_explicit_ok_false(r)
    ]

    recipe_saved = False
    if failed_steps:
        # v1.1 GUARD OK-FALSE: jawna porazka w outputs bije run_chain['verified'].
        status = "failed"
    elif chain_result["verified"]:
        status = "done"
        if learn:
            recipes.save_recipe(goal, plan_result["steps"], why=[plan_result.get("why", "")])
            recipe_saved = True
    elif any(r.get("status") == "approval_required" for r in steps_results):
        status = "approval_required"
    else:
        status = "failed"

    result = {
        "status": status,
        "plan": plan_result,
        "steps_results": steps_results,
        "recipe_saved": recipe_saved,
    }
    if failed_steps:
        result["failed_steps"] = failed_steps
    return result


def _build_registry():
    from . import registry as registry_mod

    reg = registry_mod.SkillRegistry()
    reg.discover()
    return reg


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python -m control_plane.skills.goal_planner",
        description="Jadro decyzyjne AIONS -- goal-planner z malym LLM w petli.",
    )
    parser.add_argument("goal", help="Cel po polsku, np. 'sprawdz ile pamieci ma nod linux'")
    parser.add_argument(
        "--dry-run", action="store_true", help="Tylko plan (plan_goal), bez wykonania."
    )
    parser.add_argument(
        "--no-learn", action="store_true", help="Nie zapisuj zweryfikowanej recipe."
    )
    parser.add_argument(
        "--no-cbms", action="store_true",
        help="Wylacz CBMS-first cache przed wolaniem LLM (ustawia AIONS_CBMS_CACHE=0).",
    )
    args = parser.parse_args()

    if args.no_cbms:
        os.environ["AIONS_CBMS_CACHE"] = "0"

    reg = _build_registry()

    if args.dry_run:
        result: Any = plan_goal(args.goal, reg)
    else:
        ctx = {"bag": {}}
        result = execute_goal(args.goal, reg, ctx, learn=not args.no_learn)

    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if result.get("status") in ("planned", "done") else 1


if __name__ == "__main__":
    sys.exit(main())
