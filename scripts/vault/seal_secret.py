#!/usr/bin/env python3
"""Seal a plaintext secret file into the AIONS local DPAPI vault.

Usage (Windows, zalogowany operator Marcin):
  .\\scripts\\aions_python.ps1 scripts\\vault\\seal_secret.py ^
      --input C:\\Downloads\\client_secret.json ^
      --vault-id google_oauth_client ^
      --label "Google OAuth Desktop client"

Nigdy nie commituj runtime/secrets/vault/ ani plaintext JSON.
Agenci: nie echo'uj zawartości pliku — tylko ten skrypt.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running as script without package install
_VAULT_DIR = Path(__file__).resolve().parent
if str(_VAULT_DIR) not in sys.path:
    sys.path.insert(0, str(_VAULT_DIR))

from _core import blob_path, repo_root, seal_file, vault_dir  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Seal plaintext → AIONS DPAPI vault")
    parser.add_argument("--input", required=True, type=Path, help="Plaintext secret file")
    parser.add_argument("--vault-id", required=True, help="Stable vault id (e.g. google_oauth_client)")
    parser.add_argument("--label", default="", help="Human label stored in index (no secret bytes)")
    args = parser.parse_args()

    try:
        out = seal_file(args.input.resolve(), args.vault_id, args.label)
    except Exception as exc:
        print(f"[AIONS vault] BLAD seal: {exc}", file=sys.stderr)
        return 1

    print("[AIONS vault] OK — zaszyfrowano (DPAPI CurrentUser)")
    print(f"  repo:     {repo_root()}")
    print(f"  vault:    {vault_dir()}")
    print(f"  vault_id: {args.vault_id}")
    print(f"  blob:     {out}")
    print(f"  index:    {vault_dir() / 'index.json'}")
    print("  Nastepny krok: usun plaintext poza gitem; otwieraj przez open_secret.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
