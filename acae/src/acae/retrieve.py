"""
retrieve.py — wzorzec outline-then-drill w jednej funkcji.

PO CO
-----
Caly szkielet repo to 36 tysiecy tokenow. To duzo mniej niz zrzut zrodel, ale wciaz
za duzo, zeby wysylac go przy kazdym pytaniu — a przy trzech z dziesieciu zamrozonych
zapytan bylby wrecz drozszy niz dzisiejsze Grep+Read. Bramka M2 (decyzja D4) porownuje
per zapytanie, wiec szkielet trzeba CIAC pod pytanie, a nie podawac w calosci.

JAK
---
1. Zapytanie rozbijamy na terminy dokladnie tak samo jak baseline z M0 — inaczej
   porownywalibysmy dwie rozne rzeczy i bramka nic by nie znaczyla.
2. Kazdy symbol dostaje punkty za trafienia w `name_path`, w sygnaturze i w sciezce,
   z malejaca waga. Nazwa symbolu jest silniejszym sygnalem niz nazwa katalogu.
3. Najlepsze `outline_limit` symboli trafia do szkieletu, a najlepsze `drill_limit`
   dostaja pelne cialo. To jest cale "then-drill".

Modul nie dotyka dysku: ciala przychodza przez port Reader.
"""

from __future__ import annotations

import re
from typing import Mapping, Sequence

from .ports import Reader
from .symbols import body_of, index_from_bytes

SCHEMA = "acae.slice.v1"

# MUSI byc identyczne z lista w scripts/measure_baseline.py. Rozjazd tutaj oznacza,
# ze M2 porownuje sie z baseline'em policzonym na innych terminach, czyli z niczym.
# Pilnuje tego test_retrieve.py::test_terminy_zgadzaja_sie_z_baselinem.
STOPWORDS = frozenset({
    "and", "are", "back", "does", "every", "for", "from", "how", "its", "not",
    "the", "this", "that", "them", "then", "there", "was", "were", "what",
    "when", "where", "which", "who", "why", "with",
})

TERM_RE = re.compile(r"[a-z0-9_]+")

# Nazwa symbolu jest mocniejszym sygnalem niz sygnatura, a sygnatura niz sciezka.
# Bez zroznicowania wag plik o nazwie "memory.py" wygrywalby z funkcja `store_memory`
# tylko dlatego, ze termin pada w kazdym jego symbolu.
W_NAME, W_SIGNATURE, W_PATH = 3, 2, 1


def query_terms(text: str, min_len: int = 3) -> list[str]:
    """Rozbior zapytania na terminy. Ta sama regula co w baseline z M0."""
    terms = {
        t for t in TERM_RE.findall(text.lower())
        if len(t) >= min_len and t not in STOPWORDS
    }
    return sorted(terms)


def _hits(haystack: str, terms: Sequence[str]) -> int:
    """Ile ROZNYCH terminow wystepuje w tekscie. Nie ile razy — inaczej wygrywalyby powtorzenia."""
    low = haystack.lower()
    return sum(1 for term in terms if term in low)


def score_symbol(path: str, row: Mapping[str, object], terms: Sequence[str]) -> int:
    if not terms:
        return 0
    return (
        W_NAME * _hits(str(row.get("name_path") or ""), terms)
        + W_SIGNATURE * _hits(str(row.get("signature") or ""), terms)
        + W_PATH * _hits(path, terms)
    )


def select(
    entries: Sequence[Mapping[str, object]],
    terms: Sequence[str],
    outline_limit: int,
    drill_limit: int,
) -> tuple[list[dict], list[dict]]:
    """
    Ranking symboli. Czysta funkcja — zadnego I/O, zadnej zaleznosci od kolejnosci wejscia.

    Remis rozstrzyga (sciezka, linia, name_path). Bez tego dwa symbole o tym samym
    wyniku ustawialyby sie wedlug kolejnosci wstawiania do slownika.
    """
    ranked: list[dict] = []
    for entry in entries:
        path = str(entry["path"])
        for row in entry["symbols"]:  # type: ignore[index]
            score = score_symbol(path, row, terms)
            if score > 0:
                ranked.append({
                    "score": score,
                    "path": path,
                    "lang": entry.get("lang"),
                    "row": row,
                })

    ranked.sort(key=lambda r: (-r["score"], r["path"], r["row"]["line"], r["row"]["name_path"]))
    return ranked[:outline_limit], ranked[:drill_limit]


