"""
embed.py — M7. Statyczny embedding jako most slownikowy. Arytmetyka wylacznie calkowita.

CO TO ROZWIAZUJE
----------------
Pomiar diagnostyczny rozbil porazke na dwie polowy: 37% pytan ma wlasciwy symbol obecny,
ale nisko (zla kolejnosc), a 36% ma go z wynikiem leksykalnym **zero**. Osiem mechanizmow
atakowalo kolejnosc. Zera nie rusza zadne przeliczanie, bo `0 * cokolwiek = 0`.
Ten modul daje kazdemu symbolowi wynik niezerowy — jako pierwszy moze dotknac tych 36%.

DLACZEGO MODEL STATYCZNY, A NIE TRANSFORMER
-------------------------------------------
Nie dla rozmiaru. Dla **rozkladalnosci**. Wektor tekstu jest suma wektorow tokenow, wiec
licznik podobienstwa rozklada sie DOKLADNIE:

    <sum_j q_j, sum_i d_i> = sum_{j,i} <q_j, d_i>

Kazda para (slowo z pytania, token symbolu) ma policzalny, dokladny wklad, i te wklady
sumuja sie do wyniku. Paragon nie jest wyjasnieniem dorobionym po fakcie — to jest ta sama
arytmetyka, ktora dala wynik. Transformer tego nie potrafi.

Zastrzezenie, ktore kosztowalo jeden czerwony test: rozklad jest dokladny **tylko z parami
o ujemnym wkladzie**. Pokazywanie samych dodatnich daje sume WIEKSZA od wyniku (zmierzone:
535 wobec 440), bo odejmowane skladniki znikaja. Dlatego `receipt` zwraca wszystkie pary,
a nie tylko te, ktore ladnie wygladaja.

DLACZEGO NIE MA TU ANI JEDNEGO FLOATA
-------------------------------------
Zmiennoprzecinkowy iloczyn skalarny nie jest deterministyczny miedzy maszynami: BLAS
zmienia kolejnosc sumowania zaleznie od liczby watkow, a dodawanie floatow nie jest laczne.
Dodawanie liczb calkowitych JEST laczne i dokladne, wiec kolejnosc nie ma znaczenia.

- wektor tekstu = **suma** wierszy `int16` w `int64` (suma, nie srednia — cosinus i tak
  skraca staly czynnik, a dzielenie wprowadziloby zaokraglenie),
- licznik: iloczyn skalarny w `int64`,
- mianownik: `math.isqrt` — dokladny pierwiastek calkowity,
- wynik: **promile w `int`**, zgodnie z kanonicznym JSON, ktory zabrania floatow.

Przejscie na `int` Pythona przed mnozeniem przez 1000 jest konieczne: `iloczyn * 1000`
przekracza zakres `int64`, a `int` Pythona ma dowolna precyzje.
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np

from .bm25f import split_identifier   # narzedzie tokenizujace, nie odrzucony ranker

SCHEMA = "acae.embed.v1"
PERMILLE = 1000
RECEIPT_PAIRS = 5


class ModelMismatch(RuntimeError):
    """Artefakt na dysku nie zgadza sie z karta modelu. Lepiej stanac niz zgadywac."""


def _blake2b256(path: pathlib.Path) -> str:
    h = hashlib.blake2b(digest_size=32)
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return f"blake2b256:{h.hexdigest()}"


@dataclass(frozen=True)
class Pair:
    """Jeden wiersz paragonu: ktore slowo pytania, ktory token symbolu, jaki wklad."""

    query_token: str
    doc_token: str
    permille: int

    def as_dict(self) -> dict:
        return {
            "query_token": self.query_token,
            "doc_token": self.doc_token,
            "permille": self.permille,
        }


class StaticEmbedder:
    """
    Tablica token -> wektor. Przy tworzeniu weryfikuje hashe wobec karty modelu.

    Weryfikacja nie jest ozdoba: bez niej podmieniony albo uciety plik dalby wyniki,
    ktore wygladaja sensownie i sa falszywe. Wolimy wyjatek niz cicha halucynacje.
    """

    def __init__(self, model_dir: str | pathlib.Path, verify: bool = True) -> None:
        root = pathlib.Path(model_dir)
        card_path = root / "model_card.json"
        if not card_path.is_file():
            raise ModelMismatch(f"brak karty modelu: {card_path}")
        self.card = json.loads(card_path.read_text(encoding="utf-8"))

        matrix_path = root / "vectors_int16.npy"
        tokenizer_path = root / "tokenizer.json"
        if verify:
            for name, path in (("vectors_int16.npy", matrix_path),
                               ("tokenizer.json", tokenizer_path)):
                oczekiwany = self.card.get("files", {}).get(name)
                if not path.is_file():
                    raise ModelMismatch(f"brak pliku artefaktu: {path}")
                faktyczny = _blake2b256(path)
                if oczekiwany != faktyczny:
                    raise ModelMismatch(
                        f"{name}: karta mowi {oczekiwany}, na dysku {faktyczny}"
                    )

        self.matrix = np.load(matrix_path, allow_pickle=False)
        if self.matrix.dtype != np.int16:
            raise ModelMismatch(f"oczekiwano int16, jest {self.matrix.dtype}")

        from tokenizers import Tokenizer   # lekki, bez torch
        self.tokenizer = Tokenizer.from_file(str(tokenizer_path))
        self.dim = int(self.matrix.shape[1])

    # ------------------------------------------------------------ tokenizacja

    def rows(self, text: str) -> list[tuple[str, int]]:
        """(token, numer wiersza). Tokeny spoza slownika po prostu nie wystepuja."""
        enc = self.tokenizer.encode(text, add_special_tokens=False)
        limit = int(self.matrix.shape[0])
        return [
            (tok, int(idx))
            for tok, idx in zip(enc.tokens, enc.ids)
            if 0 <= int(idx) < limit
        ]

    def vector(self, text: str) -> np.ndarray:
        """Suma wierszy w int64. Pusty tekst daje wektor zerowy, nie wyjatek."""
        rows = self.rows(text)
        if not rows:
            return np.zeros(self.dim, dtype=np.int64)
        idx = np.fromiter((i for _, i in rows), dtype=np.int64, count=len(rows))
        return self.matrix[idx].astype(np.int64).sum(axis=0)


def similarity_permille(a: np.ndarray, b: np.ndarray) -> int:
    """
    Cosinus w promilach, dokladnie i calkowicie. Ujemne podobienstwo scinamy do 0:
    ranking i tak bierze najwyzsze, a ujemne promile zasmiecalyby paragon.
    """
    licznik = int(np.dot(a, b))
    if licznik <= 0:
        return 0
    na = math.isqrt(int(np.dot(a, a)))
    nb = math.isqrt(int(np.dot(b, b)))
    if na == 0 or nb == 0:
        return 0
    return (licznik * PERMILLE) // (na * nb)


def symbol_text(path: str, row) -> str:
    """
    Tekst symbolu dla embeddingu. Regula ustalona w prerejestracji M7 i nie zmieniana:
    rozbita sciezka bez rozszerzenia + rozbity `name_path` + slowa z sygnatury i doca.
    """
    bez_rozszerzenia = path.rsplit(".", 1)[0]
    czesci: list[str] = []
    czesci += split_identifier(bez_rozszerzenia)
    czesci += split_identifier(str(row.get("name_path") or ""))
    czesci += split_identifier(str(row.get("signature") or ""))
    czesci += split_identifier(str(row.get("doc") or ""))
    return " ".join(czesci)


def receipt(
    embedder: StaticEmbedder,
    query: str,
    doc_text: str,
    limit: int = RECEIPT_PAIRS,
) -> list[Pair]:
    """
    Pary (slowo pytania, token symbolu) o najwiekszym wkladzie, w promilach tej samej
    skali co `similarity_permille`. Wklady sumuja sie do wyniku — to jest rozklad
    dokladny, nie przyblizenie.
    """
    q_rows = embedder.rows(query)
    d_rows = embedder.rows(doc_text)
    if not q_rows or not d_rows:
        return []

    qv = embedder.vector(query)
    dv = embedder.vector(doc_text)
    na = math.isqrt(int(np.dot(qv, qv)))
    nb = math.isqrt(int(np.dot(dv, dv)))
    if na == 0 or nb == 0:
        return []
    mianownik = na * nb

    Q = embedder.matrix[np.fromiter((i for _, i in q_rows), dtype=np.int64, count=len(q_rows))]
    D = embedder.matrix[np.fromiter((i for _, i in d_rows), dtype=np.int64, count=len(d_rows))]
    wklady = Q.astype(np.int64) @ D.astype(np.int64).T   # dokladnie, w int64

    # Pary o ujemnym wkladzie NIE sa pomijane. Pominiecie ich sprawialoby, ze suma
    # czolowki przekracza wynik calkowity — wykryl to `test_paragon_rozklada_sie_dokladnie`
    # (535 wobec 440). Rozklad jest dokladny tylko wtedy, gdy zawiera wszystkie skladniki;
    # sortowanie malejaco i tak stawia dodatnie na gorze, wiec czolowka paragonu sie
    # nie zmienia, a suma calosci przestaje klamac.
    pary: list[Pair] = []
    for j, (q_tok, _) in enumerate(q_rows):
        for i, (d_tok, _) in enumerate(d_rows):
            wartosc = int(wklady[j, i])
            pary.append(Pair(q_tok, d_tok, (wartosc * PERMILLE) // mianownik))

    pary.sort(key=lambda p: (-p.permille, p.query_token, p.doc_token))
    return pary[:limit]


def rank(
    embedder: StaticEmbedder,
    query: str,
    entries: Sequence[dict],
) -> list[tuple[int, str, str, int]]:
    """
    (wynik_w_promilach, sciezka, name_path, linia) dla wszystkich symboli.
    Kolejnosc rozstrzygana tak samo jak w rankingu bazowym: wynik malejaco,
    potem sciezka, linia, nazwa — zeby remisy byly deterministyczne.
    """
    qv = embedder.vector(query)
    out: list[tuple[int, str, str, int]] = []
    for entry in entries:
        path = str(entry["path"])
        for row in entry["symbols"]:
            dv = embedder.vector(symbol_text(path, row))
            out.append((
                similarity_permille(qv, dv),
                path,
                str(row["name_path"]),
                int(row["line"]),
            ))
    out.sort(key=lambda t: (-t[0], t[1], t[3], t[2]))
    return out
