"""AIONS forge — Linux skill verify pipeline (A5: sandbox on VM before promote).

Called from forge.promote() when a forge candidate's id starts with "linux.".
Runs candidate against 4 checks (candidate_dir = skills_requests/built/<name>/):

  1. schema   — skill.json validates via schema.py, has `risk`, id startswith "linux."
  2. compile  — handler.py compiles (py_compile)
  3. sandbox  — risk == "low" (read-only): the handler is actually executed
                against the VM through SSHExecutor and must return a dict
                without raising. risk != "low": the handler is NEVER
                executed here; only a harmless "echo DRY_RUN: ..." is sent
                to the VM over SSH and the check is marked skipped_dry_run.
  4. log      — the verify result is written to the VM
                (/opt/aions/forge_sandbox/verify_<id>_<ts>.json via ssh+tee)
                and appended locally to runtime/state/forge_verify_log.jsonl.

verify_linux_skill(candidate_dir) -> {"passed": bool, "id": str, "ts": str,
                                        "risk": str|None, "checks": [...]}
"""
from __future__ import annotations

import datetime
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from . import schema

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PYEXE = REPO / "venv" / "Scripts" / "python.exe"
LOCAL_LOG = REPO / "runtime" / "state" / "forge_verify_log.jsonl"
VM_SANDBOX_DIR = "/opt/aions/forge_sandbox"
VM_HOST_ALIAS = "aions-node-1"


def _now_ts() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def _check_schema(candidate_dir: Path) -> dict:
    sj = candidate_dir / "skill.json"
    if not sj.exists():
        return {"name": "schema", "passed": False, "detail": "brak skill.json"}
    try:
        obj = schema.load(str(sj))
    except Exception as e:
        return {"name": "schema", "passed": False, "detail": f"load error: {e}"}
    errs = schema.validate(obj)
    if errs:
        return {"name": "schema", "passed": False, "detail": errs}
    if not getattr(obj, "risk", None):
        return {"name": "schema", "passed": False, "detail": "brak risk"}
    if not obj.id.startswith("linux."):
        return {"name": "schema", "passed": False,
                "detail": f"id nie zaczyna sie od 'linux.': {obj.id}"}
    return {"name": "schema", "passed": True, "detail": {"id": obj.id, "risk": obj.risk}}


def _check_compile(candidate_dir: Path) -> dict:
    hp = candidate_dir / "handler.py"
    if not hp.exists():
        return {"name": "compile", "passed": False, "detail": "brak handler.py"}
    try:
        r = subprocess.run([str(PYEXE), "-m", "py_compile", str(hp)],
                            capture_output=True, text=True, timeout=30)
    except Exception as e:
        return {"name": "compile", "passed": False, "detail": f"subprocess error: {e}"}
    if r.returncode != 0:
        return {"name": "compile", "passed": False, "detail": r.stderr.strip()[:300]}
    return {"name": "compile", "passed": True, "detail": "ok"}


def _load_handler_run(candidate_dir: Path):
    hp = candidate_dir / "handler.py"
    spec = importlib.util.spec_from_file_location("forge_candidate_handler", str(hp))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fn = getattr(mod, "run", None)
    if not callable(fn):
        raise RuntimeError("handler bez callable run()")
    return fn


def _check_sandbox(candidate_dir: Path, risk: str) -> dict:
    from runtime.transport.ssh_executor import SSHExecutor

    if risk == "low":
        try:
            fn = _load_handler_run(candidate_dir)
        except Exception as e:
            return {"name": "sandbox", "passed": False, "detail": f"handler load error: {e}"}
        try:
            result = fn({}, {})
        except Exception as e:
            return {"name": "sandbox", "passed": False, "detail": f"handler raised: {e}"}
        if not isinstance(result, dict):
            return {"name": "sandbox", "passed": False,
                    "detail": f"handler nie zwrocil dict (typ={type(result).__name__})"}
        return {"name": "sandbox", "passed": True,
                "detail": {"executed": "live_on_vm", "result": result}}

    # risk medium/high: never execute for real, only a dry-run echo on the VM
    ex = SSHExecutor(host_alias=VM_HOST_ALIAS)
    cmd = f"echo DRY_RUN: candidate={candidate_dir.name} risk={risk}"
    res = ex.run(cmd, timeout=15)
    ok = res.get("rc") == 0
    return {"name": "sandbox", "passed": ok, "status": "skipped_dry_run",
            "detail": {"stdout": (res.get("stdout") or "").strip(), "rc": res.get("rc")}}


def _write_vm_log(skill_id: str, ts: str, payload: dict) -> dict:
    from runtime.transport.ssh_executor import SSHExecutor

    ex = SSHExecutor(host_alias=VM_HOST_ALIAS)
    remote_path = f"{VM_SANDBOX_DIR}/verify_{skill_id}_{ts}.json"
    body = json.dumps(payload, ensure_ascii=False, indent=2)
    cmd = f"cat <<'AIONS_EOF' | tee {remote_path} >/dev/null\n{body}\nAIONS_EOF"
    res = ex.run(cmd, timeout=20)
    return {"remote_path": remote_path, "rc": res.get("rc"),
            "stderr": (res.get("stderr") or "")[:200]}


def _append_local_log(payload: dict) -> None:
    LOCAL_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOCAL_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def verify_linux_skill(candidate_dir) -> dict:
    """Verify a linux.* forge candidate. Runs 4 checks, returns the report.

    candidate_dir: skills_requests/built/<name>/ (skill.json + handler.py)
    """
    candidate_dir = Path(candidate_dir)
    ts = _now_ts()
    checks = []
    skill_id = candidate_dir.name
    risk = None

    c1 = _check_schema(candidate_dir)
    checks.append(c1)
    if c1["passed"]:
        skill_id = c1["detail"]["id"]
        risk = c1["detail"]["risk"]

    if c1["passed"]:
        c2 = _check_compile(candidate_dir)
    else:
        c2 = {"name": "compile", "passed": False, "detail": "skipped: schema check failed"}
    checks.append(c2)

    if c1["passed"] and c2["passed"]:
        c3 = _check_sandbox(candidate_dir, risk)
    else:
        c3 = {"name": "sandbox", "passed": False, "detail": "skipped: earlier check failed"}
    checks.append(c3)

    passed_so_far = all(c.get("passed") for c in checks)
    result = {"passed": passed_so_far, "id": skill_id, "ts": ts, "risk": risk, "checks": checks}

    vm_log = _write_vm_log(skill_id, ts, result)
    c4 = {"name": "log", "passed": vm_log.get("rc") == 0, "detail": vm_log}
    checks.append(c4)

    final_passed = passed_so_far and c4["passed"]
    result = {"passed": final_passed, "id": skill_id, "ts": ts, "risk": risk, "checks": checks}
    _append_local_log(result)
    return result
