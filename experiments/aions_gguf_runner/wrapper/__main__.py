"""CLI: python -m wrapper …  (run from experiments/aions_gguf_runner)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _print(obj: object) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    # Allow `python -m wrapper` when cwd is experiments/aions_gguf_runner
    here = Path(__file__).resolve().parent.parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))

    from wrapper import mouth
    from wrapper.http_server import serve

    p = argparse.ArgumentParser(prog="aions-gguf", description="AIONS GGUF Runner Faza 0")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("health", help="Show backend / GGUF / llama-cli status")

    pu = sub.add_parser("understand", help="Intent JSON")
    pu.add_argument("--text", required=True)

    ps = sub.add_parser("speak", help="Short reply from CONTEXT")
    ps.add_argument("--context", default="")
    ps.add_argument("--context-file", default="")
    ps.add_argument("--lang", default="pl")
    ps.add_argument("--gate-query", default="", help="If set, CBMS gate-first (hit bypasses runner)")

    pv = sub.add_parser("serve", help="HTTP stub on :11435")
    pv.add_argument("--host", default="127.0.0.1")
    pv.add_argument("--port", type=int, default=11435)

    args = p.parse_args(argv)

    if args.cmd == "health":
        _print(mouth.health())
        return 0

    if args.cmd == "understand":
        _print(mouth.understand(args.text))
        return 0

    if args.cmd == "speak":
        ctx = args.context
        if args.context_file:
            ctx = Path(args.context_file).read_text(encoding="utf-8")
        if not ctx.strip():
            print("error: provide --context or --context-file", file=sys.stderr)
            return 2
        _print(
            mouth.speak_with_gate(
                ctx,
                user_lang=args.lang,
                gate_query=args.gate_query or None,
            )
        )
        return 0

    if args.cmd == "serve":
        serve(host=args.host, port=args.port)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
