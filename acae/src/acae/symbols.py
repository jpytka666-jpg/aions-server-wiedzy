"""
symbols.py — jedyny punkt styku ACAE z ts_symbols.py.

REGULA ADDITIVE ONLY: aions_core/server/ts_symbols.py NIE JEST RUSZANY. Bierzemy
z niego LANGS, DEF_NODES i mechanike chodzenia po drzewie; zastepujemy warstwe,
ktora jest CBMS-owa albo niedeterministyczna.

DLACZEGO NIE SymbolIndex.from_file()
------------------------------------
`from_file()` sam otwiera plik (ts_symbols.py:131-132). Bramka M1 wymaga, zeby rdzen
przechodzil testy na Readerze w pamieci, bez dotykania dysku — a `from_file` wnosi
I/O w srodek sciezki parsowania. Skladamy wiec indeks z bajtow, powtarzajac to,
co robi `from_file`, ale na bajtach dostarczonych przez port.

Kosztem jest zaleznosc od PRYWATNEJ metody `_walk`. Swiadoma: alternatywy to
dopisanie `from_bytes()` do ts_symbols.py (lamie ADDITIVE ONLY) albo zapis do pliku
tymczasowego (lamie bramke). Zaleznosc jest zapisana w TERMS.md jako sprzezenie
do sprawdzenia przy kazdej zmianie ts_symbols.py.

CO ZASTEPUJEMY
--------------
`sha12()` = SHA-1 obciety do 12 znakow hex, liczony po decode(errors="replace")
(:88-89, :133). Stratny i 48-bitowy: dwa rozne ciagi bajtow z niepoprawnym UTF-8
daja ten sam hash. Nasze `body_hash` to blake2b256 z bajtow ciala.
"""

from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path

from .canon import content_hash


def _aions_root() -> str:
    """
    Korzen repo AIONS, w ktorym lezy aions_core/.

    ACAE mieszka w tym repo (decyzja D1), wiec korzen wyliczamy ze wlasnego polozenia:
    src/acae/symbols.py -> src/acae -> src -> acae -> korzen. Zadnej sciezki
    absolutnej w kodzie; nadpisywalne zmienna srodowiskowa dla nietypowych ukladow.
    """
    return os.getenv("ACAE_AIONS_ROOT") or str(Path(__file__).resolve().parents[3])


def _ensure_aions_importable() -> None:
    root = _aions_root()
    if root not in sys.path:
        sys.path.insert(0, root)


_ensure_aions_importable()

from aions_core.server.ts_symbols import LANGS, SymbolIndex  # noqa: E402

try:  # pragma: no cover — brak gramatyk to blad srodowiska, nie sciezka logiki
    from tree_sitter_language_pack import get_parser
except ImportError:  # pragma: no cover
    get_parser = None


class NoGrammar(Exception):
    """Rozszerzenie bez gramatyki w LANGS. Plik trafia do skipped, pack sie nie wywraca."""


def lang_for(rel_path: str) -> str | None:
    """Nazwa gramatyki dla sciezki albo None. LANGS pochodzi z importu, nie z kopii."""
    return LANGS.get(os.path.splitext(rel_path)[1].lower())


@lru_cache(maxsize=None)
def _parser(lang: str):
    """
    Parser per gramatyka, tworzony raz.

    Drzewa tree-sittera nie sa thread-safe (dokumentacja: instancje drzew wymagaja
    jawnej kopii do uzycia w wielu watkach), wiec pakowanie jest jednowatkowe.
    Determinizm i tak wymaga stabilnej kolejnosci, wiec nic na tym nie tracimy.
    """
    if get_parser is None:
        raise RuntimeError("brak tree_sitter_language_pack — zainstaluj z requirements.txt")
    return get_parser(lang)


def index_from_bytes(rel_path: str, raw: bytes) -> SymbolIndex:
    """
    Indeks symboli zlozony z BAJTOW, bez dotykania dysku.

    Powtarza to, co robi `SymbolIndex.from_file`, ale na bajtach z portu Reader.
    Wejsciem sa bajty JUZ znormalizowane przez canon.normalize_source — dzieki temu
    numery linii odnosza sie do tresci z LF, identycznie na kazdym systemie.

    M1 i M2 potrzebuja tego samego indeksu w roznych celach: M1 bierze z niego szkielet,
    M2 dociaga z niego cialo pojedynczego symbolu. Dlatego prywatnej `_walk` dotykamy
    w JEDNYM miejscu, a nie w dwoch — sprzezenie ma miec jeden punkt pekniecia.
    """
    lang = lang_for(rel_path)
    if lang is None:
        raise NoGrammar(rel_path)

    idx = SymbolIndex(rel_path, raw.decode("utf-8", "replace"), lang)
    tree = _parser(lang).parse(raw)
    idx._walk(tree.root_node, [], raw)  # noqa: SLF001 — patrz docstring modulu
    return idx


def body_of(idx: SymbolIndex, name_path: str) -> str | None:
    """
    Cialo symbolu albo None. To jest cale „drill" z wzorca outline-then-drill.

    `idx.get()` dopasowuje najpierw doslownie, a potem po sufiksie `name_path`
    (ts_symbols.py:225-232) — wiec „evaluate" trafi w „CRLACore/evaluate", jesli nic
    doslowniejszego nie ma. Dla M2 to zachowanie jest pozadane: zapytanie zna nazwe,
    rzadko zna pelna sciezke.
    """
    sym = idx.get(name_path)
    return None if sym is None else (sym.body or "")


def outline_rows(idx: SymbolIndex) -> list[dict]:
    """
    Szkielet pliku: sygnatury bez cial.

    Kolejnosc wierszy: (linia poczatkowa, name_path). Sam numer linii nie wystarcza,
    bo dwa symbole moga zaczynac sie w tej samej linii — wtedy o kolejnosci decydowalby
    porzadek slownika, czyli kolejnosc wstawiania.
    """
    rows: list[dict] = []
    for sym in sorted(idx.symbols.values(), key=lambda s: (s.start_line or 0, s.name_path or "")):
        body = (sym.body or "").encode("utf-8")
        rows.append({
            "name_path": sym.name_path,
            "kind": sym.kind,
            "line": sym.start_line,
            "lines": (sym.end_line or 0) - (sym.start_line or 0) + 1,
            "signature": sym.signature,
            # blake2b256 zamiast sha12 z ts_symbols — patrz docstring modulu
            "body_hash": content_hash(body),
            "n_refs": len(sym.refs or ()),
        })
    return rows


def outline_from_bytes(rel_path: str, raw: bytes) -> list[dict]:
    """Skrot dla M1: bajty w srodku, szkielet na wyjsciu."""
    return outline_rows(index_from_bytes(rel_path, raw))
