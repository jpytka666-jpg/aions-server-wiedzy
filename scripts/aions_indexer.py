#!/usr/bin/env python3
"""Build or inspect the AIONS Linux filesystem index."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "mcpServers" / "VS_CODE_MCP_CODEX" / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from filesystem_provider import AionsLinuxIndexProvider  # noqa: E402


def _split_roots(raw: str) -> list[Path]:
    return [Path(part.strip()) for part in raw.split(os.pathsep) if part.strip()]


def build_provider(index_path: str, roots_arg: str, refresh_seconds: int) -> AionsLinuxIndexProvider:
    roots = _split_roots(roots_arg)
    return AionsLinuxIndexProvider(
        roots,
        Path(index_path),
        auto_refresh_seconds=refresh_seconds,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="AIONS Linux filesystem indexer")
    parser.add_argument(
        "action",
        choices=["refresh", "status", "ensure"],
        help="Refresh the index, print status, or refresh only when stale",
    )
    parser.add_argument(
        "--index-path",
        default=os.environ.get("AIONS_SEARCH_INDEX_PATH", str(REPO_ROOT / "runtime" / "state" / "aions_search_index.json")),
        help="Path to index JSON file",
    )
    parser.add_argument(
        "--roots",
        default=os.environ.get("AIONS_SEARCH_ROOTS", str(REPO_ROOT)),
        help=f"Search roots separated by '{os.pathsep}'",
    )
    parser.add_argument(
        "--refresh-seconds",
        type=int,
        default=int(os.environ.get("AIONS_SEARCH_AUTO_REFRESH_SECONDS", "900")),
        help="Auto-refresh age threshold in seconds",
    )
    args = parser.parse_args()

    provider = build_provider(args.index_path, args.roots, args.refresh_seconds)
    if args.action == "refresh":
        payload = provider.refresh()
    elif args.action == "ensure":
        payload = provider.ensure_fresh()
    else:
        payload = provider.status()

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
