"""
cli.py — `acae pack --root .`

Dziala bez uruchomionego serwera MCP i bez zadnego demona. To jest bramka M1:
pack ma byc narzedziem, ktore da sie odpalic z terminala, a nie funkcja dostepna
wylacznie przez transport, ktory offloaduje duze wyniki.
"""

from __future__ import annotations

import argparse
import tomllib
from pathlib import Path

from .canon import canonical_json
from .core import PackRequest, build_pack
from .pack import FsLocator, FsReader, FsStore, write_pack

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "acae.toml"


def _load_config(path: Path) -> dict:
    with path.open("rb") as fh:
        return tomllib.load(fh)


def _count_tokens(data: bytes) -> int | None:
    """
    Liczba tokenow tresci packa — tylko na stdout, NIGDY do manifestu.

    Gdyby trafila do manifestu, pack_hash zalezalby od wersji tiktokena, czyli od
    czegos, co nie ma nic wspolnego z trescia repo.
    """
    try:
        import tiktoken
    except ImportError:  # pragma: no cover
        return None
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(data.decode("utf-8", "replace"), disallowed_special=()))


def _cmd_pack(args: argparse.Namespace) -> int:
    cfg = _load_config(Path(args.config) if args.config else DEFAULT_CONFIG)
    pack_cfg = cfg["pack"]
    prune = cfg.get("baseline", {}).get("prune_dirs", [])

    root = Path(args.root).resolve()
    locator = FsLocator(
        root=str(root),
        roots=pack_cfg["roots"],
        prune_dirs=prune,
        max_file_bytes=pack_cfg["max_file_bytes"],
    )
    reader = FsReader(str(root))
    request = PackRequest(root=root.name, mode=args.mode)

    result = build_pack(request, locator, reader)

    counts = result.manifest["counts"]
    if args.out:
        written = write_pack(result, FsStore(args.out))
        print(f"content   {written['content']}")
        print(f"manifest  {written['manifest']}")
    else:
        print(canonical_json(result.manifest, indent=2).decode("utf-8"))

    print(f"pack_hash {result.pack_hash}")
    print(f"pliki     {counts['files']}   symbole {counts['symbols']}   pominiete {counts['skipped']}")

    tokens = _count_tokens(result.content)
    if tokens is not None:
        print(f"tokeny    {tokens} w content.txt")
        if args.budget:
            verdict = "OK" if tokens <= args.budget else "PRZEKROCZONY"
            print(f"budzet    {tokens} / {args.budget} -> {verdict}")
            if tokens > args.budget:
                return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="acae", description="Deterministyczny pack repozytorium.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("pack", help="Zbuduj pack w trybie outline.")
    p.add_argument("--root", default=".", help="Korzen repo do spakowania.")
    p.add_argument("--mode", default="outline", choices=("outline",))
    p.add_argument("--out", default=None, help="Katalog wyjsciowy. Bez niego manifest idzie na stdout.")
    p.add_argument("--config", default=None, help="Sciezka do acae.toml. Domyslnie config/acae.toml modulu.")
    p.add_argument(
        "--budget",
        type=int,
        default=None,
        help="Maksymalna liczba tokenow content.txt. Przekroczenie konczy sie kodem 1.",
    )
    p.set_defaults(func=_cmd_pack)

    args = parser.parse_args(argv)
    return int(args.func(args))
