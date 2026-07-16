#!/usr/bin/env python3
"""Offline keyword search across blend library."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "aions_core" / "memory" / "blends"))

from blend_lib import search_blends  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Search AIONS blends (offline)")
    parser.add_argument("query", help="Keywords e.g. 'Proxmox PASS jump'")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("-n", "--limit", type=int, default=5)
    args = parser.parse_args()

    hits = search_blends(args.query)[: args.limit]
    if args.json:
        print(json.dumps(hits, ensure_ascii=False, indent=2))
    else:
        if not hits:
            print("No blends matched.")
            return 0
        for h in hits:
            b = h["blend"]
            rule = b.get("conclusion", {}).get("rule", b.get("mistake", {}).get("claim", ""))
            print(f"[{h['score']}] {b['id']} ({b.get('domain')})")
            print(f"    {rule[:120]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
