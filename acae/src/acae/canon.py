"""
canon.py — jedyne miejsce, w ktorym cokolwiek jest sprowadzane do postaci kanonicznej.

Kazda z tych funkcji istnieje, bo bez niej pack_hash chwialby sie z powodu, ktory
nie ma nic wspolnego z trescia kodu: kolejnosci systemu plikow, systemu operacyjnego,
ustawien gita albo kolejnosci kluczy w slowniku.

Regula: normalizacja zachodzi RAZ, na brzegu. Dalej w glab modulu nie ma juz zadnego
wariantu zapisu — jest jedna pisownia sciezki, jeden rodzaj konca linii, jeden hash.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import PurePosixPath, PureWindowsPath

HASH_PREFIX = "blake2b256"
UTF8_BOM = b"\xef\xbb\xbf"


def normalize_source(raw: bytes) -> bytes:
    """
    Bajty zrodla sprowadzone do postaci niezaleznej od systemu i od ustawien gita.

    DLACZEGO TO NIE JEST "raw_bytes" Z PLANU §6.3
    ----------------------------------------------
    To repo ma core.autocrlf=true. Ten sam plik na Windowsie lezy na dysku z CRLF,
    a na Linuksie z LF. Hash z doslownie surowych bajtow bylby wiec rozny na roznych
    maszynach — a bramka M1 wymaga, zeby pack_hash byl porownywalny. Normalizujemy
    konce linii i scinamy BOM, a odstepstwo jest zapisane w TERMS.md zamiast byc
    cicha wlasnoscia implementacji.

    Kolejnosc podmian ma znaczenie: najpierw CRLF, potem samotne CR. Odwrotna
    kolejnosc zamienilaby CRLF w dwa znaki nowej linii.
    """
    if raw.startswith(UTF8_BOM):
        raw = raw[len(UTF8_BOM):]
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def content_hash(data: bytes) -> str:
    """
    Hash tresci w postaci "blake2b256:<64 hex>".

    Prefiks jest nazwany wprost (decyzja D2), zeby ewentualna zmiana algorytmu byla
    widoczna w danych zamiast byc cicha. Wejsciem jest wylacznie tresc — nigdy mtime,
    nigdy sciezka, nigdy rozmiar.
    """
    return f"{HASH_PREFIX}:{hashlib.blake2b(data, digest_size=32).hexdigest()}"


def to_posix_rel(path: str, root: str) -> str:
    """
    Sciezka wzgledna wobec roota, w jednej pisowni: separatory POSIX, bez './'.

    To jest JEDYNY klucz slownikow, JEDYNY klucz sortowania i JEDYNE wejscie do
    hasha sciezki w calym module. Dzis ten sam plik potrafi miec trzy pisownie
    zaleznie od tego, ktora sciezka kodu go dotknela — tu ma miec jedna.

    Nie dotyka dysku: to czysta operacja na tekscie, zeby dalo sie jej uzyc
    w rdzeniu i w testach na Readerze w pamieci.
    """
    pure = PureWindowsPath if ("\\" in path or "\\" in root) else PurePosixPath
    rel = pure(path).relative_to(pure(root))
    return PurePosixPath(*rel.parts).as_posix()


def _reject_floats(obj: object, where: str = "$") -> None:
    """
    Float w artefakcie deterministycznym to bomba z opoznionym zaplonem.

    Reprezentacja zmiennoprzecinkowa potrafi sie roznic miedzy wersjami Pythona
    i platformami, a JSON nie ma dla niej postaci kanonicznej. Kazda miara w ACAE
    jest calkowita; jesli cos jest ulamkiem, ma byc zapisane jako para licznik/mianownik
    albo jako promile, nie jako float.
    """
    if isinstance(obj, float):
        raise TypeError(f"float w kanonicznym JSON w {where}: {obj!r}")
    if isinstance(obj, dict):
        for key, value in obj.items():
            if not isinstance(key, str):
                raise TypeError(f"klucz nie-tekstowy w {where}: {key!r}")
            _reject_floats(value, f"{where}.{key}")
    elif isinstance(obj, (list, tuple)):
        for i, value in enumerate(obj):
            _reject_floats(value, f"{where}[{i}]")


def canonical_json(obj: object, indent: int | None = None) -> bytes:
    """
    JSON w jednej, powtarzalnej postaci bajtowej.

    sort_keys      — kolejnosc kluczy nie moze zalezec od kolejnosci wstawiania
    ensure_ascii   — False, zeby polskie znaki nie puchly do \\uXXXX
    separators     — bez spacji, gdy indent=None
    zapis bajtowy  — omija translacje koncow linii w trybie tekstowym na Windowsie
    """
    _reject_floats(obj)
    text = json.dumps(
        obj,
        sort_keys=True,
        ensure_ascii=False,
        indent=indent,
        separators=(",", ":") if indent is None else None,
        allow_nan=False,
    )
    return text.encode("utf-8") + b"\n"
