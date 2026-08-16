"""
TRIAZ AUDYTU — oddziela awarie od normalnej praktyki. Nadal zero tokenow i zero modeli.

PO CO
-----
`audit_calls.py` zwrocil 88 polknietych wyjatkow i 58 nieuzywanych parametrow. Wiekszosc
z nich jest niegrozna. Czytanie tego recznie kosztuje wiecej niz jest warte, a wyslanie
calosci do modelu kosztuje jeszcze wiecej. Oba pytania da sie jednak zadac statycznie:

  B. POLKNIETY WYJATEK — grozny jest ten, ktory otacza ZAPIS.
     Blad `log_exchange` byl dokladnie taki: TypeError znikal w `except: pass`, a katalog
     rozmow nigdy nie powstawal. Polkniecie wokol `import` (zaleznosc opcjonalna) albo
     wokol `close`/`shutdown` (sprzatanie) jest normalna praktyka.
     Rozstrzygamy po nazwach funkcji wolanych w bloku `try`.

  A. NIEUZYWANY PARAMETR — grozny jest ten, ktory KTOS NAPRAWDE PODAJE.
     `simulate_candidate(cbms, query, cand)` ignorowal `cand`, ale wolajacy podawal
     osmiu roznych kandydatow i wierzyl, ze to cokolwiek zmienia. Parametr, ktorego
     nikt nigdy nie podaje, to martwa sygnatura — brzydka, nie zepsuta.

ZASADA TA SAMA CO W AUDYCIE: lepiej przeoczyc niz naklamac. Kazda watpliwosc laduje
w kubelku NISKIE, nie w RYZYKO. Raport, w ktorym polowa pozycji jest zmyslona,
nie zostanie przeczytany.
"""

import argparse
import ast
import json
import pathlib
import re
import sys
from collections import defaultdict

POMIJANE = {".git", "__pycache__", "venv", ".venv", "node_modules", "_backups",
            "bundle-staging", "site-packages", ".pytest_cache"}

# Czasowniki zapisu — jesli w bloku `try` stoi cokolwiek z tej listy, polkniecie
# wyjatku znaczy "dane mogly nie dojsc i nikt sie nie dowie".
ZAPIS = re.compile(
    r"(save|write|store|commit|insert|persist|upsert|publish|append|dump|flush|"
    r"log_|_log|record|register|emit|index|send|post|put|mkdir|makedirs|rename|replace)",
    re.I)

# Sprzatanie i zamykanie — polkniecie jest tu norma, bo blad przy zamykaniu i tak
# niczego nie ratuje.
SPRZATANIE = re.compile(r"(close|shutdown|terminate|kill|join|unlink|rmtree|cleanup|"
                        r"disconnect|release|cancel)", re.I)

# Wyjatki od zaleznosci opcjonalnych. `except ImportError: pass` to wzorzec
# "dziala tez bez tej biblioteki", a nie zamiatanie bledu.
OPCJONALNE = {"ImportError", "ModuleNotFoundError", "StopIteration", "StopAsyncIteration"}


def pliki_py(root: pathlib.Path, katalogi):
    for nazwa in katalogi:
        base = root / nazwa
        if not base.is_dir():
            continue
        for p in base.rglob("*.py"):
            if not any(part in POMIJANE for part in p.parts):
                yield p


def nazwy_wolane(wezel) -> set[str]:
    """Nazwy funkcji wolanych gdziekolwiek w poddrzewie — i `f()`, i `x.f()`."""
    out = set()
    for w in ast.walk(wezel):
        if isinstance(w, ast.Call):
            if isinstance(w.func, ast.Name):
                out.add(w.func.id)
            elif isinstance(w.func, ast.Attribute):
                out.add(w.func.attr)
    return out


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


def triaz_wyjatkow(drzewa) -> list[dict]:
    """Kazdy `except ...: pass` dostaje kubelek na podstawie tresci bloku `try`."""
    wynik = []
    for rel, drzewo in drzewa.items():
        for w in ast.walk(drzewo):
            if not isinstance(w, ast.Try):
                continue
            wolane = nazwy_wolane(ast.Module(body=w.body, type_ignores=[]))
            zapisy = sorted(n for n in wolane if ZAPIS.search(n))
            sprzat = sorted(n for n in wolane if SPRZATANIE.search(n))
            for h in w.handlers:
                if [x for x in h.body if not isinstance(x, ast.Pass)]:
                    continue                     # cos robi — nie nasz przypadek
                typy = typy_handlera(h)
                if typy & OPCJONALNE:
                    kubelek, powod = "NISKIE", "zaleznosc opcjonalna"
                elif zapisy and not (sprzat and not zapisy):
                    kubelek, powod = "RYZYKO", f"w bloku try stoi zapis: {zapisy[:3]}"
                elif sprzat:
                    kubelek, powod = "NISKIE", f"sprzatanie: {sprzat[:3]}"
                elif not wolane:
                    kubelek, powod = "NISKIE", "w bloku try nie ma zadnego wywolania"
                else:
                    kubelek, powod = "SREDNIE", f"wywolania: {sorted(wolane)[:4]}"
                wynik.append({"plik": rel, "linia": h.lineno, "typy": sorted(typy),
                              "kubelek": kubelek, "powod": powod})
    return wynik


