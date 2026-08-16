"""
SONDA IMPORTOW — sprawdza, czy podsystemy schowane za `except ImportError` naprawde istnieja.

PO CO
-----
W AIONS jest kilkadziesiat miejsc w tym ksztalcie:

    try:
        from math_solver import solve as math_solve
    except ImportError:
        def math_solve(q): return (False, None)

To jest poprawny wzorzec "dziala tez bez tej biblioteki". Ale ma jedna wlasciwosc:
gdy import PADA, podsystem znika po cichu, a zaslepka grzecznie odpowiada "nie umiem".
Nic sie nie psuje, nic nie krzyczy — po prostu funkcja, ktora miala dzialac, nie dziala.
Zadna analiza statyczna tego nie zobaczy, bo statycznie kod jest w porzadku.

CO ROBI TA SONDA
----------------
Znajduje kazdy taki import i sprawdza, czy modul da sie ZNALEZC na sciezce, ktora
ma plik go importujacy. Uzywamy `find_spec`, ktore modul LOKALIZUJE, ale go NIE URUCHAMIA.
Roznica jest istotna: uruchomienie modulu AIONS wykonaloby jego kod na starcie
(wydruki, polaczenia, wczytywanie modeli), a sonda ma tylko patrzec, nie dzialac.

CZEGO NIE ZOBACZY
-----------------
Modulu, ktory sie znajduje, ale wybucha w srodku przy imporcie. Zeby to wykryc,
trzeba go naprawde uruchomic — swiadomie tego nie robimy. Wynik "ZNALEZIONY"
znaczy "plik jest tam, gdzie kod go szuka", a nie "na pewno dziala".
"""

import argparse
import ast
import importlib.util
import json
import pathlib
import sys
from collections import defaultdict

POMIJANE = {".git", "__pycache__", "venv", ".venv", "node_modules", "_backups",
            "bundle-staging", "site-packages", ".pytest_cache"}

LAPANE = {"ImportError", "ModuleNotFoundError", "Exception"}


def pliki_py(root: pathlib.Path, katalogi):
    for nazwa in katalogi:
        base = root / nazwa
        if not base.is_dir():
            continue
        for p in base.rglob("*.py"):
            if not any(part in POMIJANE for part in p.parts):
                yield p


def typy_handlera(h: ast.ExceptHandler) -> set[str]:
    if h.type is None:
        return {"GOLY"}
    wezly = h.type.elts if isinstance(h.type, ast.Tuple) else [h.type]
    out = set()
    for w in wezly:
        if isinstance(w, ast.Name):
            out.add(w.id)
        elif isinstance(w, ast.Attribute):
            out.add(w.attr)
    return out or {"?"}


def opcjonalne_importy(root: pathlib.Path, katalogi):
    """(plik, linia, nazwa_modulu, czy_wzgledny) dla kazdego importu w oslonie try/except."""
    for p in pliki_py(root, katalogi):
        rel = p.relative_to(root).as_posix()
        try:
            drzewo = ast.parse(p.read_bytes(), filename=rel)
        except (SyntaxError, ValueError):
            continue
        for w in ast.walk(drzewo):
            if not isinstance(w, ast.Try):
                continue
            if not any(typy_handlera(h) & LAPANE or typy_handlera(h) == {"GOLY"}
                       for h in w.handlers):
                continue
            for x in ast.walk(ast.Module(body=w.body, type_ignores=[])):
                if isinstance(x, ast.Import):
                    for a in x.names:
                        yield rel, x.lineno, a.name, False
                elif isinstance(x, ast.ImportFrom):
                    if x.level:                      # `from . import y` — pomijamy
                        continue
                    if x.module:
                        yield rel, x.lineno, x.module, False


def znajdz(modul: str, sciezki: list[str]) -> bool:
    """
    Czy modul da sie ZLOKALIZOWAC. Bez uruchamiania go.

    `find_spec` dla nazwy z kropka musi zaimportowac pakiety nadrzedne, wiec dla
    takich nazw sprawdzamy tylko pierwszy czlon — bezpieczniej przeoczyc niz
    uruchomic pol AIONS-a przy audycie.
    """
    korzen = modul.split(".")[0]
    stare = sys.path[:]
    try:
        sys.path[:] = sciezki + stare
        try:
            return importlib.util.find_spec(korzen) is not None
        except (ImportError, ValueError, AttributeError):
            return False
    finally:
        sys.path[:] = stare


def main():
    ap = argparse.ArgumentParser(description="Sonda opcjonalnych importow AIONS.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--dirs", nargs="*",
                    default=["aions_core", "control_plane", "server", "scripts", "mcpServers"])
    ap.add_argument("--json-out", default="")
    args = ap.parse_args()

    root = pathlib.Path(args.root).resolve()
    brak, jest = [], []
    for rel, linia, modul, _ in opcjonalne_importy(root, args.dirs):
        # Sciezka, jaka realnie ma plik uruchomiony jako skrypt: jego wlasny katalog
        # plus korzen repo. Tak startuja serwery AIONS.
        katalog = str((root / rel).parent)
        (jest if znajdz(modul, [katalog, str(root)]) else brak).append(
            {"plik": rel, "linia": linia, "modul": modul})

    wg_modulu = defaultdict(list)
    for x in brak:
        wg_modulu[x["modul"]].append(f"{x['plik']}:{x['linia']}")

    print(f"opcjonalnych importow: {len(jest) + len(brak)}   "
          f"ZNALEZIONE {len(jest)}   BRAKUJACE {len(brak)}")
    print()
    if wg_modulu:
        print("=" * 78)
        print("MODULY, KTORYCH NIE MA — podsystem cicho zastapiony zaslepka")
        print("=" * 78)
        for modul in sorted(wg_modulu, key=lambda m: (-len(wg_modulu[m]), m)):
            miejsca = wg_modulu[modul]
            print(f"  {modul}   ({len(miejsca)} miejsc)")
            for m in miejsca[:4]:
                print(f"      {m}")
            if len(miejsca) > 4:
                print(f"      ... i {len(miejsca) - 4} wiecej")

    if args.json_out:
        (root / args.json_out).write_text(
            json.dumps({"brakujace": brak, "znalezione": jest},
                       ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8", newline="\n")
        print(f"\npelny wynik: {args.json_out}")


if __name__ == "__main__":
    sys.exit(main())
