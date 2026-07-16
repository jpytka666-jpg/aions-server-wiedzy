"""AIONS 'papiery' store — personal admin items as CBMS-style JSON blocks.

No external DB. Each item is one JSON block on disk (E:), human-readable, greppable,
backup-able. Same philosophy as CBMS: everything is a block.
"""
from __future__ import annotations
import datetime
import glob
import hashlib
import json
import os

STORE = r"E:\AI_WORKSPACE\AIONS_workspace\papiery"


def _pid(title):
    seed = (title + datetime.datetime.now().isoformat()).encode("utf-8")
    return "paper_" + hashlib.sha1(seed).hexdigest()[:8]


def add(title, deadline="", note="", priority="normal", tags=None):
    os.makedirs(STORE, exist_ok=True)
    pid = _pid(title)
    obj = {
        "id": pid, "type": "paper", "title": title,
        "deadline": deadline, "note": note, "priority": priority,
        "status": "open", "tags": tags or [],
        "created": datetime.datetime.now().isoformat(),
    }
    with open(os.path.join(STORE, pid + ".json"), "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=2))
    return obj


def _all():
    out = []
    for fp in glob.glob(os.path.join(STORE, "*.json")):
        try:
            with open(fp, encoding="utf-8") as f:
                out.append(json.load(f))
        except Exception:
            pass
    return out


def list_open():
    items = [p for p in _all() if p.get("status") == "open"]
    prio = {"high": 0, "normal": 1, "low": 2}
    return sorted(items, key=lambda p: (p.get("deadline") or "9999-12-31", prio.get(p.get("priority"), 1)))


def due(days=7):
    today = datetime.date.today()
    soon = []
    for p in list_open():
        d = p.get("deadline")
        if d:
            try:
                if (datetime.date.fromisoformat(d) - today).days <= days:
                    soon.append(p)
            except Exception:
                pass
    return soon


def done(pid):
    fp = os.path.join(STORE, pid + ".json")
    if os.path.exists(fp):
        with open(fp, encoding="utf-8") as f:
            o = json.load(f)
        o["status"] = "done"
        o["done_at"] = datetime.datetime.now().isoformat()
        with open(fp, "w", encoding="utf-8") as f:
            f.write(json.dumps(o, ensure_ascii=False, indent=2))
        return o
    return None


def find(q):
    q = q.lower()
    return [p for p in _all()
            if q in (p.get("title", "") + " " + p.get("note", "") + " " + " ".join(p.get("tags", []))).lower()]
