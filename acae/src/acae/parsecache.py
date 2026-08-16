"""
parsecache.py — trwaly cache sparsowanych outline'ow. ADAPTER, nie rdzen.

PO CO
-----
Zmierzone na zywym repo: jedno zapytanie trwa **9490 ms**, z czego **8865 ms** to
ponowne parsowanie tych samych 169 plikow, a samo szukanie **0 ms**. Sto procent czasu
idzie na przemielenie od nowa czegos, co sie nie zmienilo.

Cache usuwa dokladnie ten koszt i nic wiecej. Nie dotyka punktacji, nie zmienia
`pack_hash`, nie ma wplywu na zaden pomiar — pilnuja tego testy.

DLACZEGO TO NIE JEST W `core.py`
--------------------------------
Rdzen ma zapisana bramke: „nie otwiera plikow, nie zna katalogu roboczego, caly da sie
przetestowac na slowniku w pamieci" (M1). Cache musi cos zapisac na dysk, wiec zyje tutaj.
`core.collect_entries` przyjmuje gotowy SLOWNIK i go uzupelnia; calosc I/O jest w tym module.

UNIEWAZNIANIE — dwa poziomy, oba konieczne
------------------------------------------
1. **Klucz** to `(sciezka, content_hash)`. Zmiana choc jednego bajtu pliku to chybienie
   i ponowne sparsowanie. Zmiana nazwy tez.
2. **Wersje gramatyk** siedza w naglowku pliku cache. Zmiana `tree-sitter` albo
   `tree-sitter-language-pack` **wyrzuca CALY cache**, bo inna wersja gramatyki daje
   inny outline, a wiec inny `pack_hash`. To jest ryzyko R9 z kontraktu i jedyny sposob,
   w jaki ten cache moglby cicho zepsuc artefakt.

Bez punktu 2 cache po aktualizacji biblioteki podawalby stary outline dla niezmienionego
pliku i `pack_hash` przestalby odpowiadac temu, co narzedzie naprawde widzi.
"""

from __future__ import annotations

import json
from importlib import metadata
from pathlib import Path

SCHEMA = "acae.parsecache.v1"

# Pakiety, ktorych wersja zmienia ksztalt outline'u. Zgodne z pinami z requirements.txt
# i z ryzykiem R9 opisanym w CONTRACT.md.
PAKIETY_GRAMATYK = ("tree-sitter", "tree-sitter-language-pack")


def wersje_gramatyk() -> dict[str, str]:
    out = {}
    for nazwa in PAKIETY_GRAMATYK:
        try:
            out[nazwa] = metadata.version(nazwa)
        except metadata.PackageNotFoundError:
            out[nazwa] = "(brak)"
    return out


def load(path: Path) -> dict:
    """
    Wczytanie cache. Przy rozjezdzie wersji gramatyk zwraca PUSTY slownik.

    Cicha odmowa jest tu wlasciwa: brak cache to tylko wolniej, a zly cache to zly
    `pack_hash`. Wolimy zaplacic dziewiec sekund niz oddac artefakt, ktory nie opisuje
    tego, co jest na dysku.
    """
    p = Path(path)
    if not p.is_file():
        return {}
    try:
        dane = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if dane.get("schema") != SCHEMA:
        return {}
    if dane.get("grammars") != wersje_gramatyk():
        return {}
    wpisy = dane.get("entries")
    return dict(wpisy) if isinstance(wpisy, dict) else {}


def save(path: Path, cache: dict) -> None:
    """Zapis cache wraz z wersjami gramatyk. Blad zapisu jest NIEISTOTNY — to tylko szybkosc."""
    p = Path(path)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(
                {"schema": SCHEMA, "grammars": wersje_gramatyk(), "entries": cache},
                ensure_ascii=False, sort_keys=True,
            ) + "\n",
            encoding="utf-8", newline="\n",
        )
    except OSError:
        pass
