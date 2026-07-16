"""
Full-system scan orchestrator — all drives, background-friendly.

Phase 1: Everything CSV inventory per drive (complete file map)
Phase 2: turbo_scanner per drive (code graph, deps, duplicates)
Phase 3: project-root detection + master_map.json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
TURBO = SCRIPTS / "turbo_scanner.py"
PYTHON = REPO_ROOT / "venv" / "Scripts" / "python.exe"
EVERYTHING = Path(r"C:\Program Files\Everything\es.exe")
LOGS = REPO_ROOT / "logs"
SCAN_ROOT = REPO_ROOT / "scan_results"
DEFAULT_EXCLUDED_DRIVES = {
    "F": "backing/home volume for Dev Drive D:\\",
}

PROJECT_MARKERS = {
    ".git", "pyproject.toml", "package.json", "Cargo.toml", "go.mod",
    "pom.xml", "build.gradle", "CMakeLists.txt", "requirements.txt",
    "setup.py", "mcp.json", "docker-compose.yml", "docker-compose.yaml",
}

SYSTEM_SKIP_PARTS = (
    "\\windows\\winsxs\\",
    "\\windows\\system32\\",
    "\\windows\\servicing\\",
    "\\$recycle.bin\\",
    "\\system volume information\\",
    "\\pagefile.sys",
    "\\hiberfil.sys",
    "\\swapfile.sys",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_status(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = _now()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def get_ready_drives() -> List[str]:
    drives: List[str] = []
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        root = Path(f"{letter}:\\")
        try:
            if root.exists() and root.is_dir():
                drives.append(f"{letter}:\\")
        except OSError:
            pass
    return drives


def get_default_excluded_drives() -> Dict[str, str]:
    """Drives skipped only for implicit auto-detect runs."""
    return dict(DEFAULT_EXCLUDED_DRIVES)


def resolve_drive_order(requested: List[str] | None) -> List[str]:
    """Return drives in requested order, skipping missing/unavailable letters."""
    if not requested:
        excluded = set(get_default_excluded_drives())
        return [drive for drive in get_ready_drives() if drive[0].upper() not in excluded]
    ready = {d[0].upper() for d in get_ready_drives()}
    ordered: List[str] = []
    for item in requested:
        letter = item.strip().rstrip(":\\").upper()
        if not letter or len(letter) != 1:
            continue
        if letter not in ready:
            continue
        drive = f"{letter}:\\"
        if drive not in ordered:
            ordered.append(drive)
    return ordered


def export_drive_inventory(drive: str, out_csv: Path, log: Path) -> int:
    """Everything full export for one drive root."""
    prefix = drive if drive.endswith("\\") else drive + "\\"
    query = f"{prefix}*"
    cmd = [str(EVERYTHING), "-export-csv", str(out_csv), query]
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"\n[{_now()}] INVENTORY {drive} query={query}\n")
        result = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3600
        )
        f.write(result.stdout[-2000:] if result.stdout else "")
        if result.stderr:
            f.write(result.stderr[-2000:])
        f.write(f"\nexit={result.returncode}\n")
    if not out_csv.exists():
        return 0
    # Count lines minus header
    try:
        with open(out_csv, "r", encoding="utf-8", errors="replace") as f:
            return max(0, sum(1 for _ in f) - 1)
    except OSError:
        return 0


def run_turbo_drive(drive: str, output_dir: Path, log: Path) -> Dict[str, Any]:
    cmd = [str(PYTHON), str(TURBO), drive, "-o", str(output_dir)]
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"\n[{_now()}] TURBO {drive}\n")
        proc = subprocess.run(
            cmd, stdout=f, stderr=subprocess.STDOUT, cwd=str(REPO_ROOT), timeout=86400
        )
        f.write(f"\n[{_now()}] TURBO {drive} exit={proc.returncode}\n")
    scans = sorted([d for d in output_dir.iterdir() if d.is_dir()], reverse=True)
    if not scans:
        return {"drive": drive, "status": "error", "exit_code": proc.returncode}
    summary_path = scans[0] / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    return {"drive": drive, "status": "ok" if proc.returncode == 0 else "error", "scan_id": scans[0].name, **summary}


def detect_project_roots(inventory_csv: Path, max_roots: int = 500) -> List[Dict[str, Any]]:
    """Find project roots from inventory paths."""
    if not inventory_csv.exists():
        return []
    roots: Dict[str, Dict[str, Any]] = {}
    marker_hits: Dict[str, Set[str]] = defaultdict(set)

    with open(inventory_csv, "r", encoding="utf-8", errors="replace") as f:
        header = f.readline()
        for line in f:
            if not line.strip():
                continue
            # CSV: Name,Path,... or Path in second column
            parts = line.split(",")
            if len(parts) < 2:
                continue
            path = parts[1].strip('"').replace("\\", "/")
            name = Path(path).name.lower()
            for marker in PROJECT_MARKERS:
                if name == marker.lower() or path.lower().endswith("/" + marker.lower()):
                    if any(skip in path.lower().replace("/", "\\") for skip in SYSTEM_SKIP_PARTS):
                        continue
                    root = str(Path(path).parent) if name != marker.lower() else path
                    if marker == ".git":
                        root = str(Path(path).parent)
                    marker_hits[root].add(marker)

    for root, markers in marker_hits.items():
        roots[root] = {
            "path": root,
            "markers": sorted(markers),
            "score": len(markers),
        }

    ranked = sorted(roots.values(), key=lambda x: (-x["score"], x["path"]))
    return ranked[:max_roots]


def build_master_map(campaign_dir: Path, drives: List[str], drive_results: List[Dict[str, Any]]) -> Path:
    master: Dict[str, Any] = {
        "campaign_id": campaign_dir.name,
        "created_at": _now(),
        "drives": drives,
        "drive_results": drive_results,
        "project_roots": [],
        "totals": {
            "inventory_files": 0,
            "code_files_scanned": 0,
            "project_roots": 0,
        },
    }

    for dr in drive_results:
        inv = dr.get("inventory_files", 0)
        master["totals"]["inventory_files"] += inv
        master["totals"]["code_files_scanned"] += dr.get("total_files", 0) or 0
        for pr in dr.get("project_roots", []):
            master["project_roots"].append({**pr, "drive": dr.get("drive")})

    master["totals"]["project_roots"] = len(master["project_roots"])
    master["project_roots"].sort(key=lambda x: (-x.get("score", 0), x.get("path", "")))

    out = campaign_dir / "master_map.json"
    out.write_text(json.dumps(master, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Full-system scan orchestrator")
    parser.add_argument(
        "--drives",
        default=None,
        help=(
            "Comma-separated drive letters in scan order (e.g. D,E,C or explicit D,E,F,C). "
            "When omitted, auto-detect skips special-case backing volumes such as F:."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    requested = [d.strip() for d in args.drives.split(",")] if args.drives else None
    drives = resolve_drive_order(requested)
    if not drives:
        print("No drives available to scan.", file=sys.stderr)
        return 1

    campaign_id = datetime.now().strftime("full_system_%Y%m%d_%H%M%S")
    campaign_dir = SCAN_ROOT / campaign_id
    campaign_dir.mkdir(parents=True, exist_ok=True)

    status_path = LOGS / "full_system_scan_status.json"
    log_path = LOGS / f"full_system_scan_{campaign_id}.log"

    status: Dict[str, Any] = {
        "campaign_id": campaign_id,
        "state": "running",
        "phase": "init",
        "drive_order": "→".join(drives),
        "drives": drives,
        "default_excluded_drives": get_default_excluded_drives(),
        "current_drive": None,
        "completed_drives": [],
        "started_at": _now(),
        "log_file": str(log_path),
        "campaign_dir": str(campaign_dir),
    }
    _write_status(status_path, status)

    drive_results: List[Dict[str, Any]] = []

    for i, drive in enumerate(drives, 1):
        status["phase"] = f"drive_{i}_of_{len(drives)}"
        status["current_drive"] = drive
        _write_status(status_path, status)

        drive_dir = campaign_dir / f"drive_{drive[0]}"
        drive_dir.mkdir(parents=True, exist_ok=True)

        inv_csv = drive_dir / "inventory_everything.csv"
        try:
            inv_count = export_drive_inventory(drive, inv_csv, log_path)
        except Exception as e:
            inv_count = 0
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"\n[{_now()}] INVENTORY ERROR {drive}: {e}\n")

        project_roots = detect_project_roots(inv_csv)

        turbo_result: Dict[str, Any] = {"drive": drive}
        try:
            turbo_result = run_turbo_drive(drive, drive_dir / "turbo", log_path)
        except Exception as e:
            turbo_result = {"drive": drive, "status": "error", "error": str(e)}
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"\n[{_now()}] TURBO ERROR {drive}: {e}\n")

        merged = {
            "drive": drive,
            "inventory_files": inv_count,
            "inventory_csv": str(inv_csv),
            "project_roots": project_roots,
            **turbo_result,
        }
        (drive_dir / "drive_summary.json").write_text(
            json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        drive_results.append(merged)
        status["completed_drives"].append(drive)
        _write_status(status_path, status)

    status["phase"] = "master_map"
    _write_status(status_path, status)
    master_path = build_master_map(campaign_dir, drives, drive_results)

    status["state"] = "completed"
    status["current_drive"] = None
    status["master_map"] = str(master_path)
    status["finished_at"] = _now()
    _write_status(status_path, status)

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n[{_now()}] COMPLETE campaign={campaign_id}\n")

    print(f"Full system scan complete: {campaign_id}")
    print(f"Master map: {master_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
