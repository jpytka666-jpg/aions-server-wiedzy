"""AIONS forge — self-requesting new skill blocks (verify-before-trust).

Flow:
  1) AIONS hits a capability gap -> request_skill() writes a request to
     skills_requests/pending/<name>.json.
  2) The BIG model (Claude) writes the block code into
     skills_requests/built/<name>/ (skill.json + handler.py).
  3) promote() VERIFIES it (schema + py_compile + import run()) and only then
     copies it into skills_lib/. Unverified/local code never auto-runs.
     A5: candidates whose id starts with "linux." are instead verified
     through forge_linux_verify.verify_linux_skill(), which sandbox-tests
     the handler on the VM poligon (aions-node-1) before promotion.
"""
from __future__ import annotations
import datetime
import json
import re
import shutil
import subprocess
from pathlib import Path

from . import schema

REPO = Path(__file__).resolve().parents[2]
REQ = REPO / "skills_requests"
PENDING = REQ / "pending"
BUILT = REQ / "built"
DONE = REQ / "done"
FAILED = REQ / "failed"
SKILLS_LIB = REPO / "skills_lib"
PYEXE = REPO / "venv" / "Scripts" / "python.exe"


def _slug(text):
    s = re.sub(r"[^a-z0-9]+", "_", (text or "").lower()).strip("_")
    return ("auto." + s)[:40] if s else "auto.unnamed"


def _ensure():
    for d in (PENDING, BUILT, DONE, FAILED):
        d.mkdir(parents=True, exist_ok=True)


def request_skill(name, description, inputs=None, why="", requested_by="aions"):
    _ensure()
    obj = {
        "name": name, "type": "skill_request", "description": description,
        "inputs": inputs or [], "why": why, "requested_by": requested_by,
        "status": "requested", "created": datetime.datetime.now().isoformat(),
    }
    (PENDING / f"{name}.json").write_text(
        json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return obj


def list_requests(status="requested"):
    _ensure()
    folders = {"requested": [PENDING], "built": [BUILT], "done": [DONE], "failed": [FAILED]}
    dirs = folders.get(status, [PENDING, BUILT, DONE, FAILED])
    out = []
    for d in dirs:
        for fp in d.glob("*.json"):
            try:
                out.append(json.loads(fp.read_text(encoding="utf-8")))
            except Exception:
                pass
    return out


def gap_detect(registry, intent, min_score=2.0):
    hits = registry.search(intent, top_k=3)
    if hits and hits[0]["score"] >= min_score:
        return {"gap": False, "best": hits[0]}
    return {"gap": True, "suggested": {"name": _slug(intent), "description": intent}}


def plan_or_request(registry, intent, min_score=2.0):
    g = gap_detect(registry, intent, min_score)
    if not g["gap"]:
        return {"action": "have_skill", "best": g["best"]}
    req = request_skill(g["suggested"]["name"], g["suggested"]["description"], why=f"auto-gap: {intent}")
    return {"action": "requested", "request": req["name"]}


def _move_request(name, folder, status, errors=None):
    _ensure()
    p = PENDING / f"{name}.json"
    obj = {}
    if p.exists():
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            obj = {}
        p.unlink(missing_ok=True)
    obj["name"] = name
    obj["status"] = status
    if errors:
        obj["errors"] = errors
    (folder / f"{name}.json").write_text(
        json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def promote(name):
    """Verify a big-model-built block in built/<name>/ and copy to skills_lib."""
    _ensure()
    src = BUILT / name
    sj = src / "skill.json"
    hp = src / "handler.py"
    if not sj.exists() or not hp.exists():
        return {"ok": False, "error": f"brak skill.json/handler.py w {src}"}
    try:
        errs = schema.validate(schema.load(str(sj)))
    except Exception as e:
        errs = [f"load error: {e}"]
    if errs:
        _move_request(name, FAILED, "failed", errs)
        return {"ok": False, "errors": errs}

    if name.startswith("linux."):
        # A5: linux.* candidates go through the VM sandbox verify pipeline
        # (schema + compile + live/dry-run on aions-node-1 + audit log)
        # instead of the generic py_compile/import-run check below.
        from . import forge_linux_verify
        v = forge_linux_verify.verify_linux_skill(src)
        if not v.get("passed"):
            _move_request(name, FAILED, "failed", v.get("checks"))
            return {"ok": False, "error": "linux sandbox verify failed", "verify": v}
    else:
        r = subprocess.run([str(PYEXE), "-m", "py_compile", str(hp)],
                           capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            _move_request(name, FAILED, "failed", [r.stderr.strip()[:300]])
            return {"ok": False, "error": "py_compile failed", "detail": r.stderr.strip()[:300]}
        chk = ("import importlib.util; "
               f"spec=importlib.util.spec_from_file_location('h', r'{hp}'); "
               "m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); "
               "print('OK' if callable(getattr(m,'run',None)) else 'NORUN')")
        r2 = subprocess.run([str(PYEXE), "-c", chk], capture_output=True, text=True, timeout=30)
        if "OK" not in (r2.stdout or ""):
            _move_request(name, FAILED, "failed", ["handler bez callable run()", (r2.stderr or "").strip()[:200]])
            return {"ok": False, "error": "handler.run missing"}

    dest = SKILLS_LIB / name
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(src, dest)
    _move_request(name, DONE, "done")
    shutil.rmtree(src, ignore_errors=True)
    return {"ok": True, "promoted": name, "path": str(dest)}
