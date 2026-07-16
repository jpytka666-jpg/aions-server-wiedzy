"""HTTP klient do rezydentnego llama-server (Phi-4-mini, CPU-only).

Serwer jest uruchamiany osobno (runtime/llama_server_run.cmd, zadanie
harmonogramu "AIONS_LLM_Server") i trzyma model w RAM na stale -- brak
kosztu zaladowania modelu od zera przy kazdym wywolaniu (jak w
wrapper/generate.py::_run_llama_cli, ktory spawnuje llama-cli.exe per
wywolanie).

v2.0 (Phi-4-mini): klient jest teraz MODEL-AGNOSTYCZNY. Zamiast recznie
budowac prompt w formacie ChatML (co dzialalo dla Bielika, ale NIE pasuje
do natywnego szablonu czatu Phi-4-mini), wolamy standardowy endpoint OpenAI
/v1/chat/completions z lista messages -- llama-server (uruchomiony z flaga
--jinja) sam aplikuje szablon czatu zapisany w GGUF-ie danego modelu. Zmiana
modelu (np. powrot do innego backendu) nie wymaga juz zmian w tym pliku.

generate_http() nigdy nie rzuca wyjatku na zewnatrz -- kazdy problem
(serwer wylaczony, timeout, zly JSON, polaczenie odrzucone) konczy sie
zwrotem {"ok": False, ...}, tak aby wolajacy mogl bez ryzyka fallbackowac
do dotychczasowej sciezki llama-cli.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

# Musi byc zgodny z --port w runtime/llama_server_run.cmd.
SERVER_URL = "http://127.0.0.1:8877"

# Tag modelu wysylany w polu "model" zadania -- llama-server ignoruje jego
# wartosc przy wyborze modelu (serwuje zawsze ten jeden zaladowany GGUF),
# pole jest wymagane tylko przez ksztalt OpenAI-kompatybilnego API.
MODEL_TAG = "phi-4-mini"


def generate_http(
    system: str,
    user: str,
    *,
    n_predict: int = 200,
    timeout: float = 90.0,
) -> dict[str, Any]:
    """POST /v1/chat/completions do rezydentnego llama-server.

    Szablon czatu (Phi natywny, nie ChatML) aplikuje serwer sam dzieki
    fladze --jinja -- tutaj przekazujemy tylko liste messages.

    Zwraca {"ok": True, "content": str, "wall_s": float, "mode": "server"}
    przy sukcesie, albo {"ok": False, "error": str, "mode": "server"} przy
    KAZDYM problemie (brak serwera, timeout, zly JSON) -- nigdy wyjatku.
    """
    t0 = time.time()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user or ""})

    payload = {
        "model": MODEL_TAG,
        "messages": messages,
        "max_tokens": int(n_predict),
        "temperature": 0.2,
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{SERVER_URL}/v1/chat/completions",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        body = json.loads(raw)
    except Exception as e:  # noqa: BLE001 -- twardy firewall, patrz docstring
        return {
            "ok": False,
            "error": f"{type(e).__name__}: {e}",
            "backend": "llama-server",
            "mode": "server",
            "wall_s": round(time.time() - t0, 2),
        }

    wall = round(time.time() - t0, 2)
    try:
        choices = body.get("choices") or []
        content = (choices[0].get("message", {}).get("content") or "").strip()
    except Exception as e:  # noqa: BLE001 -- niespodziewany ksztalt odpowiedzi
        return {
            "ok": False,
            "error": f"bad_response_shape: {type(e).__name__}: {e} | body={body!r}"[:300],
            "backend": "llama-server",
            "mode": "server",
            "wall_s": wall,
        }

    if not content:
        return {
            "ok": False,
            "error": f"empty_response: {body!r}"[:300],
            "backend": "llama-server",
            "mode": "server",
            "wall_s": wall,
        }
    return {
        "ok": True,
        "content": content,
        "backend": "llama-server",
        "mode": "server",
        "wall_s": wall,
    }


def health(timeout: float = 3.0) -> bool:
    """Szybki health-check /health -- True jesli serwer odpowiada 200."""
    try:
        req = urllib.request.Request(f"{SERVER_URL}/health", method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False
