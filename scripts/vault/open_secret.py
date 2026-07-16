#!/usr/bin/env python3
"""Open (decrypt) a vault entry — tylko dla zalogowanego operatora Windows (DPAPI).

Usage:
  .\\scripts\\aions_python.ps1 scripts\\vault\\open_secret.py --vault-id google_oauth_client --out runtime\\secrets\\gmail_oauth.json

  .\\scripts\\aions_python.ps1 scripts\\vault\\open_secret.py --list

Agenci MCP: NIGDY nie wypisuj stdout tego skryptu do czatu. Uruchamiaj lokalnie;
control_plane / integracje czytaja plik docelowy, nie chat.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_VAULT_DIR = Path(__file__).resolve().parent
if str(_VAULT_DIR) not in sys.path:
    sys.path.insert(0, str(_VAULT_DIR))

from _core import list_entries, open_vault_entry, vault_dir  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Open AIONS DPAPI vault entry")
    parser.add_argument("--vault-id", help="Vault id to decrypt")
    parser.add_argument("--out", type=Path, help="Write plaintext to this path (0600)")
    parser.add_argument("--list", action="store_true", help="List vault metadata only")
    args = parser.parse_args()

    if args.list:
        entries = list_entries()
        if not entries:
            print("[AIONS vault] (pusty index)")
            return 0
        print(f"[AIONS vault] wpisy w {vault_dir() / 'index.json'}:")
        for vid, meta in sorted(entries.items()):
            print(f"  - {vid}: label={meta.get('label', '')} blob={meta.get('blob', '')}")
        return 0

    if not args.vault_id:
        parser.error("--vault-id wymagane (albo --list)")

    try:
        plaintext = open_vault_entry(args.vault_id)
    except Exception as exc:
        print(f"[AIONS vault] BLAD open: {exc}", file=sys.stderr)
        return 1

    if args.out:
        out_path = args.out.resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(plaintext)
        try:
            os.chmod(out_path, 0o600)
        except OSError:
            pass
        print(f"[AIONS vault] OK — zapisano {out_path} ({len(plaintext)} bajtow)")
        return 0

    # Bez --out: zapis do stdout (TYLKO lokalnie; agenci nie echo'uja)
    sys.stdout.buffer.write(plaintext)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
