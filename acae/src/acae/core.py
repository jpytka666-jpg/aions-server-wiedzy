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
            # Docstring skrocony mocniej niz w wierszu outline'u: w packu placi sie za
            # niego liczba symboli w calym repo, a pierwsze zdanie niesie wiekszosc sensu.
            doc = " ".join((row.get("doc") or "").split())[:120]
            out.append(f"  {row['line']} {row['kind']} {row['name_path']} | {sig}" + (f" :: {doc}" if doc else ""))
    out.append("")
    return out


def collect_entries(locator: Locator, reader: Reader) -> tuple[list[dict], list[dict]]:
    """
    Przefiltrowane wpisy plikow plus raport pominiec. Czysta funkcja nad portami.

    Kolejnosc plikow narzucamy TUTAJ, przez sorted(), zamiast ufac kontraktowi portu.
    Bramka M1 wymaga, zeby Locator zwracajacy liste odwrocona dal ten sam pack_hash —
    a to jest wlasnosc rdzenia, nie uprzejmosc adaptera.

    Wydzielone z build_pack, bo M2 (drill) potrzebuje DOKLADNIE tego samego zbioru
    plikow co M1. Druga kopia regul odrzucania rozjechalaby sie przy pierwszej zmianie
    i bramka M2 przestalaby byc porownywalna z M1.
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

        hits = scan_bytes(raw)
        if hits:
            # Powod i numery linii — nigdy sama tresc trafienia.
            skipped.append({"path": rel, "reason": "secret", "rules": sorted({h["rule"] for h in hits})})
            continue

        if lang_for(rel) is None:
            skipped.append({"path": rel, "reason": "no_grammar"})
            continue

        try:
            rows = outline_from_bytes(rel, raw)
        except NoGrammar:
            skipped.append({"path": rel, "reason": "no_grammar"})
            continue

        entries.append({
            "path": rel,
            "lang": lang_for(rel),
            "bytes": len(raw),
            "content_hash": content_hash(raw),
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
