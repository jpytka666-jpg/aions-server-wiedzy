#!/usr/bin/env python3
"""Analyze a blend mistake record (offline). Usage via scripts/aions_python.ps1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "aions_core" / "memory" / "blends"))

from blend_lib import (  # noqa: E402
    BLEND_DIR,
    CONCLUSIONS_DIR,
    SEED_DIR,
    analyze_mistake,
    load_blend,
    save_blend,
    update_manifest,
)


def resolve_input(path: str) -> Path:
    p = Path(path)
    if p.exists():
        return p
    seed = SEED_DIR / f"{path}.json"
    if seed.exists():
        return seed
    seed2 = SEED_DIR / path
    if seed2.exists():
        return seed2
    raise FileNotFoundError(f"Blend not found: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="AIONS blend analyzer (offline)")
    parser.add_argument("input", help="Path to mistake/blend JSON or blend id")
    parser.add_argument(
        "-o", "--output", help="Output path (default: conclusions/<id>.json)"
    )
    parser.add_argument("--json", action="store_true", help="Print full blend JSON to stdout")
    args = parser.parse_args()

    src = resolve_input(args.input)
    blend = load_blend(src)
    blend = analyze_mistake(blend)

    out = Path(args.output) if args.output else CONCLUSIONS_DIR / f"{blend['id']}.json"
    save_blend(blend, out)
    update_manifest(blend, out)

    if args.json:
        print(json.dumps(blend, ensure_ascii=False, indent=2))
    else:
        a = blend["analyzer"]
        print(f"OK analyzed {blend['id']}")
        print(f"  error_class: {a['error_class']}")
        print(f"  root_cause: {a['root_cause']}")
        print(f"  output: {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