def _render(
    query: str,
    terms: Sequence[str],
    outline: Sequence[Mapping[str, object]],
    bodies: Sequence[Mapping[str, object]],
) -> bytes:
    lines: list[str] = [
        f"# {SCHEMA}",
        f"# pytanie: {query}",
        f"# terminy: {' '.join(terms)}",
        f"# szkielet: {len(outline)} symboli · ciala: {len(bodies)}",
    ]

    # Szkielet grupowany po pliku, pliki i symbole w kolejnosci rosnacej.
    by_file: dict[str, list[Mapping[str, object]]] = {}
    langs: dict[str, str] = {}
    for item in outline:
        by_file.setdefault(str(item["path"]), []).append(item)
        langs[str(item["path"])] = str(item.get("lang") or "?")

    for path in sorted(by_file):
        lines.append("")
        lines.append(f"## {path} [{langs[path]}]")
        for item in sorted(by_file[path], key=lambda i: (i["row"]["line"], i["row"]["name_path"])):
            row = item["row"]
            sig = str(row.get("signature") or "").strip()
            lines.append(f"  {row['line']} {row['kind']} {row['name_path']} | {sig}")

    for body in bodies:
        lines.append("")
        lines.append(f"### {body['path']} :: {body['name_path']}")
        lines.append(str(body["text"]))
        if body.get("truncated"):
            lines.append(f"[... uciete, cialo ma {body['total_lines']} linii ...]")

    lines.append("")
    return "\n".join(lines).encode("utf-8")


def build_slice(
    entries: Sequence[Mapping[str, object]],
    query: str,
    reader: Reader,
    outline_limit: int = 40,
    drill_limit: int = 5,
    max_body_lines: int = 200,
) -> tuple[bytes, dict]:
    """
    Wycinek szkieletu pod zapytanie plus ciala najlepiej trafionych symboli.

    Ciala dociagamy przez ponowne zbudowanie indeksu z bajtow — po jednym parsowaniu
    na PLIK, nie na symbol. Przy piaciu celach z trzech plikow to trzy parsowania,
    a nie piec.

    Ucinanie dlugiego ciala jest jawne: w tresci laduje wiersz z liczba linii oryginalu.
    Ciche ucinanie zamienialoby oszczednosc tokenow w gubienie kodu.
    """
    terms = query_terms(query)
    outline, drill = select(entries, terms, outline_limit, drill_limit)

    # Grupujemy po pliku, zeby kazdy plik sparsowac raz.
    wanted: dict[str, list[str]] = {}
    for item in drill:
        wanted.setdefault(str(item["path"]), []).append(str(item["row"]["name_path"]))

    bodies: list[dict] = []
    for path in sorted(wanted):
        try:
            idx = index_from_bytes(path, reader.read(path))
        except (OSError, Exception):  # noqa: B014 — brak ciala nie moze wywrocic wycinka
            continue
        for name_path in sorted(wanted[path]):
            text = body_of(idx, name_path)
            if text is None:
                continue
            body_lines = text.split("\n")
            truncated = len(body_lines) > max_body_lines
            bodies.append({
                "path": path,
                "name_path": name_path,
                "text": "\n".join(body_lines[:max_body_lines]),
                "truncated": truncated,
                "total_lines": len(body_lines),
            })

    text = _render(query, terms, outline, bodies)
    meta = {
        "terms": terms,
        "outline_symbols": len(outline),
        "drilled": len(bodies),
        "files": len({str(i["path"]) for i in outline}),
    }
    return text, meta
