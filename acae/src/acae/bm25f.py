"""
bm25f.py — M4.1. Ranking oparty na modelu, a nie na wagach wymyslonych z palca.

PO CO TO ZASTEPUJE `score_symbol`
---------------------------------
Dotychczasowy scoring pekl DWA RAZY w ciagu jednej sesji:
  * najpierw rowne wagi terminow — wygrywal termin CZESTY, nie ISTOTNY
    (`CBMSMemory` bilo `provenance()` na pytaniu o provenance),
  * potem `RARITY_CAP=64` — sufit splaszczal termin bardzo rzadki ze srednio czestym
    (`provenance` w ~5 symbolach i `write` w ~24 dostawaly identyczna wage).
Oba razy przyczyna byla ta sama: to byl wymyslony od nowa IDF bez teorii. BM25F ma to
rozwiazane od dwudziestu lat, w dodatku z dwiema wlasnosciami, ktorych recznie sie nie
odtworzy:

1. **Nasycenie** (`k1`) — dziesiate wystapienie terminu nie wazy tyle co pierwsze.
   Bez tego dlugi symbol wygrywa samym powtarzaniem.
2. **Normalizacja dlugosci PER POLE** (`b_f`) — a sygnatura symbolu to zbior bardzo
   krotkich pol. Zwykly BM25 z jedna srednia dlugoscia karalby nazwe symbolu za to,
   ze jest krotka. BM25F normalizuje kazde pole wzgledem sredniej TEGO pola.
   Dla `name_path` `b=0`, bo dlugosc nazwy nie niesie zadnego sygnalu o trafnosci.

Kolejnosc operacji jest istotna i rozni BM25F od naiwnego „BM25 per pole, potem suma":
czestosci sumujemy PRZED nasyceniem, nie po. Inaczej trafienie rozlozone na trzy pola
dostawaloby trzy razy pelna nagrode zamiast jednej nasyconej.

TOKENIZACJA
-----------
BM25 liczy tokeny, wiec identyfikatory trzeba rozbic: `server_host` -> `server`, `host`;
`withProvenance` -> `with`, `provenance`. To NIE jest AMAP — nie rozwijamy skrotow,
tylko tniemy po znakach niealfanumerycznych i po granicy camelCase.

Skutek uboczny do zmierzenia, nie do przemilczenia: dopasowanie podciagiem znika.
Dzis `prov` trafialby w `provenance`; po zmianie nie trafi, bo `prov` nie jest tokenem.
Jesli to obnizy recall, znaczy ze AMAP (M4.5) jest potrzebny — i bedzie to WIDAC
w pomiarze, zamiast byc kwestia przeczucia.

FLOATY
------
Wynik liczymy w zmiennoprzecinkowych (logarytm w IDF), ale **kwantujemy do liczby
calkowitej** (tysieczne) przed sortowaniem, a remisy rozstrzyga `(sciezka, linia, name_path)`.
Dzieki temu porzadek nie zalezy od ostatniego bitu mantysy. Do artefaktow zaden wynik
nie trafia — obowiazuje zakaz floatow z `canon._reject_floats`.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Mapping, Sequence

SCHEMA = "acae.bm25f.v1"

_NON_ALNUM = re.compile(r"[^A-Za-z0-9]+")
_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
MIN_TOKEN = 2

# Wynik skalowany do tysiecznych i zaokraglany do int — patrz sekcja FLOATY.
SCALE = 1000
K1 = 1.2


@dataclass(frozen=True)
class Field:
    """Pole dokumentu z wlasna waga i wlasna normalizacja dlugosci."""

    key: str
    weight: float
    b: float


# Wagi odzwierciedlaja ten sam porzadek co poprzednio (nazwa > sygnatura > sciezka),
# ale teraz z nasyceniem i normalizacja per pole. `b=0` dla nazwy: dlugosc `name_path`
# nie niesie sygnalu, wiec karanie za nia byloby szumem.
FIELDS: tuple[Field, ...] = (
    Field("name_path", 3.0, 0.0),
    Field("signature", 1.5, 0.3),
    Field("doc", 1.0, 0.5),
    Field("path", 0.8, 0.2),
)


def split_identifier(text: str) -> list[str]:
    """`CBMSMemory/get_memory_stats` -> ['cbms','memory','get','memory','stats']."""
    out: list[str] = []
    for chunk in _NON_ALNUM.split(text or ""):
        if not chunk:
            continue
        for part in _CAMEL.split(chunk):
            token = part.lower()
            if len(token) >= MIN_TOKEN:
                out.append(token)
    return out


def prepare_terms(terms: Sequence[str]) -> list[str]:
    """
    Terminy zapytania przez ten sam tokenizator co dokumenty.

    Gdyby zapytanie i indeks tokenizowaly inaczej, `memory_store` z pytania nigdy
    nie trafiloby w `memory` + `store` z symbolu. Jeden tokenizator, jedna pisownia.
    """
    seen: list[str] = []
    for term in terms:
        for token in split_identifier(term) or [term.lower()]:
            if token not in seen:
                seen.append(token)
    return seen


class Bm25fIndex:
    """
    Indeks BM25F nad symbolami packa. Buduje sie raz, odpytuje wielokrotnie.

    Dokumentem jest SYMBOL, nie plik — bo to symbol jest jednostka, ktora zwracamy.
    Indeksowanie plikami dawaloby recall na poziomie pliku i nie odrozniloby
    `provenance()` od stu innych funkcji w tym samym module.
    """

    def __init__(
        self,
        entries: Sequence[Mapping[str, object]],
        fields: Sequence[Field] = FIELDS,
        k1: float = K1,
    ) -> None:
        self.fields = tuple(fields)
        self.k1 = k1
        self.docs: list[dict] = []
        df: Counter = Counter()
        totals = {f.key: 0 for f in self.fields}

        for entry in entries:
            path = str(entry["path"])
            path_tokens = split_identifier(path)
            for row in entry["symbols"]:  # type: ignore[index]
                tf: dict[str, Counter] = {}
                lengths: dict[str, int] = {}
                present: set[str] = set()
                for field in self.fields:
                    tokens = path_tokens if field.key == "path" else split_identifier(str(row.get(field.key) or ""))
                    counter = Counter(tokens)
                    tf[field.key] = counter
                    lengths[field.key] = len(tokens)
                    totals[field.key] += len(tokens)
                    present |= set(counter)
                for token in present:
                    df[token] += 1
                self.docs.append({
                    "path": path,
                    "lang": entry.get("lang"),
                    "row": row,
                    "tf": tf,
                    "len": lengths,
                })

        self.n = max(1, len(self.docs))
        self.df = df
        self.avg = {f.key: (totals[f.key] / self.n) or 1.0 for f in self.fields}

    def idf(self, term: str) -> float:
        """Wariant Lucene'owy: zawsze dodatni, wiec termin czesty nie odejmuje punktow."""
        df = self.df.get(term, 0)
        return math.log(1.0 + (self.n - df + 0.5) / (df + 0.5))

    def score_doc(self, doc: Mapping[str, object], terms: Sequence[str], weight_permille: int = 1000) -> int:
        """
        Wynik jednego symbolu. `weight_permille` pozwala wazyc CALY zestaw terminow
        slabiej — tak wejda pozniej terminy rozszerzone z M4.2/M4.3, bez mieszania
        ich z terminami oryginalnymi w jednym worku.
        """
        total = 0.0
        for term in terms:
            acc = 0.0
            for field in self.fields:
                freq = doc["tf"][field.key].get(term, 0)  # type: ignore[index]
                if not freq:
                    continue
                length = doc["len"][field.key]  # type: ignore[index]
                denom = 1.0 - field.b + field.b * (length / self.avg[field.key])
                acc += field.weight * freq / (denom or 1.0)
            if acc > 0.0:
                # Nasycenie PO zsumowaniu pol — to jest istota BM25F.
                total += self.idf(term) * acc / (self.k1 + acc)
        return int(round(total * SCALE * weight_permille / 1000))

    def rank(
        self,
        terms: Sequence[str],
        limit: int,
        expansion: Sequence[str] = (),
        expansion_permille: int = 500,
    ) -> list[dict]:
        """
        Ranking symboli. Zwraca ten sam ksztalt co `retrieve.select`, zeby dalo sie
        podmienic ranker bez ruszania renderowania wycinka.

        Remis rozstrzyga `(sciezka, linia, name_path)` — nigdy kolejnosc wstawiania.
        """
        base = prepare_terms(terms)
        extra = [t for t in prepare_terms(expansion) if t not in base]
        ranked: list[dict] = []
        for doc in self.docs:
            score = self.score_doc(doc, base)
            if extra:
                score += self.score_doc(doc, extra, weight_permille=expansion_permille)
            if score > 0:
                ranked.append({"score": score, "path": doc["path"], "lang": doc["lang"], "row": doc["row"]})
        ranked.sort(key=lambda d: (-d["score"], d["path"], d["row"]["line"], d["row"]["name_path"]))
        return ranked[:limit]
