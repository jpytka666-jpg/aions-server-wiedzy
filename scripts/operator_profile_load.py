#!/usr/bin/env python3
"""Load operator profile from canonical CBMS memory path."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def _resolve_aions_path() -> Path:
    env = os.environ.get("AIONS_PATH", "").strip()
    if env:
        return Path(env)
    candidates = [
        Path(r"E:\server wiedzy\aions_core"),
        Path("/mnt/d/AIONS_DEV/cbms"),
        Path("/mnt/e/server wiedzy/aions_core"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path(r"E:\server wiedzy\aions_core")


def operator_profile_path(aions_path: Path | None = None) -> Path:
    base = aions_path or _resolve_aions_path()
    return base / "memory" / "operator_profile.json"


def load_operator_profile(aions_path: Path | None = None) -> dict[str, Any]:
    path = operator_profile_path(aions_path)
    if not path.is_file():
        return {
            "loaded": False,
            "path": str(path),
            "error": "operator_profile.json not found",
        }
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    return {
        "loaded": True,
        "path": str(path),
        "profile": data,
    }


if __name__ == "__main__":
    print(json.dumps(load_operator_profile(), ensure_ascii=False, indent=2))
