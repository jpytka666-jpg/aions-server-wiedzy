"""
cli.py — `acae pack` i `acae ask`.

Dziala bez uruchomionego serwera MCP i bez zadnego demona. To jest bramka M1:
pack ma byc narzedziem, ktore da sie odpalic z terminala, a nie funkcja dostepna
wylacznie przez transport, ktory offloaduje duze wyniki.

`pack` buduje caly szkielet repo. `ask` robi to, po co ten szkielet istnieje:
tnie go pod jedno pytanie i dociaga ciala kilku symboli. To jest wzorzec
outline-then-drill w postaci komendy.
"""

from __future__ import annotations

import argparse
import tomllib
from pathlib import Path

from .canon import canonical_json
from . import parsecache
from .core import PackRequest, build_pack, collect_entries
from .pack import FsLocator, FsReader, FsStore, write_pack
from .retrieve import build_slice

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "acae.toml"


def _load_config(path: Path) -> dict:
    with path.open("rb") as fh:
        return tomllib.load(fh)


def _ports(args: argparse.Namespace) -> tuple[Path, FsLocator, FsReader, dict]:
    """Wspolne wejscie obu komend: config, korzen, Locator i Reader."""
    cfg = _load_config(Path(args.config) if args.config else DEFAULT_CONFIG)
    pack_cfg = cfg["pack"]
    root = Path(args.root).resolve()
    locator = FsLocator(
        root=str(root),
        roots=pack_cfg["roots"],
        prune_dirs=cfg.get("baseline", {}).get("prune_dirs", []),
        max_file_bytes=pack_cfg["max_file_bytes"],
    )
    return root, locator, FsReader(str(root)), cfg


def _count_tokens(data: bytes) -> int | None:
    """
    Liczba tokenow — tylko na stdout, NIGDY do manifestu.

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
    root, locator, reader, _ = _ports(args)
    result = build_pack(PackRequest(root=root.name, mode=args.mode), locator, reader)
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


def _cmd_ask(args: argparse.Namespace) -> int:
    """
    Wycinek szkieletu pod jedno pytanie plus ciala kilku najlepiej trafionych symboli.

    Bez --out tresc idzie na stdout i nic wiecej, zeby dalo sie ja przepuscic potokiem.
    Podsumowanie pojawia sie tylko wtedy, gdy tresc trafia do pliku.
    """
    root, locator, reader, _ = _ports(args)

    # Cache sparsowanych outline'ow. Zmierzone przed jego dolozeniem: jedno pytanie
    # trwalo 9490 ms, z czego 8865 ms szlo na ponowne parsowanie tych samych plikow,
    # a samo szukanie 0 ms. Cache nie zmienia ANI wyniku, ANI `pack_hash` —
    # pilnuje tego `test_cache_nie_zmienia_pack_hash`.
    cache_path = root / "acae" / "_out" / "parse_cache.json"
    outline_cache = parsecache.load(cache_path)
    przed = len(outline_cache)
    entries, _skipped = collect_entries(locator, reader, outline_cache=outline_cache)
    if len(outline_cache) != przed:
        parsecache.save(cache_path, outline_cache)

    # Ranking po ZNACZENIU, gdy sa oba artefakty: tablica wektorow i opisy plikow.
    # Zmierzone na 306 pytaniach zadanych po ludzku: 62,0% wobec 25,1% dla samego
    # szukania po slowach. Bez tego narzedzie oddawaloby dwuipolkrotnie gorszy wynik
    # niz ten, ktory mierzymy.
    #
    # Gdy ktoregokolwiek artefaktu brak — cichy powrot do rankera leksykalnego.
    # Narzedzie ma dzialac gorzej, a nie nie dzialac wcale.
    ranked = None
    uwagi: list[str] = []
    if args.rank == "meaning":
        try:
            from .describe import load_descriptions
            from .embed import StaticEmbedder
            from .embedindex import EmbedIndex

            opisy, prov = load_descriptions(root / "acae" / "_desc" / "descriptions.json",
                                            strict=False)
            brakujace = {str(e["path"]) for e in entries} - set(opisy)
            if brakujace:
                uwagi.append(f"{len(brakujace)} plikow bez opisu (pack sie zmienil?)")
            index = EmbedIndex(StaticEmbedder(root / "acae" / "_model"), entries, opisy)
            ranked = index.ranked(args.query, max(args.outline_limit, args.drill))
        except Exception as e:  # brak modelu, brak opisow, zle wersje — wszystko jedno
            uwagi.append(f"ranking po znaczeniu niedostepny ({type(e).__name__}), "
                         f"szukam samymi slowami")

    text, meta = build_slice(
        entries,
        args.query,
        reader,
        outline_limit=args.outline_limit,
        drill_limit=args.drill,
        ranked=ranked,
    )
    for u in uwagi:
        print(f"uwaga     {u}")

    if args.out:
        location = FsStore(args.out).write("slice.txt", text)
        print(f"slice     {location}")
        print(f"terminy   {' '.join(meta['terms'])}")
        print(f"symbole   {meta['outline_symbols']} w szkielecie, {meta['drilled']} z cialem")
        print(f"pliki     {meta['files']}")
        tokens = _count_tokens(text)
        if tokens is not None:
            print(f"tokeny    {tokens}")
            if args.budget:
                verdict = "OK" if tokens < args.budget else "PRZEKROCZONY"
                print(f"budzet    {tokens} / {args.budget} -> {verdict}")
                if tokens >= args.budget:
                    return 1
    else:
        print(text.decode("utf-8"), end="")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="acae", description="Deterministyczny pack repozytorium.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=".", help="Korzen repo.")
    common.add_argument("--config", default=None, help="Sciezka do acae.toml. Domyslnie config/acae.toml modulu.")
    common.add_argument("--out", default=None, help="Katalog wyjsciowy.")
    common.add_argument("--budget", type=int, default=None, help="Limit tokenow; przekroczenie konczy sie kodem 1.")

    p = sub.add_parser("pack", parents=[common], help="Zbuduj pack w trybie outline.")
    p.add_argument("--mode", default="outline", choices=("outline",))
    p.set_defaults(func=_cmd_pack)

    a = sub.add_parser("ask", parents=[common], help="Wytnij szkielet pod pytanie i dociagnij ciala.")
    a.add_argument("--query", required=True, help="Pytanie w jezyku naturalnym.")
    a.add_argument("--outline-limit", type=int, default=40, help="Ile symboli trafia do szkieletu.")
    a.add_argument("--drill", type=int, default=5, help="Ile symboli dostaje pelne cialo.")
    a.set_defaults(func=_cmd_ask)

    args = parser.parse_args(argv)
    return int(args.func(args))
