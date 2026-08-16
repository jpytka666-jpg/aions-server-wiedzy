"""
SKANER SCIEZEK NA SZTYWNO — gdzie kod siega poza repo.

PO CO
-----
System jest „porozpierdalany" nie dlatego, ze pliki leza w wielu miejscach — kopie
zapasowe moga lezec, gdzie chca. Jest porozpierdalany dlatego, ze KOD SIEGA NA SZTYWNO
do katalogow poza repo. Kazda taka sciezka to zaleznosc od maszyny: przeniesienie repo,
przelaczenie dysku albo skasowanie „starego folderu" wylacza kawalek systemu — po cichu,
bo prawie zawsze siedzi to w `try/except`.

Przyklad, ktory sprowokowal ten skaner:
    sys.path.insert(0, r"E:\\AI DEVELOPMENT\\WORK SPACE\\IMPORT FROM _F")

CO ROZROZNIA
------------
- **ZYWA**  — sciezka istnieje na dysku i lezy POZA repo. Prawdziwa zaleznosc zewnetrzna.
- **MARTWA**— sciezka nie istnieje. Kod juz z niej nie korzysta, tylko o tym nie wie.
- **WEWN.** — wskazuje do wnetrza repo. Da sie zamienic na wzgledna bez przenoszenia.

Sam skaner NIE przenosi i NIE zmienia niczego. Ma dac liste do decyzji.
"""

import argparse
import ast
import json
import pathlib
import re
import sys
from collections import defaultdict

POMIJANE = {".git", "__pycache__", "venv", ".venv", "node_modules",
            "site-packages", ".pytest_cache",
            # `bundle-staging` to KOPIA calego repo przygotowana do spakowania.
            # Bez tego skaner mieli te same pliki drugi raz i trwa minutami.
            "bundle-staging", "_backups", "backups", "_out", "_desc"}

# Litera dysku + dwukropek + separator. Lapie i `C:\x`, i `C:/x`.
SCIEZKA = re.compile(r"^[A-Za-z]:[\\/]")


def pliki(root: pathlib.Path, katalogi, rozszerzenia):
    for nazwa in katalogi:
        base = root / nazwa
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if p.suffix.lower() not in rozszerzenia:
                continue
            if any(cz in POMIJANE for cz in p.parts):
                continue
            yield p


def literaly_py(sciezka: pathlib.Path, rel: str):
    """Kazdy literal tekstowy wygladajacy na sciezke bezwzgledna, z numerem linii."""
    try:
        drzewo = ast.parse(sciezka.read_bytes(), filename=rel)
    except (SyntaxError, ValueError):
        return
    for w in ast.walk(drzewo):
        if isinstance(w, ast.Constant) and isinstance(w.value, str):
            if SCIEZKA.match(w.value.strip()):
                yield w.lineno, w.value.strip()


def literaly_tekst(sciezka: pathlib.Path):
    """Dla json/toml/ps1 — po linii, bo skladni nie parsujemy."""
    try:
        tresc = sciezka.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return
    for nr, linia in enumerate(tresc.splitlines(), 1):
        for kandydat in re.findall(r'["\']([A-Za-z]:[\\/][^"\']{2,160})["\']', linia):
            yield nr, kandydat


def main() -> int:
    ap = argparse.ArgumentParser(description="Sciezki na sztywno w kodzie AIONS.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--dirs", nargs="*",
                    default=["aions_core", "control_plane", "server", "scripts",
                             "mcpServers", "runtime", "acae"])
    ap.add_argument("--json-out", default="")
    args = ap.parse_args()

    root = pathlib.Path(args.root).resolve()
    znaleziska = []

    for p in pliki(root, args.dirs, {".py"}):
        rel = p.relative_to(root).as_posix()
        for nr, tekst in literaly_py(p, rel):
            znaleziska.append({"plik": rel, "linia": nr, "sciezka": tekst, "rodzaj": "py"})
    for p in pliki(root, args.dirs, {".json", ".toml", ".ps1", ".bat", ".cmd"}):
        rel = p.relative_to(root).as_posix()
        for nr, tekst in literaly_tekst(p):
            znaleziska.append({"plik": rel, "linia": nr, "sciezka": tekst, "rodzaj": "config"})

    korzen_txt = str(root).lower()
    for z in znaleziska:
        s = z["sciezka"]
        try:
            istnieje = pathlib.Path(s).exists()
        except OSError:
            istnieje = False
        wewnatrz = s.lower().replace("/", "\\").startswith(korzen_txt.replace("/", "\\"))
        z["istnieje"] = istnieje
        z["stan"] = "WEWN" if wewnatrz else ("ZYWA" if istnieje else "MARTWA")

    licz = defaultdict(int)
    for z in znaleziska:
        licz[z["stan"]] += 1

    print(f"sciezek bezwzglednych w kodzie: {len(znaleziska)}")
    print(f"   ZYWA   (istnieje, POZA repo — prawdziwa zaleznosc): {licz['ZYWA']}")
    print(f"   MARTWA (nie istnieje — kod o tym nie wie)         : {licz['MARTWA']}")
    print(f"   WEWN   (wskazuje do repo — do uwzglednienia)      : {licz['WEWN']}")

    for stan, naglowek in (("ZYWA", "ZALEZNOSCI POZA REPO — te trzeba wciagnac do srodka"),
                           ("MARTWA", "SCIEZKI DO NICZEGO — kod siega tam, gdzie nic nie ma"),
                           ("WEWN", "WSKAZUJA DO REPO — wystarczy zamienic na wzgledne")):
        poz = [z for z in znaleziska if z["stan"] == stan]
        if not poz:
            continue
        print()
        print("=" * 78)
        print(stan + " — " + naglowek)
        print("=" * 78)
        for z in poz[:40]:
            print(f"  {z['plik']}:{z['linia']}")
            print(f"      {z['sciezka']}")
        if len(poz) > 40:
            print(f"  ... i {len(poz) - 40} wiecej")

    if args.json_out:
        (root / args.json_out).write_text(
            json.dumps({"znaleziska": znaleziska}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8", newline="\n")
        print(f"\npelny wynik: {args.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
