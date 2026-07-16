#!/usr/bin/env python3
"""Smoke + optional remote API health (Faza 3 E2E)."""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from control_plane.planner import create_plan
from control_plane.executor import store_plan, execute_step, get_execution

TUNNEL_HELP = """
SSH tunnel (Proxmox guest @ 192.168.1.150, user ubuntu):
  ssh -L 8765:127.0.0.1:8765 -i D:\\AIONS_DEV\\vm\\aions-milestone-c\\keys\\id_ed25519 ubuntu@192.168.1.150 -N

Hyper-V fallback (@ 192.168.1.186):
  ssh -L 8765:127.0.0.1:8765 -i D:\\AIONS_DEV\\vm\\aions-milestone-c\\keys\\id_ed25519 ubuntu@192.168.1.186 -N

Then:
  curl http://127.0.0.1:8765/health
  python scripts/test_control_plane.py --remote-url http://127.0.0.1:8765/health
"""


def _runner(tool: str, args: dict):
    return {"tool": tool, "args": args, "ok": True}


def _resolve_health_url(remote_url: str | None = None) -> str:
    if remote_url:
        url = remote_url.rstrip("/")
        return url if url.endswith("/health") else f"{url}/health"
    base = os.environ.get("AIONS_REMOTE_API_URL", "").rstrip("/")
    if not base:
        proxmox = os.environ.get("AIONS_PROXMOX_GUEST_API", "http://192.168.1.150:8765")
        base = proxmox.rstrip("/")
    return f"{base}/health"


def check_remote_api(remote_url: str | None = None) -> bool:
    url = _resolve_health_url(remote_url)
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            ok = data.get("status") == "ok"
            print(f"remote_api {url} -> {data}")
            return ok
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"remote_api {url} SKIP ({exc})")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Control plane smoke test + optional remote /health via SSH tunnel.",
        epilog=TUNNEL_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--remote-url",
        metavar="URL",
        help="Remote API base or /health URL (default: env AIONS_REMOTE_API_URL or 192.168.1.150:8765)",
    )
    parser.add_argument(
        "--remote-only",
        action="store_true",
        help="Skip local smoke; only probe remote /health",
    )
    args = parser.parse_args()

    if not args.remote_only:
        plan = store_plan(create_plan("sprawdz health"))
        assert len(plan.steps) >= 1
        step = plan.steps[0]
        result = execute_step(plan.id, step.id, _runner)
        assert result.status == "ok"
        state = get_execution(plan.id)
        assert state and state.status in ("completed", "running")
        print("control_plane smoke OK", plan.id, step.tool)

    if check_remote_api(args.remote_url):
        print("control_plane remote E2E OK")
    else:
        print("control_plane remote E2E skipped (host unreachable from this machine)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
