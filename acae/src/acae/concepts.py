"""
concepts.py — semantyczny codebook (M5). Wiedza ZAPISANA, nie wyliczona.

CZYM TO SIE ROZNI OD M4.1-M4.6
------------------------------
Szesc poprzednich mechanizmow probowalo WYLICZYC zwiazek „slowo z pytania -> identyfikator
w kodzie" ze statystyki: z wag, ze wspolwystepowania, z grafu wywolan, z cudzych docstringow.
Wszystkie zostaly odrzucone pomiarem, bo tej informacji w danych **nie ma** — nigdzie w repo
nie stoi zdanie „maszyna to jest to, co w kodzie nazywa sie host".

Ten modul nie liczy niczego. On to **czyta z pliku**, w ktorym czlowiek to wpisal.

DOPASOWANIE PO TOKENACH, NIE PO PODCIAGU
----------------------------------------
`form` jest podciagiem `Performance`, wiec dopasowanie podciagiem dawalo 31 „trafien"
na pojeciu „formularz", z ktorych zadne nie bylo trafieniem. Tokenizujemy identyfikator
(`split_identifier` z bm25f — to NARZEDZIE tokenizujace, nie odrzucony ranker BM25F)
i porownujemy cale tokeny.

KAZDE ROZSZERZENIE MA PARAGON
-----------------------------
`lookup()` zwraca pary (token, ConceptHit). Nie da sie wprowadzic tokenu do zapytania
bez zapisu, ktore pojecie go wniosło i przez ktore slowo — bo funkcja nie zwraca golych
stringow.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from .bm25f import split_identifier

SCHEMA = "acae.codebook.v1"

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "config" / "semantic_codebook.json"

# Te same wagi pol co w rankerze bazowym, zeby wynik byl porownywalny.
W_NAME, W_SIGNATURE, W_PATH = 3, 2, 1

# Sufit wagi rzadkosci. Ta sama wartosc co w retrieve.RARITY_CAP — celowo, zeby
# rozszerzenie i termin oryginalny byly w tej samej skali.
RARITY_CAP = 512


@dataclass(frozen=True)
class ConceptHit:
    """Paragon jednego rozszerzenia: ktore pojecie, przez ktore slowo, na jakie tokeny."""

    concept: str
    query_term: str
    matched_surface: str
    code_tokens: tuple[str, ...]
    eo: str | None

    def as_dict(self) -> dict:
        return {
            "rule": "semantic_codebook",
            "concept": self.concept,
            "derived_from": self.query_term,
            "matched_surface": self.matched_surface,
            "code_tokens": list(self.code_tokens),
            "eo": self.eo,
            "weight_class": "expansion",
        }


class Codebook:
    """
    Slownik pojec wczytany z pliku. Nic nie zgaduje.

    Dopasowanie idzie po formach powierzchniowych: slowo z pytania musi byc DOKLADNIE
    jedna z form wpisanych przez czlowieka. Bez dopasowania czesciowego — inaczej
    „form" trafialoby w „performance" i wrocilibysmy do zgadywania.
    """

    def __init__(self, path: Path | str = DEFAULT_PATH) -> None:
        raw = json.loads(Path(path).read_bytes())
        self.schema = raw.get("schema", SCHEMA)
        self.concepts = raw["concepts"]
        self._by_surface: dict[str, list[dict]] = {}
        for concept in self.concepts:
            for surface in concept["surface"]:
                self._by_surface.setdefault(surface.lower(), []).append(concept)

    def __len__(self) -> int:
        return len(self.concepts)

    def lookup(self, terms: Sequence[str]) -> list[tuple[str, ConceptHit]]:
        """
        Terminy zapytania -> tokeny kodu, kazdy z paragonem.

        Deduplikacja po tokenie: ten sam token moze wyjsc z kilku pojec, zostaje
        pierwszy paragon w porzadku alfabetycznym pojecia — zeby wynik byl powtarzalny.
        """
        out: dict[str, ConceptHit] = {}
        for term in sorted({t.lower() for t in terms if t}):
            for concept in self._by_surface.get(term, []):
                hit = ConceptHit(
                    concept=concept["id"],
                    query_term=term,
                    matched_surface=term,
                    code_tokens=tuple(concept["code"]),
                    eo=concept.get("eo"),
                )
                for token in concept["code"]:
                    if token not in out:
                        out[token] = hit
        return sorted(out.items(), key=lambda kv: (kv[1].concept, kv[0]))


class SymbolTokens:
    """
    Tokeny identyfikatorow dla kazdego symbolu packa, policzone raz.

    Trzyma tez `df` — w ilu symbolach token wystepuje — bo rozszerzenie musi wazyc
    rzadkoscia tak samo jak terminy oryginalne. Bez tego token `get` bilby token `host`.
    """

    def __init__(self, entries: Sequence[Mapping[str, object]]) -> None:
        self.docs: list[tuple[str, Mapping[str, object], frozenset[str], frozenset[str], frozenset[str]]] = []
        self.df: Counter = Counter()
        for entry in entries:
            path = str(entry["path"])
            path_tokens = frozenset(split_identifier(path))
            for row in entry["symbols"]:  # type: ignore[index]
                name = frozenset(split_identifier(str(row.get("name_path") or "")))
                sig = frozenset(split_identifier(str(row.get("signature") or "")))
                self.docs.append((path, row, name, sig, path_tokens))
                for token in name | sig | path_tokens:
                    self.df[token] += 1
        self.n = max(1, len(self.docs))

    def rarity(self, token: str) -> int:
        return max(1, min(RARITY_CAP, self.n // (1 + self.df.get(token, 0))))

    def score(self, doc_index: int, tokens: Sequence[str]) -> int:
        """Punkty symbolu za tokeny rozszerzenia. Dopasowanie CALYCH tokenow."""
        _, _, name, sig, path_tokens = self.docs[doc_index]
        total = 0
        for token in tokens:
            pola = (
                W_NAME * (token in name)
                + W_SIGNATURE * (token in sig)
                + W_PATH * (token in path_tokens)
            )
            if pola:
                total += self.rarity(token) * pola
        return total
