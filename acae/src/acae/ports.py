"""
ports.py — granica miedzy rdzeniem a swiatem.

Cale I/O siedzi za tymi trzema protokolami. Rdzen (core.py) nie wie, czy pliki
przychodza z dysku, z pamieci, czy z gita — i dlatego da sie go przetestowac bez
dotykania dysku, co jest jedna z bramek M1.

Uzywamy typing.Protocol, nie klas bazowych: adapter nie musi niczego dziedziczyc
ani importowac, wystarczy ze ma zgodne metody. Dzieki temu Reader w tescie to
dziesiec linii nad slownikiem, a nie podklasa z zaslepkami.
"""

from __future__ import annotations

from typing import Mapping, Protocol, Sequence


class Locator(Protocol):
    """Ustala, KTORE pliki wchodza do packa. Tu i tylko tu zyja reguly wykluczania."""

    def list_files(self) -> Sequence[str]:
        """
        Sciezki wzgledne w postaci POSIX, POSORTOWANE porownaniem bajtowym.

        Sortowanie jest kontraktem, nie uprzejmoscia: `scan_dir()` w ts_symbols.py
        (:275-283) go nie ma i kolejnosc bierze z systemu plikow. Na NTFS wychodzi
        stabilnie, ale to wlasnosc NTFS, nie kodu.
        """
        ...

    def skipped(self) -> Sequence[Mapping[str, object]]:
        """
        Pliki odrzucone, kazdy z jawnym powodem z zamknietej listy:
        ignored | binary | too_large | secret | no_grammar | submodule | unreadable.

        Plik nie moze wypasc z zakresu po cichu. `scan_dir()` lyka ValueError
        i plik znika bez sladu (:282-283) — to jest dokladnie ta wlasnosc,
        ktorej tu nie powtarzamy.
        """
        ...


class Reader(Protocol):
    """Dostarcza tresc. Nic wiecej — zadnego listowania, zadnego zapisu."""

    def read(self, rel: str) -> bytes:
        """
        Bajty pliku JUZ ZNORMALIZOWANE przez canon.normalize_source.

        Normalizacja nalezy do brzegu, nie do rdzenia: gdyby rdzen dostawal bajty
        surowe, musialby wiedziec o core.autocrlf i o BOM, czyli o systemie plikow.
        """
        ...


class Store(Protocol):
    """Przyjmuje gotowy artefakt. Rdzen nie wie, gdzie on lezy."""

    def write(self, name: str, data: bytes) -> str:
        """Zapisuje `data` pod logiczna nazwa `name`. Zwraca lokalizacje do raportu."""
        ...
