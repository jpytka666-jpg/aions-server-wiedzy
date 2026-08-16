"""
describe.py — M8: opis kazdego pliku po ludzku jako dodatkowe pole rankingu.

PO CO
-----
Dziewiec mechanizmow probowalo WYLICZYC zwiazek „slowo z pytania -> identyfikator
w kodzie" z tego, co w repo juz lezy. Pomiar sufitu (STATE 2026-08-12T22:10) pokazal,
dlaczego zadne nie moglo zadzialac: dla 9 z 11 pytan grupy zerowej w calym repo nie ma
ANI JEDNEGO ludzkiego zdania opisujacego wlasciwe pliki. Nie da sie wycisnac sygnalu
ze zbioru, ktory go nie zawiera.

M8 nie szuka sygnalu — wytwarza go. `_desc/descriptions.json` to opis kazdego ze 169
plikow napisany jezykiem, ktorym pyta czlowiek. Generowanie bylo niedeterministyczne
(model), UZYWANIE jest deterministyczne: artefakt powstal raz, jest zacommitowany
i od tej chwili wchodzi do rankingu jak kazde inne dane. Ta sama granica co przy M7 —
`export_model.py` wolno zalezec od `torch`, warstwie zapytania nie wolno.

WAGA — decyzja z prerejestracji
-------------------------------
Opis wchodzi z waga pola `path` (`W_PATH = 1`), najnizsza z istniejacych. Nowa waga
byloby pokretlem strojonym po zobaczeniu wyniku. Opis wskazuje PLIK, nie symbol,
wiec wszystkie symbole z danego pliku dostaja go tak samo.

DECYZJA M8-a — opisy licza sie do rzadkosci
-------------------------------------------
Prerejestracja milczy o tym, czy tekst opisu ma wchodzic do `term_rarity`. Milczenie
nie jest tu neutralne. `term_rarity` daje terminowi wage `total // (1 + df)` z sufitem
`RARITY_CAP`, wiec termin o `df = 0` dostaje wage MAKSYMALNA. Slowa takie jak „machine",
„password", „computer" wystepuja po tej zmianie WYLACZNIE w opisach — gdyby opisy
nie liczyly sie do `df`, takie slowo mialoby `df = 0` i wage 512 zamiast ~7.
Siedemdziesiat razy wiecej, niz wynika z „najnizszej wagi".

M8 wygladalby wtedy swietnie z powodu, ktorego nikt nie zapisal. To jest ta sama klasa
bledu co rowne wagi -> RARITY_CAP -> stosunek bez wsparcia -> LLR bez kontroli
pospolitosci: statystyka bez kontroli mianownika, piaty raz w tym projekcie.

Dlatego opis wchodzi do `df` na rowni z pozostalymi polami. Wariant przeciwny NIE jest
mierzony — bylby darmowym drugim strzalem.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Sequence

# `_haystack` swiadomie brane z retrieve, a nie odtwarzane tutaj: to jedno zrodlo prawdy
# o tym, jaki tekst symbolu widzi ranker. Odtworzenie go na drugi raz znaczyloby, ze
# zmiana pola w retrieve.py cicho rozjezdza rzadkosc miedzy baseline'em a M8.
from .retrieve import RARITY_CAP, W_PATH, _haystack, score_symbol

SCHEMA = "acae.descriptions.v1"


class DescriptionsError(RuntimeError):
    """Artefakt opisow nie nadaje sie do pomiaru."""


def load_descriptions(
    path: Path,
    expected_pack_hash: str | None = None,
    strict: bool = True,
) -> tuple[dict[str, str], dict]:
    """
    Wczytanie artefaktu opisow wraz z prowieniencja.

    DWA TRYBY, bo to sa dwa rozne zastosowania tego samego pliku:

    * **`strict=True` (pomiar)** — rozjazd `pack_hash` PRZERYWA robote. Liczby porownywane
      miedzy dwudziestoma kilkoma pomiarami musza dotyczyc tego samego repo, inaczej
      cala tabela klamie.
    * **`strict=False` (uzycie)** — rozjazd tylko USTAWIA FLAGE w prowieniencji
      (`stale=True`) i pozwala dzialac. Gdy zmienisz dwa pliki ze 169, opisy pozostalych
      167 sa nadal prawdziwe i blokowanie narzedzia byloby szkodliwe.

    Bez tego rozdzielenia kazda edycja `server.py` blokowala narzedzie — i dokladnie
    to zmuszalo nas do recznego cofania plikow przed kazdym uruchomieniem.
    """
    dane = json.loads(Path(path).read_text(encoding="utf-8"))
    opisy = dane.get("descriptions")
    prov = dane.get("provenance", {})
    if not isinstance(opisy, dict) or not opisy:
        raise DescriptionsError(f"{path}: brak mapy `descriptions`")

    faktyczny = str(prov.get("pack_hash") or "")
    rozjazd = expected_pack_hash is not None and faktyczny != expected_pack_hash
    if rozjazd and strict:
        raise DescriptionsError(
            f"{path}: opisy wyprodukowano dla pack_hash {faktyczny or '(brak)'}, "
            f"a repo ma teraz {expected_pack_hash}. Pomiar przerwany."
        )
    prov = dict(prov)
    prov["stale"] = bool(rozjazd)
    return {str(k): str(v) for k, v in opisy.items()}, prov


def term_rarity_with_descriptions(
    entries: Sequence[Mapping[str, object]],
    terms: Sequence[str],
    descriptions: Mapping[str, str],
) -> dict[str, int]:
    """
    `term_rarity` z retrieve.py, ale tekst opisu pliku wchodzi do `df` jak kazde inne pole.

    Powod w naglowku modulu (decyzja M8-a). Reszta arytmetyki jest identyczna z baseline'em,
    lacznie z sufitem: rozjazd tutaj znaczylby, ze M8 i baseline licza na innych wagach
    i porownanie nie mowi nic o opisach.
    """
    if not terms:
        return {}
    df = {term: 0 for term in terms}
    total = 0
    for entry in entries:
        path = str(entry["path"])
        opis = descriptions.get(path, "").lower()
        for row in entry["symbols"]:  # type: ignore[index]
            total += 1
            hay = f"{_haystack(path, row)} {opis}"
            for term in terms:
                if term in hay:
                    df[term] += 1
    return {term: max(1, min(RARITY_CAP, total // (1 + df[term]))) for term in terms}


def score_with_description(
    path: str,
    row: Mapping[str, object],
    terms: Sequence[str],
    rarity: Mapping[str, int],
    description: str,
) -> int:
    """Wynik baseline'u plus trafienia w opisie pliku, z waga `W_PATH`."""
    score = score_symbol(path, row, terms, rarity)
    if not description:
        return score
    opis = description.lower()
    for term in terms:
        if term in opis:
            score += rarity.get(term, 1) * W_PATH
    return score


