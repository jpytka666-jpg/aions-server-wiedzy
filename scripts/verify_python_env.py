#!/usr/bin/env python3
"""Weryfikacja środowiska Python AIONS — uruchamiaj przez aions_python.ps1 / aions_python.sh."""
from __future__ import annotations

import os
import platform
import sys
from pathlib import Path


def load_config(repo_root: Path) -> dict[str, str]:
    cfg_path = repo_root / ".aions" / "python.env"
    if not cfg_path.is_file():
        raise SystemExit(f"[AIONS] Brak konfiguracji: {cfg_path}")
    out: dict[str, str] = {}
    for line in cfg_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        out[key.strip()] = val.strip()
    return out


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    cfg = load_config(repo_root)
    expected = cfg.get("AIONS_PYTHON_VERSION", "?")
    actual = f"{sys.version_info.major}.{sys.version_info.minor}"

    print("=== AIONS Python Environment ===")
    print(f"platform     : {platform.system()} {platform.release()}")
    print(f"executable   : {sys.executable}")
    print(f"version      : {actual} (expected {expected})")
    print(f"repo_root    : {repo_root}")
    print(f"config       : {repo_root / '.aions' / 'python.env'}")
    print(f"AIONS_VENV_WIN  : {cfg.get('AIONS_VENV_WIN', 'n/a')}")
    print(f"AIONS_VENV_LINUX: {cfg.get('AIONS_VENV_LINUX', 'n/a')}")
    print(f"in_venv      : {getattr(sys, 'prefix', '') != getattr(sys, 'base_prefix', '')}")
    print(f"CHROMA_PATH  : {os.environ.get('CHROMA_PATH', '(not set)')}")

    if actual != expected:
        print(f"\n[FAIL] Wersja {actual} != oczekiwana {expected}")
        raise SystemExit(1)
    print("\n[OK] Python environment matches AIONS policy")


if __name__ == "__main__":
    main()
