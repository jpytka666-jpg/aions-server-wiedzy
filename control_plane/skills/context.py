"""AIONS Skill Engine — execution context.

The context is a whitelist of helpers skills may call. Skills never touch global
state directly; they go through ctx. Inside the MCP server, ctx can be built with
real backends (memory_store, browser, etc.) via the `extra` dict.
"""
from __future__ import annotations
import datetime
import json
import subprocess
from pathlib import Path

from . import world_state

from aions_core.lokalizacje import gdzie as _gdzie

REPO = Path(__file__).resolve().parents[2]
STATE = REPO / "runtime" / "state"
# 2026-08-16: adres z `config/lokalizacje.json` zamiast wpisanego na sztywno.
# `gdzie()` zwraca None, gdy programu nie ma — `_find_files` i tak to sprawdza
# i oddaje czytelny blad zamiast wybuchac.
EVERYTHING = _gdzie("everything_es") or Path("es.exe")


def _find_files(query, folder="", max_results=50):
    if not EVERYTHING.exists():
        return {"ok": False, "error": "Everything CLI not found", "files": []}
    cmd = [str(EVERYTHING), "-n", str(max_results)]
    if folder:
        cmd.append(str(folder).rstrip("\\/"))
    if query:
        cmd.append(query)
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        files = [ln for ln in out.stdout.strip().splitlines() if ln.strip()]
        return {"ok": True, "files": files}
    except Exception as e:
        return {"ok": False, "error": str(e), "files": []}


def _save_note(text, session="skill_engine"):
    STATE.mkdir(parents=True, exist_ok=True)
    p = STATE / "skill_notes.json"
    notes = []
    if p.exists():
        try:
            notes = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            notes = []
    notes.append({
        "ts": datetime.datetime.utcnow().isoformat() + "Z",
        "session": session,
        "text": text,
    })
    p.write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "note_id": len(notes), "path": str(p)}


def _launch_app(name, args=None):
    """Launch a Windows app detached so its window stays open."""
    try:
        p = subprocess.Popen([name] + (args or []),
                             creationflags=0x00000008, close_fds=True)
        return {"ok": True, "pid": p.pid}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _close_app(image):
    """Close an app by image name (e.g. 'notepad.exe')."""
    try:
        out = subprocess.run(["taskkill", "/IM", image, "/F"],
                             capture_output=True, text=True, timeout=10)
        return {"ok": out.returncode == 0, "stdout": out.stdout.strip()}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def build_context(extra=None):
    ctx = {
        "find_files": _find_files,
        "save_note": _save_note,
        "launch_app": _launch_app,
        "close_app": _close_app,
        "state_get": world_state.get,
        "state_set": world_state.set,
        "bag": {},
    }
    if extra:
        ctx.update(extra)
    return ctx