def triaz_parametrow(drzewa, nieuzyte) -> list[dict]:
    """
    Nieuzywany parametr wazy tyle, ile wierzy w niego wolajacy.

    Szukamy w CALYM repo wywolan o tej nazwie funkcji i sprawdzamy, czy ktokolwiek
    podaje ten parametr — pozycyjnie na jego miejscu albo po nazwie. Metody
    rozpoznajemy po `x.nazwa(...)`, bo inaczej przeoczylibysmy caly CRLA.
    """
    # nazwa funkcji -> lista (liczba pozycyjnych, zbior slow kluczowych) z wywolan
    wywolania = defaultdict(list)
    for _rel, drzewo in drzewa.items():
        for w in ast.walk(drzewo):
            if not isinstance(w, ast.Call):
                continue
            nazwa = (w.func.id if isinstance(w.func, ast.Name)
                     else w.func.attr if isinstance(w.func, ast.Attribute) else None)
            if nazwa:
                wywolania[nazwa].append((len(w.args), {k.arg for k in w.keywords if k.arg}))

    # nazwa funkcji -> lista pozycji parametrow (zeby wiedziec, ktory indeks to nasz)
    pozycje = {}
    for _rel, drzewo in drzewa.items():
        for w in ast.walk(drzewo):
            if isinstance(w, (ast.FunctionDef, ast.AsyncFunctionDef)):
                a = w.args
                pozycje.setdefault(w.name, []).append(
                    [x.arg for x in (a.posonlyargs + a.args)])

    wynik = []
    for poz in nieuzyte:
        fn, par = poz["funkcja"], poz["parametr"]
        wolania = wywolania.get(fn, [])
        listy = pozycje.get(fn, [])
        # indeks parametru; przy metodach `self` jest pierwszy, a wolajacy go nie podaje
        idx = None
        for lst in listy:
            if par in lst:
                idx = lst.index(par)
                if lst and lst[0] in ("self", "cls"):
                    idx -= 1
                break
        podany = False
        for n_poz, kw in wolania:
            if par in kw or (idx is not None and idx >= 0 and n_poz > idx):
                podany = True
                break
        if not wolania:
            kubelek, powod = "NISKIE", "funkcji nikt w repo nie wola"
        elif podany:
            kubelek, powod = "RYZYKO", f"wolajacy PODAJE ten argument ({len(wolania)} wywolan)"
        else:
            kubelek, powod = "NISKIE", "nikt nigdy nie podaje tego argumentu"
        wynik.append({**poz, "kubelek": kubelek, "powod": powod})
    return wynik


def main():
    ap = argparse.ArgumentParser(description="Triaz wynikow audytu statycznego.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--audit", default="acae/_out/audit.json")
    ap.add_argument("--dirs", nargs="*",
                    default=["aions_core", "control_plane", "server", "scripts", "mcpServers"])
    ap.add_argument("--json-out", default="")
    args = ap.parse_args()

    root = pathlib.Path(args.root).resolve()
    surowy = json.loads((root / args.audit).read_text(encoding="utf-8"))

    drzewa = {}
    for p in pliki_py(root, args.dirs):
        rel = p.relative_to(root).as_posix()
        try:
            drzewa[rel] = ast.parse(p.read_bytes(), filename=rel)
        except (SyntaxError, ValueError):
            continue

    B = triaz_wyjatkow(drzewa)
    A = triaz_parametrow(drzewa, surowy["A_nieuzyte_parametry"])

    def licz(xs):
        c = defaultdict(int)
        for x in xs:
            c[x["kubelek"]] += 1
        return c

    cb, ca = licz(B), licz(A)
    print(f"POLKNIETE WYJATKI   {len(B):>4}  ->  "
          f"RYZYKO {cb['RYZYKO']}   SREDNIE {cb['SREDNIE']}   NISKIE {cb['NISKIE']}")
    print(f"NIEUZYTE PARAMETRY  {len(A):>4}  ->  "
          f"RYZYKO {ca['RYZYKO']}   NISKIE {ca['NISKIE']}")
    print()
    print("=" * 78)
    print("RYZYKO — POLKNIETY WYJATEK WOKOL ZAPISU")
    print("=" * 78)
    for x in [y for y in B if y["kubelek"] == "RYZYKO"]:
        print(f"  {x['plik']}:{x['linia']}  except {'/'.join(x['typy'])}")
        print(f"      {x['powod']}")
    print()
    print("=" * 78)
    print("RYZYKO — PARAMETR IGNOROWANY, CHOC WOLAJACY GO PODAJE")
    print("=" * 78)
    for x in [y for y in A if y["kubelek"] == "RYZYKO"]:
        print(f"  {x['plik']}:{x['linia']}  {x['funkcja']}() ignoruje `{x['parametr']}`")
        print(f"      {x['powod']}")

    if args.json_out:
        (root / args.json_out).write_text(
            json.dumps({"B_wyjatki": B, "A_parametry": A}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8", newline="\n")
        print(f"\npelny triaz: {args.json_out}")


if __name__ == "__main__":
    sys.exit(main())
