"""
rerank.py — M15: przesiewacz (cross-encoder) na czolowce. WARSTWA ODCZYTU.

CO TO ROBI I CZEGO NIE ROBI
---------------------------
Ten modul **nie uruchamia zadnego modelu**. Czyta zamrozone oceny z `_desc/rerank_cache.json`.
Model odpala sie RAZ, osobnym skryptem (`scripts/build_rerank_cache.py`), a wynik jest
kwantyzowany, zapisany i zacommitowany.

To jest ten sam wzorzec, ktory zadzialal juz trzy razy w tym projekcie: streszczenia
(M8), dziedziny (M11) i tablica wektorow (M7). **Droga rzecz dzieje sie raz, na boku,
i zostaje zamrozona; wszystko dalej jest deterministyczne.**

Powod jest twardy, nie estetyczny. Cross-encoder liczy na liczbach zmiennoprzecinkowych,
wiec miedzy maszynami i wersjami bibliotek moga wyjsc roznice na dalekich miejscach
po przecinku. Gdyby model biegl przy kazdym pomiarze, `result_hash` przestalby byc
porownywalny miedzy przebiegami. Z zamrozonym cache pomiar odtwarza sie bit w bit
— takze na maszynie, ktora modelu w ogole nie ma.

SKALA OCENY — I POMYLKA, KTORA TU BYLA
--------------------------------------
Prerejestracja M15 zakladala, ze wyjscie jest prawdopodobienstwem (sigmoida), bo
`sentence_transformers` domyslnie tak robi przy jednym neuronie wyjsciowym. **To bylo
bledne dla TEGO modelu.** Sprawdzone przed pomiarem:

    config deklaruje aktywacje: torch.nn.modules.linear.Identity
    faktycznie uzyta          : Identity

Model nadpisuje domyslne zachowanie biblioteki i oddaje **surowy logit**, nie
prawdopodobienstwo. Proba na jawnych parach: para pasujaca -0,95, niepasujaca -11,45 —
czyli nawet trafienie wychodzi UJEMNE, wiec zero nie jest tu zadna granica.

Skutek zapisany w prerejestracji i wykonany: **wariant `rerank_abstain` WYCOFANY**,
nie przestrojony na inna liczbe. Prog dobrany po zobaczeniu tych danych bylby dokladnie
tym, czego ta metodologia zabrania.

Zapisujemy wiec **milijednostki logitu** (logit * 1000, zaokraglone w dol od polowy),
bez zadnej granicy decyzyjnej. Ocena sluzy WYLACZNIE do porownywania kandydatow miedzy
soba — do tego wystarcza kolejnosc, a nie skala bezwzgledna.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Sequence

from .canon import content_hash

SCHEMA = "acae.rerank.v1"

# Zadnej granicy decyzyjnej NIE MA — patrz naglowek. Wariant odmawiajacy zostal wycofany
# przed pomiarem, gdy okazalo sie, ze model oddaje logit, a nie prawdopodobienstwo.


class RerankError(RuntimeError):
    """Cache przesiewacza nie nadaje sie do pomiaru."""


def question_key(question: str) -> str:
    """Klucz pytania. Hash tresci, zeby cache nie zalezal od kolejnosci ani formatowania."""
    return content_hash(question.encode("utf-8"))


def candidate_key(path: str, name_path: str) -> str:
    """Klucz kandydata. Sciezka plus nazwa symbolu — para jednoznaczna w calym packu."""
    return f"{path}::{name_path}"


def load_cache(path: Path, expected_pack_hash: str | None = None) -> tuple[dict, dict]:
    """
    Wczytanie zamrozonych ocen.

    Rozjazd `pack_hash` PRZERYWA pomiar — oceny wystawione dla innego stanu repo
    opisuja kod, ktorego juz nie ma. Ta sama regula co przy opisach i przy modelu M7.
    """
    dane = json.loads(Path(path).read_text(encoding="utf-8"))
    oceny = dane.get("scores")
    prov = dane.get("provenance", {})
    if not isinstance(oceny, dict) or not oceny:
        raise RerankError(f"{path}: brak mapy `scores`")

    faktyczny = str(prov.get("pack_hash") or "")
    if expected_pack_hash is not None and faktyczny != expected_pack_hash:
        raise RerankError(
            f"{path}: oceny wystawiono dla pack_hash {faktyczny or '(brak)'}, "
            f"a repo ma teraz {expected_pack_hash}. Pomiar przerwany."
        )
    return oceny, prov


def rerank(
    ranked: Sequence[Mapping[str, object]],
    question: str,
    cache: Mapping[str, Mapping[str, int]],
) -> tuple[list[dict], list[dict]]:
    """
    Przestawia podana czolowke wylacznie ocena przesiewacza.

    Kolejnosc wejsciowa NIE ma znaczenia dla wyniku — remisy rozstrzygane sa tak samo
    jak wszedzie w tym projekcie: (sciezka, linia, name_path). Bez tego wynik zalezalby
    od tego, co przypadkiem podal embedding.

    Brak oceny w cache jest BLEDEM, nie cichym zerem. Symbol bez oceny znaczy, ze cache
    powstal dla innej czolowki — a wtedy pomiar mierzy cos innego, niz sadzimy.
    """
    oceny = cache.get(question_key(question))
    if oceny is None:
        raise RerankError(f"brak ocen dla pytania: {question[:60]!r}")

    z_ocena: list[dict] = []
    for item in ranked:
        klucz = candidate_key(str(item["path"]), str(item["row"]["name_path"]))
        if klucz not in oceny:
            raise RerankError(f"brak oceny dla kandydata {klucz}")
        nowy = dict(item)
        nowy["rerank_permille"] = int(oceny[klucz])
        nowy["embed_score"] = int(item["score"])
        nowy["score"] = int(oceny[klucz])
        z_ocena.append(nowy)

    z_ocena.sort(
        key=lambda r: (-r["rerank_permille"], r["path"], r["row"]["line"], r["row"]["name_path"])
    )
    paragony = [{
        "rule": "cross_encoder_rerank",
        "note": "czolowka przestawiona ocena przesiewacza; skala 0..1000 promili, granica 500",
        "top": [
            {
                "symbol": f"{r['path']}:{r['row']['name_path']}",
                "rerank": r["rerank_permille"],
                "embed": r["embed_score"],
            }
            for r in z_ocena[:3]
        ],
    }]
    return z_ocena, paragony
