"""
AUDYT STATYCZNY — szuka wzorcow awarii, ktore juz raz nas ugryzly. Zero tokenow, zero modeli.

SKAD TE KONKRETNE SPRAWDZENIA
-----------------------------
Nie sa wymyslone. Kazde odpowiada bledowi znalezionemu recznie 2026-08-15/16 w AIONS:

  A. parametr przyjmowany i NIGDY nieuzyty
     -> `crla_core.simulate_candidate(cbms, query, cand)` ignorowal `cand`, przez co
        osmiu "roznych" kandydatow turnieju liczylo dokladnie to samo.

  B. `except: pass` / `except Exception: pass` — blad polkniety bez sladu
     -> `log_exchange` wolany z trzema argumentami zamiast czterech; TypeError znikal,
        a katalog rozmow po prostu nigdy nie powstal.

  C. import, ktory nigdy nie jest uzyty
     -> `pocket_qc` i `stylist` importowane w obu serwerach CBMS i niewolane ani razu.

  D. wywolanie funkcji z repo z inna liczba argumentow albo nieznanym slowem kluczowym
     -> `run_crla(query, cbms, FACTS, seed=..., candidates=...)` wobec sygnatury
        `run_crla(cbms, query, seed=123, n_candidates=8)`. Endpoint zwracal 500 zawsze.

ZASADA: LEPIEJ PRZEOCZYC NIZ NAKLAMAC
-------------------------------------
Kazde sprawdzenie jest CELOWO zachowawcze. Sprawdzenie D dziala tylko dla funkcji
zdefiniowanych w repo DOKLADNIE RAZ — przy dwoch definicjach tej samej nazwy nie da sie
staticznie rozstrzygnac, ktora jest wolana, wiec milczymy. Lepiej zglosic dziesiec
prawdziwych niz sto, z ktorych polowa jest zmyslona: raport, ktoremu nie mozna ufac,
nie zostanie przeczytany.

Podobnie A pomija `self`, `cls`, `_`, parametry zaczynajace sie od `_`, oraz cialo
`pass`/`...`/sam docstring (protokoly, zaslepki, klasy bazowe).
"""

import argparse
import ast
import json
import pathlib
import sys
from collections import defaultdict

DOMYSLNE_KATALOGI = ("aions_core", "control_plane", "server", "scripts", "mcpServers")
POMIJANE = {".git", "__pycache__", "venv", ".venv", "node_modules", "_backups",
            "bundle-staging", "site-packages", ".pytest_cache"}


def pliki_py(root: pathlib.Path, katalogi):
    for nazwa in katalogi:
        base = root / nazwa
        if not base.is_dir():
            continue
        for p in base.rglob("*.py"):
            if any(part in POMIJANE for part in p.parts):
                continue
            yield p


def cialo_puste(fn: ast.FunctionDef) -> bool:
    """Zaslepka: sam `pass`, `...`, docstring albo `raise NotImplementedError`."""
    ciala = [w for w in fn.body if not (isinstance(w, ast.Expr) and isinstance(w.value, ast.Constant))]
    if not ciala:
        return True
    if len(ciala) == 1:
        w = ciala[0]
        if isinstance(w, ast.Pass):
            return True
        if isinstance(w, ast.Raise):
            return True
    return False


def zbierz_definicje(drzewa):
    """Nazwa funkcji -> lista (plik, linia, sygnatura). Tylko funkcje modulowe."""
    defs = defaultdict(list)
    for sciezka, drzewo in drzewa.items():
        for w in ast.walk(drzewo):
            if isinstance(w, ast.FunctionDef) and not any(
                isinstance(r, ast.ClassDef) for r in getattr(w, "_rodzice", [])
            ):
                a = w.args
                defs[w.name].append({
                    "plik": sciezka, "linia": w.lineno,
                    "pozycyjne": [x.arg for x in (a.posonlyargs + a.args)],
                    "domyslne": len(a.defaults),
                    "kw_only": [x.arg for x in a.kwonlyargs],
                    "vararg": a.vararg is not None,
                    "kwarg": a.kwarg is not None,
                })
    return defs


def oznacz_rodzicow(drzewo):
    for rodzic in ast.walk(drzewo):
        for dziecko in ast.iter_child_nodes(rodzic):
            dziecko._rodzice = getattr(rodzic, "_rodzice", []) + [rodzic]


