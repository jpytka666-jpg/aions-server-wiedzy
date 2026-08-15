"""
Scalenie dziedzin i przypisan (M11) w jeden artefakt `_desc/domains.json` + walidacja.

Ten sam wzorzec co `build_descriptions.py`: skrypt ODMAWIA ZAPISU, gdy cokolwiek sie nie
zgadza. Artefakt wchodzacy do pomiaru ma nie powstac wcale, zamiast powstac cicho zepsuty.

Sprawdzenia sa dobrane pod konkretne tryby awarii, ktore juz raz nas kosztowaly czas:

* **pokrycie** — wszystkie 169 plikow packa maja polke. Brak choc jednego znaczy, ze
  ktorys agent urwal robote, a pomiar liczylby na niepelnym zbiorze.
* **rozmiar dziedziny** — zaden dzial nie moze urosnac ponad `MAX_W_DZIEDZINIE`.
  M6 przegral dokladnie na tym: „zakres" na 139 ze 169 plikow nie zawezal niczego,
  a ja odczytalem z tego wnioski, do ktorych ten pomiar nie uprawnial. Prerejestracja
  M11 mowi wprost: jesli zawezenie zostawia ponad polowe, mechanizm jest nieuruchomiony.
  Lepiej wylapac to TUTAJ niz po pomiarze.
* **dziedzina pusta** — dzial bez plikow to dzial, ktory moze przyciagnac pytanie
  i nie miec czym odpowiedziec. Najgorszy mozliwy rodzaj polki.
* **nieznane `id`** — przypisanie do dziedziny spoza listy znaczy, ze ktos ja wymyslil.

Prowieniencja: model, data, `pack_hash` packa oraz hash korpusu opisow, na ktorym
dziedziny powstaly. Bez tego drugiego nie da sie pozniej powiedziec, czy dziedziny
opisuja te same streszczenia, ktore dzis mamy.
"""
import argparse
import datetime
import json
import pathlib
from collections import Counter

ACAE = pathlib.Path("acae")

MAX_W_DZIEDZINIE = 25   # patrz naglowek — prog wynika z prerejestracji, nie z wyniku
MIN_W_DZIEDZINIE = 1
KINDS = {"runs", "serves", "stores", "checks", "connects", "describes"}


def main():
    ap = argparse.ArgumentParser(description="Scal dziedziny i przypisania M11.")
    ap.add_argument("--model", default="claude-opus-4-6")
    ap.add_argument("--out", default="domains.json")
    args = ap.parse_args()

    katalog = ACAE / "_desc"
    manifest = json.loads((ACAE / "_out" / "manifest.json").read_text(encoding="utf-8"))
    w_packu = {str(f["path"]) for f in manifest["files"]}

    draft = json.loads((katalog / "domains_draft.json").read_text(encoding="utf-8"))
    domeny = draft["domains"]
    znane = {str(d["id"]) for d in domeny}

    czesci = sorted(katalog.glob("assign_*.json"))
    przypisania: dict[str, dict] = {}
    kolizje: list[str] = []
    for p in czesci:
        for sciezka, wpis in json.loads(p.read_text(encoding="utf-8")).items():
            if sciezka in przypisania and przypisania[sciezka] != wpis:
                kolizje.append(sciezka)
            przypisania[sciezka] = wpis

    braki = sorted(w_packu - set(przypisania))
    nadmiar = sorted(set(przypisania) - w_packu)
    zle_id = sorted(
        s for s, w in przypisania.items()
        if str(w.get("primary")) not in znane
        or (w.get("secondary") and str(w["secondary"]) not in znane)
    )
    zle_kind = sorted(s for s, w in przypisania.items() if str(w.get("kind")) not in KINDS)

    licznik = Counter()
    for w in przypisania.values():
        licznik[str(w["primary"])] += 1
        if w.get("secondary"):
            licznik[str(w["secondary"])] += 1
    puste = sorted(i for i in znane if licznik[i] < MIN_W_DZIEDZINIE)
    spuchniete = sorted(i for i in znane if licznik[i] > MAX_W_DZIEDZINIE)

    print(f"czesci wczytane   : {len(czesci)} ({', '.join(p.name for p in czesci)})")
    print(f"przypisan         : {len(przypisania)}")
    print(f"plikow w packu    : {len(w_packu)}")
    print(f"dziedzin          : {len(domeny)}")
    print()
    print("rozmiary dziedzin (liczac wtorne):")
    for i, n in licznik.most_common():
        znacznik = "  <-- ZA DUZA" if n > MAX_W_DZIEDZINIE else ""
        print(f"   {n:>3}  {i}{znacznik}")
    print()
    rodzaje = Counter(str(w.get("kind")) for w in przypisania.values())
    print("rodzaje:", ", ".join(f"{k}={n}" for k, n in rodzaje.most_common()))
    print()

    bledy = []
    if braki:
        bledy.append(f"{len(braki)} plikow bez dziedziny: {braki[:5]}")
    if nadmiar:
        bledy.append(f"{len(nadmiar)} przypisan spoza packa: {nadmiar[:5]}")
    if kolizje:
        bledy.append(f"{len(kolizje)} plikow przypisanych sprzecznie: {kolizje[:5]}")
    if zle_id:
        bledy.append(f"{len(zle_id)} przypisan do nieistniejacej dziedziny: {zle_id[:5]}")
    if zle_kind:
        bledy.append(f"{len(zle_kind)} nieznanych rodzajow: {zle_kind[:5]}")
    if puste:
        bledy.append(f"dziedziny bez ani jednego pliku: {puste}")
    if spuchniete:
        bledy.append(
            f"dziedziny powyzej {MAX_W_DZIEDZINIE} plikow: "
            + ", ".join(f"{i}={licznik[i]}" for i in spuchniete)
        )

    if bledy:
        print("WALIDACJA NIE PRZESZLA — artefakt NIE zostal zapisany:")
        for b in bledy:
            print(f"  * {b}")
        raise SystemExit(1)

    opisy_bajty = (katalog / "descriptions.json").read_bytes()
    from acae.canon import content_hash

    artefakt = {
        "provenance": {
            "model": args.model,
            "generated_at": datetime.datetime.now(datetime.timezone.utc)
            .replace(microsecond=0).isoformat(),
            "pack_hash": manifest["pack_hash"],
            "descriptions_hash": content_hash(opisy_bajty),
            "parts": [p.name for p in czesci],
            "domains": len(domeny),
            "files": len(przypisania),
        },
        "domains": domeny,
        "assignments": dict(sorted(przypisania.items())),
    }
    cel = katalog / args.out
    cel.write_text(
        json.dumps(artefakt, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )
    print(f"WALIDACJA PRZESZLA — zapisano {cel} ({cel.stat().st_size} bajtow)")
    print(f"najwieksza dziedzina: {licznik.most_common(1)[0][1]} plikow "
          f"(prog {MAX_W_DZIEDZINIE})")


if __name__ == "__main__":
    main()
