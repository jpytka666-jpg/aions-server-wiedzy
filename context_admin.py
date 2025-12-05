from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from server.store import VectorStore


def _default_output_dir() -> Path:
    return Path("logs") / "context_dumps"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def cmd_list(store: VectorStore, _: argparse.Namespace) -> None:
    sessions = store.list_sessions()
    print(json.dumps({"sessions": sessions}, ensure_ascii=False, indent=2))


def cmd_stats(store: VectorStore, args: argparse.Namespace) -> None:
    stats = store.session_stats(args.session_id)
    print(json.dumps(stats, ensure_ascii=False, indent=2))


def cmd_dump(store: VectorStore, args: argparse.Namespace) -> None:
    output_dir = Path(args.output or _default_output_dir())
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    sessions = store.list_sessions()
    _ensure_dir(output_dir)
    summary: dict[str, Any] = {"timestamp": timestamp, "sessions": []}
    for entry in sessions:
        session_id = entry["session_id"]
        dump = store.dump_session(session_id)
        session_dir = output_dir / session_id
        _ensure_dir(session_dir)
        dump_path = session_dir / f"{timestamp}.jsonl"
        with dump_path.open("w", encoding="utf-8") as fh:
            for item in dump["entries"]:
                fh.write(json.dumps(item, ensure_ascii=False))
                fh.write("\n")
        summary["sessions"].append({"session_id": session_id, "file": str(dump_path), "documents": len(dump["entries"])})
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def cmd_prune(store: VectorStore, args: argparse.Namespace) -> None:
    cutoff = None
    if args.cutoff:
        cutoff = datetime.fromisoformat(args.cutoff.replace("Z", "+00:00"))
    removed = store.prune_expired(args.session_id, cutoff)
    print(json.dumps({"session_id": args.session_id, "removed": removed}, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AIONS Context Administration CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub_list = sub.add_parser("list", help="List sessions")
    sub_list.set_defaults(func=cmd_list)

    sub_stats = sub.add_parser("stats", help="Session statistics")
    sub_stats.add_argument("session_id")
    sub_stats.set_defaults(func=cmd_stats)

    sub_dump = sub.add_parser("dump", help="Snapshot all sessions to disk")
    sub_dump.add_argument("--output", "-o", help="Output directory (default logs/context_dumps)")
    sub_dump.set_defaults(func=cmd_dump)

    sub_prune = sub.add_parser("prune", help="Prune expired entries in a session")
    sub_prune.add_argument("session_id")
    sub_prune.add_argument("--cutoff", help="ISO timestamp overriding metadata expires_at checks")
    sub_prune.set_defaults(func=cmd_prune)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    persist = os.environ.get("CHROMA_PATH")
    store = VectorStore(persist_path=persist)
    args.func(store, args)


if __name__ == "__main__":
    main()