def main():
    ap = argparse.ArgumentParser(description="Audyt statyczny wzorcow awarii w AIONS.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--dirs", nargs="*", default=list(DOMYSLNE_KATALOGI))
    ap.add_argument("--json-out", default="")
    args = ap.parse_args()

    root = pathlib.Path(args.root).resolve()
    drzewa, bledy_skladni = {}, []
    for p in pliki_py(root, args.dirs):
        rel = p.relative_to(root).as_posix()
        try:
            drzewo = ast.parse(p.read_bytes(), filename=rel)
        except (SyntaxError, ValueError) as e:
            bledy_skladni.append({"plik": rel, "blad": str(e)})
            continue
        oznacz_rodzicow(drzewo)
        drzewa[rel] = drzewo

    defs = zbierz_definicje(drzewa)
    jednoznaczne = {n: d[0] for n, d in defs.items() if len(d) == 1}

    A, B, C, D = [], [], [], []

    for rel, drzewo in drzewa.items():
        uzyte = {w.id for w in ast.walk(drzewo) if isinstance(w, ast.Name)}
        uzyte |= {w.attr for w in ast.walk(drzewo) if isinstance(w, ast.Attribute)}

        for w in ast.walk(drzewo):
            # --- C: import nigdy nieuzyty
            if isinstance(w, (ast.Import, ast.ImportFrom)):
                for alias in w.names:
                    nazwa = (alias.asname or alias.name).split(".")[0]
                    if nazwa == "*" or nazwa.startswith("_"):
                        continue
                    if nazwa not in uzyte:
                        C.append({"plik": rel, "linia": w.lineno, "nazwa": nazwa})

            # --- B: polkniety wyjatek
            if isinstance(w, ast.ExceptHandler):
                tresc = [x for x in w.body if not isinstance(x, ast.Pass)]
                if not tresc:
                    typ = getattr(w.type, "id", None) or (
                        getattr(getattr(w.type, "attr", None), "__str__", lambda: "")()
                        if w.type is not None else "GOLY")
                    B.append({"plik": rel, "linia": w.lineno, "typ": str(typ or "GOLY")})

            # --- A: parametr przyjmowany i nieuzyty
            if isinstance(w, ast.FunctionDef) and not cialo_puste(w):
                nazwy_w_ciele = {n.id for x in w.body for n in ast.walk(x)
                                 if isinstance(n, ast.Name)}
                nazwy_w_ciele |= {n.attr for x in w.body for n in ast.walk(x)
                                  if isinstance(n, ast.Attribute)}
                a = w.args
                for arg in a.posonlyargs + a.args + a.kwonlyargs:
                    if arg.arg in ("self", "cls", "_") or arg.arg.startswith("_"):
                        continue
                    if arg.arg not in nazwy_w_ciele:
                        A.append({"plik": rel, "linia": w.lineno,
                                  "funkcja": w.name, "parametr": arg.arg})

            # --- D: wywolanie niezgodne z sygnatura
            if isinstance(w, ast.Call) and isinstance(w.func, ast.Name):
                # Rozstrzygamy WYLACZNIE nazwy widoczne w TYM pliku: zdefiniowane lokalnie
                # albo jawnie zaimportowane. Bez tego `set()` z biblioteki standardowej
                # dopasowywal sie do metody `set` z `world_state.py` i produkowal
                # dziesiatki zmyslonych zgloszen. Lepiej przeoczyc niz naklamac.
                if w.func.id not in widoczne[rel]:
                    continue
                d = jednoznaczne.get(w.func.id)
                if not d:
                    continue
                if any(isinstance(x, ast.Starred) for x in w.args) or \
                        any(k.arg is None for k in w.keywords):
                    continue          # *args / **kwargs w wywolaniu — nie rozstrzygamy
                poz = d["pozycyjne"]
                nadane = {k.arg for k in w.keywords}
                obowiazkowe = len(poz) - d["domyslne"]
                powod = None
                if not d["vararg"] and len(w.args) > len(poz):
                    powod = f"podano {len(w.args)} pozycyjnych, funkcja przyjmuje {len(poz)}"
                elif not d["kwarg"]:
                    nieznane = nadane - set(poz) - set(d["kw_only"])
                    if nieznane:
                        powod = f"nieznane slowa kluczowe: {sorted(nieznane)}"
                    else:
                        kolizja = {poz[i] for i in range(min(len(w.args), len(poz)))} & nadane
                        if kolizja:
                            powod = f"argument podany dwa razy: {sorted(kolizja)}"
                        elif len(w.args) + len(nadane & set(poz)) < obowiazkowe:
                            powod = (f"za malo argumentow: {len(w.args) + len(nadane & set(poz))} "
                                     f"wobec wymaganych {obowiazkowe}")
                if powod:
                    D.append({"plik": rel, "linia": w.lineno, "wolane": w.func.id,
                              "definicja": f"{d['plik']}:{d['linia']}", "powod": powod})

    print(f"przeanalizowano {len(drzewa)} plikow .py"
          + (f", {len(bledy_skladni)} nie parsuje sie" if bledy_skladni else ""))
    for e in bledy_skladni[:5]:
        print(f"   NIE PARSUJE: {e['plik']}")
    print()
    print(f"D. WYWOLANIE NIEZGODNE Z SYGNATURA        : {len(D):>4}   <- najgrozniejsze")
    print(f"B. WYJATEK POLKNIETY BEZ SLADU            : {len(B):>4}")
    print(f"A. PARAMETR PRZYJMOWANY I NIEUZYWANY      : {len(A):>4}")
    print(f"C. IMPORT NIGDY NIEUZYTY                  : {len(C):>4}")
    print()
    if D:
        print("=" * 74)
        print("D — WYWOLANIA, KTORE NIE MOGA ZADZIALAC")
        print("=" * 74)
        for x in D:
            print(f"  {x['plik']}:{x['linia']}  ->  {x['wolane']}()")
            print(f"      {x['powod']}")
            print(f"      definicja: {x['definicja']}")

    if args.json_out:
        pathlib.Path(args.json_out).write_text(
            json.dumps({"D_sygnatury": D, "B_polkniete": B, "A_nieuzyte_parametry": A,
                        "C_martwe_importy": C, "bledy_skladni": bledy_skladni},
                       ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8", newline="\n")
        print(f"\npelny raport: {args.json_out}")


if __name__ == "__main__":
    sys.exit(main())
