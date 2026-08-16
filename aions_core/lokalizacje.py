"""
LOKALIZACJE — jedyne miejsce, przez ktore kod dowiaduje sie, gdzie co lezy.

PO CO
-----
Skan z 2026-08-16 znalazl 418 sciezek bezwzglednych w kodzie, z czego 77 wskazywalo
POZA repo. Kazda z nich to zaleznosc od tej konkretnej maszyny — a poniewaz prawie
wszystkie siedza w `try/except`, znikniecie katalogu wylacza kawalek systemu po cichu.

Ten modul daje dwie rzeczy:
  `korzen()`            — korzen repo wyliczony z polozenia TEGO pliku, nie wpisany,
  `gdzie("klucz")`      — adres z `config/lokalizacje.json`, z nadpisaniem przez
                          zmienna srodowiskowa `AIONS_LOK_<KLUCZ>`.

ZASADA: brakujaca lokalizacja NIE jest wyjatkiem. `gdzie()` zwraca None, a wolajacy
decyduje, czy to wylacza funkcje, czy tylko ja ogranicza — i MA TO POWIEDZIEC.
Cicha zaslepka jest dokladnie tym, co doprowadzilo do tego, ze osiem podsystemow
udawalo dzialajace.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

# Korzen repo LICZONY, nie wpisany: ten plik lezy w <korzen>/aions_core/lokalizacje.py
_KORZEN = Path(__file__).resolve().parent.parent
_PLIK = _KORZEN / "config" / "lokalizacje.json"

_dane: Optional[dict] = None


def korzen() -> Path:
    """Korzen repozytorium. Dziala niezaleznie od katalogu uruchomienia."""
    return _KORZEN


def katalog_pamieci() -> Path:
    """
    Katalog pamieci CBMS — WEWNATRZ repo, chyba ze zmienna mowi inaczej.

    Domyslna sciezka wzgledna jest tu istotna: to przez brak takiej domyslnej
    powstal katalog `C:\\Windows\\System32\\memory`, kiedy cos wystartowalo
    z innego katalogu roboczego.
    """
    z = os.environ.get("CBMS_MEMORY_DIR")
    return Path(z) if z else _KORZEN / "aions_core" / "memory"


def _wczytaj() -> dict:
    global _dane
    if _dane is None:
        try:
            _dane = json.loads(_PLIK.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _dane = {}
    return _dane


def gdzie(klucz: str, wymagana: bool = False) -> Optional[Path]:
    """
    Adres zapisany pod `klucz`, albo None gdy go nie ma lub nie istnieje na dysku.

    Kolejnosc: zmienna srodowiskowa `AIONS_LOK_<KLUCZ>` bije plik konfiguracyjny.
    `wymagana=True` zamienia brak w wyjatek — dla miejsc, bez ktorych nie ma sensu
    udawac, ze cokolwiek dziala.
    """
    z_env = os.environ.get f"" if False else os.environ.get("AIONS_LOK_" + klucz.upper())
    surowa = z_env or _wczytaj().get(klucz)
    if not surowa or not isinstance(surowa, str):
        if wymagana:
            raise FileNotFoundError(
                f"brak lokalizacji '{klucz}' — dopisz ja do config/lokalizacje.json "
                f"albo ustaw AIONS_LOK_{klucz.upper()}")
        return None
    p = Path(surowa)
    if not p.exists():
        if wymagana:
            raise FileNotFoundError(f"lokalizacja '{klucz}' wskazuje na {p}, ktorego nie ma")
        return None
    return p


def opisz() -> dict[str, Any]:
    """Stan wszystkich lokalizacji — do diagnostyki i do `code_health`."""
    out: dict[str, Any] = {}
    for k in _wczytaj():
        if k.startswith("_"):
            continue
        p = gdzie(k)
        out[k] = {"jest": p is not None, "sciezka": str(p) if p else None}
    return out