def rank_all(
    entries: Sequence[Mapping[str, object]],
    terms: Sequence[str],
    descriptions: Mapping[str, str],
) -> tuple[list[dict], dict[str, int]]:
    """
    Pelny ranking symboli z opisami. Zwraca tez wagi rzadkosci — miernik potrzebuje
    ich do warunku diagnostycznego i nie ma sensu liczyc ich drugi raz.

    Remisy rozstrzygane DOKLADNIE tak jak w `retrieve.select`: (sciezka, linia, name_path).
    Inne rozstrzyganie przestawialoby wyniki niezaleznie od opisow.
    """
    rarity = term_rarity_with_descriptions(entries, terms, descriptions)
    ranked: list[dict] = []
    for entry in entries:
        path = str(entry["path"])
        opis = descriptions.get(path, "")
        for row in entry["symbols"]:  # type: ignore[index]
            score = score_with_description(path, row, terms, rarity, opis)
            if score > 0:
                ranked.append({
                    "score": score,
                    "path": path,
                    "lang": entry.get("lang"),
                    "row": row,
                })
    ranked.sort(key=lambda r: (-r["score"], r["path"], r["row"]["line"], r["row"]["name_path"]))
    return ranked, rarity


def receipt(
    ranked: Sequence[Mapping[str, object]],
    terms: Sequence[str],
    descriptions: Mapping[str, str],
    rarity: Mapping[str, int],
    limit: int = 3,
) -> list[dict]:
    """
    Paragon: dla czolowych symboli — ktore slowa z pytania trafily w OPIS pliku
    i ile punktow za to wpadlo.

    Bez tego nie da sie odroznic „opis pomogl" od „leksyka i tak by to znalazla",
    a to jest cale pytanie tego etapu.
    """
    pozycje = []
    for item in ranked[:limit]:
        path = str(item["path"])
        opis = descriptions.get(path, "").lower()
        trafione = [t for t in terms if t in opis]
        pozycje.append({
            "symbol": f"{path}:{item['row']['name_path']}",
            "score": item["score"],
            "terms_in_description": trafione,
            "from_description": sum(rarity.get(t, 1) * W_PATH for t in trafione),
        })
    return [{"rule": "file_description", "note": f"opis pliku z waga W_PATH={W_PATH}", "top": pozycje}]
