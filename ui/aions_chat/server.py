"""AIONS Chat -- lokalny serwer HTTP (biblioteka standardowa, zero zaleznosci).

Bind TYLKO 127.0.0.1:8770. Serwuje index.html pod "/" oraz obsluguje
POST /api/chat z JSON {"message": "..."} -> {"reply": "...", "data": {...}}.

Ten plik TYLKO CZYTA/IMPORTUJE istniejacy system AIONS (control_plane.skills).
Nie modyfikuje zadnych plikow AIONS. To samodzielny, dodatkowy modul UI.
"""
from __future__ import annotations

import json
import re
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8771
HERE = Path(__file__).resolve().parent
INDEX_HTML = HERE / "index.html"

AIONS_ROOT = r"E:\server wiedzy"
if AIONS_ROOT not in sys.path:
    sys.path.insert(0, AIONS_ROOT)

# --- Integracja z AIONS: tylko import, zero modyfikacji istniejacych plikow ---
AIONS_IMPORT_ERROR = None
try:
    from control_plane.skills.registry import SkillRegistry
    from control_plane.skills import executor, planner, papiery, forge  # noqa: F401
    from control_plane.skills.context import build_context
except Exception as e:  # pragma: no cover - brak AIONS to nadal poprawny stan (fallback komunikat)
    SkillRegistry = None
    executor = planner = papiery = forge = None
    build_context = None
    AIONS_IMPORT_ERROR = f"{type(e).__name__}: {e}"

# Ryzykowne skille -- NIGDY nie wykonuj automatycznie
RISKY_IDS = {"file.delete", "proc.kill", "sys.lock", "sys.empty_temp", "app.close"}

reg = None
REG_INFO = {"loaded": 0, "errors": []}
if SkillRegistry is not None:
    try:
        reg = SkillRegistry()
        REG_INFO = reg.discover()
    except Exception as e:
        REG_INFO = {"loaded": 0, "errors": [f"{type(e).__name__}: {e}"]}
        reg = None

# Auto-odswiezanie rejestru: nowe bloki (np. z forge) pojawiaja sie bez restartu.
_LAST_DISCOVER = [0.0]


def _refresh_reg():
    global REG_INFO
    if reg is None:
        return
    if time.time() - _LAST_DISCOVER[0] > 5:
        try:
            REG_INFO = reg.discover()
            _LAST_DISCOVER[0] = time.time()
        except Exception:
            pass


# Prosty stan w pamieci procesu -- oczekujaca ryzykowna akcja (jeden uzytkownik, jedna sesja)
PENDING = {"skill_id": None, "inputs": None, "label": None}
PENDING_LOCK = threading.Lock()

ADD_TRIGGERS = ("dodaj", "zapamietaj", "zapamiętaj", "papier")
LAST_GAP = {"desc": None}


def _extract_inputs(skill_id, msg):
    """Wyciaga proste parametry z wiadomosci (np. litera dysku, tekst zapytania)."""
    inputs = {}
    m = re.search(r"\b([A-Za-z]):", msg or "")
    if skill_id == "sys.free_space" and m:
        inputs["drive"] = m.group(1).upper() + ":\\"
    if skill_id in ("web.search", "web.open_maps", "paper.find", "web.weather"):
        inputs["query"] = msg
    return inputs


def _run(skill_id, inputs):
    ctx = build_context()
    return executor.run_skill(reg, skill_id, inputs, ctx)


def _fmt_outputs(outputs):
    if not outputs:
        return "wykonano."
    parts = [f"{k}: {v}" for k, v in outputs.items() if k != "ok"]
    return ", ".join(parts) if parts else "wykonano."


def _fmt_papers(items, empty_msg):
    if not items:
        return empty_msg
    lines = []
    for p in items[:15]:
        deadline = f" (termin: {p['deadline']})" if p.get("deadline") else ""
        lines.append(f"- {p['title']}{deadline} [id: {p['id']}]")
    return f"Masz {len(items)} spraw:\n" + "\n".join(lines)


