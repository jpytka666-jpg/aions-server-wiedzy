"""
Scalenie partii opisow (M8) w jeden artefakt `_desc/descriptions.json` + walidacja.

Opisy generuje model, wiec generowanie NIE jest deterministyczne. Uzywanie ich juz jest:
plik powstaje raz, jest commitowany i od tej chwili wchodzi do rankingu jak kazde inne
dane. Ta sama granica co przy modelu M7 — `export_model.py` wolno zalezec od `torch`,
warstwie zapytania nie wolno.

Skrypt ODMAWIA ZAPISU, gdy walidacja nie przejdzie. Artefakt wchodzacy do pomiaru
ma nie powstac wcale, zamiast powstac cicho zepsuty. Pierwszy przebieg M8 pokazal
dlaczego: jeden "opis" byl notatka agenta do siebie ("Stopped at 1 line - file was
already read before in batch") i przeszedlby niezauwazony.

Prowieniencja zapisana w artefakcie: model, data, `pack_hash` zrodla. Bez `pack_hash`
po miesiacu nikt nie odrozni opisow swiezych od opisujacych juz nieistniejacy kod.
"""
import argparse
import datetime
import json
import pathlib
import re

ACAE = pathlib.Path("acae")

# Frazy, ktorymi model mowi o sobie zamiast o pliku. Kazda z nich w pierwszym
# przebiegu albo wystapila, albo jest jej najblizszym sasiadem.
META = re.compile(
    r"(stopped at|already read|as requested|I will now|I'll now|cannot read|"
    r"unable to read|the file list|this batch|per the instructions)",
    re.IGNORECASE,
)
MIN_SLOW = 40          # ponizej tego opis nie niesie tresci...
MIN_SLOW_MARKER = 8    # ...chyba ze plik to pusty znacznik pakietu
MAX_KROTKICH = 15      # ile plikow-znacznikow dopuszczamy, zanim to jest objaw


def wczytaj_partie(katalog):
    opisy, skad, duplikaty = {}, {}, []
    pliki = sorted(katalog.glob("desc_*.json"), key=lambda p: int(p.stem.split("_")[1]))
    for p in pliki:
        dane = json.loads(p.read_text(encoding="utf-8"))
        for sciezka, opis in dane.items():
            if sciezka in opisy:
                duplikaty.append((sciezka, skad[sciezka], p.name))
            opisy[sciezka] = opis
            skad[sciezka] = p.name
    return opisy, [p.name for p in pliki], duplikaty


def main():
    ap = argparse.ArgumentParser(description="Scal partie opisow M8 w jeden artefakt.")
    ap.add_argument("--model", default="claude-haiku-4-5-20251001")
    ap.add_argument("--out", default="descriptions.json")
    args = ap.parse_args()

    katalog = ACAE / "_desc"
    manifest = json.loads((ACAE / "_out" / "manifest.json").read_text(encoding="utf-8"))
    w_packu = {str(f["path"]) for f in manifest["files"]}

    opisy, partie, duplikaty = wczytaj_partie(katalog)
    braki = sorted(w_packu - set(opisy))
    nadmiar = sorted(set(opisy) - w_packu)
    nieczytelne = sorted(k for k, v in opisy.items() if v.strip().upper() == "UNREADABLE")
    meta = sorted(k for k, v in opisy.items() if META.search(v))
    wyciek = sorted(k for k in opisy if k.startswith("acae/tests"))

    dlugosci = {k: len(v.split()) for k, v in opisy.items()}
    krotkie = sorted(k for k, n in dlugosci.items() if n < MIN_SLOW)
    urwane = sorted(k for k, n in dlugosci.items() if n < MIN_SLOW_MARKER)

    posortowane = sorted(dlugosci.values())
    mediana = posortowane[len(posortowane) // 2] if posortowane else 0

    print(f"partie wczytane   : {len(partie)} ({', '.join(partie)})")
    print(f"opisow            : {len(opisy)}")
    print(f"plikow w packu    : {len(w_packu)}")
    print()
    print(f"slow na opis      : min {posortowane[0] if posortowane else 0}"
          f"  mediana {mediana}  max {posortowane[-1] if posortowane else 0}")
    print(f"opisow >= 100 slow: {sum(1 for n in posortowane if n >= 100)} z {len(posortowane)}")
    print()

    bledy = []
    if braki:
        bledy.append(f"brak opisu dla {len(braki)} plikow: {braki[:5]}")
    if nadmiar:
        bledy.append(f"opis dla {len(nadmiar)} plikow spoza packa: {nadmiar[:5]}")
    if duplikaty:
        bledy.append(f"{len(duplikaty)} sciezek opisanych dwukrotnie: {duplikaty[:3]}")
    if nieczytelne:
        bledy.append(f"{len(nieczytelne)} plikow UNREADABLE: {nieczytelne}")
    if meta:
        bledy.append(f"{len(meta)} opisow zawiera meta-tekst agenta: {meta}")
    if wyciek:
        bledy.append(f"WYCIEK: opisano pliki ze zbioru testowego: {wyciek}")
    if urwane:
        bledy.append(f"{len(urwane)} opisow ponizej {MIN_SLOW_MARKER} slow (urwane): {urwane}")
    if len(krotkie) > MAX_KROTKICH:
        bledy.append(
            f"{len(krotkie)} opisow ponizej {MIN_SLOW} slow przy dopuszczalnych "
            f"{MAX_KROTKICH} — to nie sa juz same puste znaczniki: {krotkie[:8]}"
        )

    if bledy:
        print("WALIDACJA NIE PRZESZLA — artefakt NIE zostal zapisany:")
        for b in bledy:
            print(f"  * {b}")
        raise SystemExit(1)

    if krotkie:
        print(f"UWAGA (dopuszczone): {len(krotkie)} opisow ponizej {MIN_SLOW} slow "
              f"— sprawdz, czy to puste znaczniki pakietu:")
        for k in krotkie:
            print(f"    {dlugosci[k]:>3} slow  {k}")
        print()

    artefakt = {
        "provenance": {
            "model": args.model,
            "generated_at": datetime.datetime.now(datetime.timezone.utc)
            .replace(microsecond=0)
            .isoformat(),
            "pack_hash": manifest["pack_hash"],
            "batches": partie,
            "count": len(opisy),
        },
        "descriptions": dict(sorted(opisy.items())),
    }
    cel = katalog / args.out
    cel.write_text(
        json.dumps(artefakt, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"WALIDACJA PRZESZLA — zapisano {cel} ({cel.stat().st_size} bajtow)")
    print(f"pack_hash zrodla  : {manifest['pack_hash']}")


if __name__ == "__main__":
    main()
