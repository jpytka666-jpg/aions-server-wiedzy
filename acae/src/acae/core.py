"""
core.py — PackRequest -> PackResult. Czysta funkcja, zero I/O.

"Czysta" znaczy tu: modul nie importuje os.path do chodzenia po dysku, nie otwiera
plikow, nie wola gita i nie zna katalogu roboczego. Wszystko, co przychodzi ze swiata,
przychodzi przez porty. Dlatego caly rdzen da sie przetestowac na slowniku w pamieci —
to jedna z bramek M1, a nie ozdoba architektoniczna.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from . import __version__
from .canon import canonical_json, content_hash
from .ports import Locator, Reader
from .secrets import scan_bytes
from .symbols import NoGrammar, lang_for, outline_from_bytes

SCHEMA = "acae.pack.v1"

# Zamkniete wyliczenie powodow. Plik nie moze wypasc z packa poza ta lista.
REASONS = ("ignored", "binary", "too_large", "secret", "no_grammar", "submodule", "unreadable")


@dataclass(frozen=True)
class PackRequest:
    root: str
    mode: str = "outline"
    tool_version: str = __version__


@dataclass(frozen=True)
class PackResult:
    manifest: Mapping[str, object]
    content: bytes
    skipped: Sequence[Mapping[str, object]] = field(default_factory=tuple)

    @property
    def pack_hash(self) -> str:
        return str(self.manifest["pack_hash"])


def _content_lines(entries: Sequence[Mapping[str, object]]) -> list[str]:
    """
    Tresc packa: naglowek pliku, potem po jednym wierszu na symbol.

    Format jest celowo waski. To jest artefakt, ktory ma OSZCZEDZAC tokeny — kazdy
    znak ozdobnika mnozy sie przez liczbe symbolow w repo. Sygnatura niesie wiecej
    informacji niz nazwa, wiec zostaje; ciala nie ma z definicji trybu outline.
    """
    out: list[str] = [f"# {SCHEMA}"]
    for entry in entries:
        out.append("")
        out.append(f"## {entry['path']} [{entry['lang']}]")
        for row in entry["symbols"]:  # type: ignore[index]
            sig = (row["signature"] or "").strip()
            # Docstring CELOWO nie trafia do tresci packa. Zmierzone: emisja podnosila
            # pack z 36492 do 46296 tokenow (+27%) i wycinki niemal dwukrotnie
            # (q05 1174 -> 3884), nie poprawiajac ani jednego zapytania. Pole `doc`
            # zostaje w wierszach outline'u, bo tam sluzy PUNKTOWANIU i kosztuje zero.
            out.append(f"  {row['line']} {row['kind']} {row['name_path']} | {sig}")
    out.append("")
    return out


def collect_entries(
    locator: Locator,
    reader: Reader,
    outline_cache: dict | None = None,
) -> tuple[list[dict], list[dict]]:
    """
    Przefiltrowane wpisy plikow plus raport pominiec. Czysta funkcja nad portami.

    Kolejnosc plikow narzucamy TUTAJ, przez sorted(), zamiast ufac kontraktowi portu.
    Bramka M1 wymaga, zeby Locator zwracajacy liste odwrocona dal ten sam pack_hash —
    a to jest wlasnosc rdzenia, nie uprzejmosc adaptera.

    Wydzielone z build_pack, bo M2 (drill) potrzebuje DOKLADNIE tego samego zbioru
    plikow co M1. Druga kopia regul odrzucania rozjechalaby sie przy pierwszej zmianie
    i bramka M2 przestalaby byc porownywalna z M1.

    `outline_cache` — opcjonalny slownik `(sciezka, content_hash) -> wiersze outline`.
    Zmierzone: przy jednym zapytaniu **8865 ms z 8865 ms** idzie na ponowne parsowanie
    tych samych 169 plikow, a samo szukanie zajmuje 0 ms. Cache usuwa dokladnie ten koszt.

    Rdzen NADAL nie dotyka dysku — dostaje gotowy slownik i go uzupelnia, a zapisywanie
    zostaje po stronie adaptera (`parsecache.py`). Bez tego rozdzialu bramka „rdzen dziala
    na slowniku w pamieci" przestalaby obowiazywac.

    Gdy `outline_cache` jest `None`, zachowanie jest IDENTYCZNE z poprzednim —
    pilnuje tego `test_cache_nie_zmienia_pack_hash`.
    """
    skipped: list[dict] = [dict(s) for s in locator.skipped()]
    entries: list[dict] = []

    for rel in sorted(locator.list_files()):
        try:
            raw = reader.read(rel)
        except OSError:
            skipped.append({"path": rel, "reason": "unreadable"})
            continue

        if b"\x00" in raw:
            skipped.append({"path": rel, "reason": "binary"})
            continue

        ch = content_hash(raw)

        # Szukanie sekretow tez idzie do cache. Zmierzone: 1244 ms na przebieg, liczone
        # od nowa dla tych samych niezmienionych plikow. Klucz to SAMA TRESC — regula
        # nie zalezy od sciezki, w odroznieniu od outline'u, gdzie decyduje rozszerzenie.
        klucz_s = f"s\x00{ch}"
        rules = None if outline_cache is None else outline_cache.get(klucz_s)
        if rules is None:
            rules = sorted({h["rule"] for h in scan_bytes(raw)})
            if outline_cache is not None:
                outline_cache[klucz_s] = rules
        if rules:
            # Powod i nazwy regul — nigdy sama tresc trafienia.
            skipped.append({"path": rel, "reason": "secret", "rules": rules})
            continue

        if lang_for(rel) is None:
            skipped.append({"path": rel, "reason": "no_grammar"})
            continue

        # Klucz cache: sciezka ORAZ hash tresci. Sama tresc nie wystarcza, bo gramatyka
        # zalezy od rozszerzenia — ten sam bajt w bajt plik pod inna nazwa moze dac
        # inny outline. Zmiana nazwy powoduje chybienie, i tak ma byc.
        ch = content_hash(raw)
        klucz = f"{rel}\x00{ch}"
        rows = None if outline_cache is None else outline_cache.get(klucz)

        if rows is None:
            try:
                rows = outline_from_bytes(rel, raw)
            except NoGrammar:
                skipped.append({"path": rel, "reason": "no_grammar"})
                continue
            if outline_cache is not None:
                outline_cache[klucz] = rows

        entries.append({
            "path": rel,
            "lang": lang_for(rel),
            "bytes": len(raw),
            "content_hash": ch,
            "symbols": rows,
        })

    return entries, skipped


def build_pack(request: PackRequest, locator: Locator, reader: Reader) -> PackResult:
    """Zlozenie packa z tego, co podaja porty."""
    entries, skipped = collect_entries(locator, reader)
    total_symbols = sum(len(e["symbols"]) for e in entries)

    content = "\n".join(_content_lines(entries)).encode("utf-8")

    manifest: dict = {
        "schema": SCHEMA,
        "root": request.root,
        "mode": request.mode,
        "tool_version": request.tool_version,
        "counts": {
            "files": len(entries),
            "symbols": total_symbols,
            "skipped": len(skipped),
            "content_bytes": len(content),
        },
        "files": [
            {
                "path": e["path"],
                "lang": e["lang"],
                "bytes": e["bytes"],
                "content_hash": e["content_hash"],
                "symbols": len(e["symbols"]),
            }
            for e in entries
        ],
        "skipped": sorted(skipped, key=lambda s: (str(s.get("path", "")), str(s.get("reason", "")))),
        "content_hash": content_hash(content),
    }
    # pack_hash liczony z manifestu BEZ pola pack_hash — inaczej zaleznosc byla by
    # cykliczna i trzeba by ja maskowac pustym stringiem, co latwo przeoczyc przy zmianie.
    manifest["pack_hash"] = content_hash(canonical_json(manifest))

    return PackResult(manifest=manifest, content=content, skipped=tuple(manifest["skipped"]))