def handle_message(message: str) -> dict:
    """Prosty router po polsku. Zwraca {"reply": str, "data": {...}}."""
    global PENDING
    msg = (message or "").strip()
    low = msg.lower()

    if not msg:
        return {"reply": "Napisz cos, to odpowiem.", "data": {}}

    _refresh_reg()

    # --- Potwierdzenie oczekujacej ryzykownej akcji ---
    if low in ("potwierdzam", "tak, potwierdzam", "potwierdz", "potwierdź"):
        with PENDING_LOCK:
            pending_skill = PENDING["skill_id"]
            pending_inputs = PENDING["inputs"] or {}
            PENDING = {"skill_id": None, "inputs": None, "label": None}
        if not pending_skill:
            return {"reply": "Nie mam zadnej oczekujacej akcji do potwierdzenia.", "data": {}}
        if reg is None:
            return {"reply": "Rejestr skilli AIONS nie jest zaladowany, nie moge wykonac.", "data": {}}
        res = _run(pending_skill, pending_inputs)
        if res["status"] == "ok":
            return {"reply": f"Wykonano ({pending_skill}): {_fmt_outputs(res['outputs'])}", "data": res}
        return {"reply": f"Nie udalo sie wykonac {pending_skill}: {res.get('error')}", "data": res}

    # --- Zamowienie nowego bloku (forge): 'zamow nowy' po napotkaniu luki ---
    if forge is not None and any(low.startswith(t) for t in ("zamow", "zamów")):
        if LAST_GAP.get("desc"):
            desc = LAST_GAP["desc"]
            LAST_GAP["desc"] = None
            req = forge.request_skill(forge._slug(desc), desc, why="z czatu AIONS")
            return {"reply": f"Zamowilem nowy blok: {req['name']}. Trafil do kolejki -- Claude go zbuduje, sprawdzi i doda. Bez Ciebie.", "data": {"request": req}}
        return {"reply": "Nie ma czego zamowic. Najpierw popros o cos, czego nie umiem, potem napisz 'zamow nowy'.", "data": {}}

    if reg is None:
        return {
            "reply": f"Rejestr skilli AIONS jest niedostepny ({AIONS_IMPORT_ERROR}). Sprawdz sciezke E:\\server wiedzy.",
            "data": {},
        }

    # --- a) Komendy papierow (kolejnosc ma znaczenie: 'zrobione' zanim 'papier'->add) ---
    if any(w in low for w in ("zrobione", "odhacz")):
        return {"reply": "Podaj id sprawy, zeby ja odhaczyc (np. 'zrobione paper_xxxxxxxx').", "data": {}}

    if any(w in low for w in ("co mam", "do zrobienia", "lista")):
        res = _run("paper.list", {})
        if res["status"] == "ok":
            return {"reply": _fmt_papers(res["outputs"].get("papers", []), "Nie masz zadnych otwartych spraw."), "data": res}
        return {"reply": f"Blad przy paper.list: {res.get('error')}", "data": res}

    if any(w in low for w in ("pilne", "termin")):
        res = _run("paper.due", {"days": 7})
        if res["status"] == "ok":
            return {"reply": _fmt_papers(res["outputs"].get("due", []), "Nic pilnego w najblizszych 7 dniach."), "data": res}
        return {"reply": f"Blad przy paper.due: {res.get('error')}", "data": res}

    if any(t in low for t in ADD_TRIGGERS):
        title = msg
        for t in ADD_TRIGGERS:
            title = re.sub(re.escape(t), "", title, count=1, flags=re.IGNORECASE)
        title = title.strip(" :,.-") or msg
        res = _run("paper.add", {"title": title})
        if res["status"] == "ok":
            o = res["outputs"]
            return {"reply": f"Zapisalem: '{o.get('title')}' (id: {o.get('id')}).", "data": res}
        return {"reply": f"Nie udalo sie zapisac: {res.get('error')}", "data": res}

    # --- b) Ogolne wyszukiwanie w rejestrze skilli ---
    hits = reg.search(msg, top_k=3)
    best = hits[0] if hits else None
    obj = reg.get(best["id"]) if best else None

    # Luka (brak dopasowania albo slabe) -> zapamietaj i zaproponuj zamowienie
    if obj is None or best["score"] < 2:
        LAST_GAP["desc"] = msg
        return {"reply": "Nie mam jeszcze takiego bloku. Napisz 'zamow nowy', a AIONS zamowi go u Claude (zbuduje, sprawdzi i doda -- bez Ciebie).", "data": {"hits": hits}}

    if obj.risk in ("medium", "high") or obj.id in RISKY_IDS:
        with PENDING_LOCK:
            PENDING = {"skill_id": obj.id, "inputs": _extract_inputs(obj.id, msg), "label": obj.name}
        return {"reply": f"To akcja ryzykowna ({obj.id}). Napisz 'potwierdzam' zeby wykonac.", "data": {"hits": hits, "pending": obj.id}}

    res = _run(obj.id, _extract_inputs(obj.id, msg))
    if res["status"] == "ok":
        return {"reply": f"{obj.name}: {_fmt_outputs(res['outputs'])}", "data": res}
    if res["status"] == "skipped":
        return {"reply": f"Pomijam ({obj.id}): {res.get('error')}", "data": res}
    return {"reply": f"Blad przy {obj.id}: {res.get('error')}", "data": res}


class Handler(BaseHTTPRequestHandler):
    server_version = "AIONSChat/1.0"

    def log_message(self, fmt, *args):  # ciche logi w konsoli, ale bez zaszumiania
        print("[http]", self.address_string(), fmt % args)

    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            try:
                data = INDEX_HTML.read_bytes()
            except Exception as e:
                self._send_json({"error": f"Brak index.html: {e}"}, status=500)
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if self.path == "/api/health":
            self._send_json({"ok": True, "skills_loaded": REG_INFO.get("loaded", 0)})
            return
        self._send_json({"error": "not found"}, status=404)

    def do_POST(self):
        if self.path != "/api/chat":
            self._send_json({"error": "not found"}, status=404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(length) if length > 0 else b"{}"
            payload = json.loads(raw.decode("utf-8") or "{}")
            message = payload.get("message", "")
            result = handle_message(message)
            self._send_json(result, status=200)
        except Exception as e:
            traceback.print_exc()
            self._send_json({"reply": f"Blad serwera: {e}", "data": {}}, status=200)


def _open_ui():
    url = f"http://{HOST}:{PORT}/"
    try:
        import webview  # opcjonalne -- uzywane TYLKO jesli juz jest w venv
    except Exception:
        import webbrowser

        webbrowser.open(url)
        return False
    window = webview.create_window("AIONS Chat", url, width=960, height=720, min_size=(480, 400))
    webview.start()
    return True


def main():
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"[AIONS Chat] serwer: http://{HOST}:{PORT}  (skille zaladowane: {REG_INFO.get('loaded', 0)}, "
          f"bledy: {len(REG_INFO.get('errors', []))})")
    if AIONS_IMPORT_ERROR:
        print(f"[AIONS Chat] UWAGA: import control_plane nie powiodl sie: {AIONS_IMPORT_ERROR}")

    try:
        import webview  # noqa: F401
        have_webview = True
    except Exception:
        have_webview = False

    if have_webview:
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        try:
            _open_ui()
        finally:
            httpd.shutdown()
    else:
        import webbrowser

        webbrowser.open(f"http://{HOST}:{PORT}/")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            httpd.shutdown()


if __name__ == "__main__":
    main()
