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

# Docstring wazy tyle co sygnatura. To jedyne pole, w ktorym kod jest opisany JEZYKIEM
# NATURALNYM, wiec jako jedyne lapie pytania zadane opisem zamiast identyfikatorem.
W_DOC = 2

# Gorny limit wagi rzadkosci. Bez niego termin wystepujacy raz w calym repo (literowka,
# nazwa wlasna, przypadkowy identyfikator) dostawalby wage rowna liczbie symboli
# i jednym trafieniem przewracalby caly ranking.
#
# DLACZEGO 512, A NIE 64
# ----------------------
# Przy 64 sufit bil za nisko i SPLASZCZAL realne roznice: dla pytania
# „provenance memory write" termin `provenance` (~5 symboli) i `write` (~24 symbole)
# dostawaly identyczna wage 64. `provenance()` konczylo z 320 punktami — dokladnie tyle
# samo co `_write_vm_log` i `_write_status` — a remis rozstrzygala sciezka alfabetycznie,
# wiec odpowiedz wypadala poza drill. Sufit ma chronic przed df=1, a nie zrownywac
# terminu bardzo rzadkiego ze srednio czestym.
RARITY_CAP = 512


def query_terms(text: str, min_len: int = 3) -> list[str]:
    """Rozbior zapytania na terminy. Ta sama regula co w baseline z M0."""
    terms = {
        t for t in TERM_RE.findall(text.lower())
        if len(t) >= min_len and t not in STOPWORDS
    }
    return sorted(terms)


def _haystack(path: str, row: Mapping[str, object]) -> str:
    return (
        f"{path} {row.get('name_path') or ''} "
        f"{row.get('signature') or ''} {row.get('doc') or ''}"
    ).lower()


def term_rarity(entries: Sequence[Mapping[str, object]], terms: Sequence[str]) -> dict[str, int]:
    """
    Waga terminu odwrotnie proporcjonalna do tego, jak czesto pada w repo.

    DLACZEGO TO JEST KONIECZNE
    --------------------------
    Bez tego kazdy termin wazy tyle samo, a wtedy wygrywa termin CZESTY, nie ISTOTNY.
    Zmierzone na zywym repo dla pytania „how is provenance recorded on memory writes":
    `CBMSMemory` dostawal 6 punktow (trafienie w czeste „memory" w nazwie, sygnaturze
    I sciezce), a funkcja `provenance()` tylko 5 (rzadkie „provenance" w nazwie
    i sygnaturze) — czyli odpowiedz przegrywala z tlem.

    Waga jest CALKOWITA (zadnych floatow w porzadkowaniu) i ograniczona z gory, zeby
    literowka wystepujaca raz w calym repo nie zmiotla rankingu jednym trafieniem.
    """
    if not terms:
        return {}
    df = {term: 0 for term in terms}
    total = 0
    for entry in entries:
        path = str(entry["path"])
        for row in entry["symbols"]:  # type: ignore[index]
            total += 1
            hay = _haystack(path, row)
            for term in terms:
                if term in hay:
                    df[term] += 1
    return {term: max(1, min(RARITY_CAP, total // (1 + df[term]))) for term in terms}


def score_symbol(
    path: str,
    row: Mapping[str, object],
    terms: Sequence[str],
    rarity: Mapping[str, int] | None = None,
) -> int:
    """
    Punkty symbolu dla zapytania. Bez `rarity` kazdy termin wazy 1 — tak licza testy
    jednostkowe wag pol; `select` zawsze podaje wagi rzadkosci policzone na calym zbiorze.
    """
    if not terms:
        return 0
    weights = rarity or {}
    name = str(row.get("name_path") or "").lower()
    signature = str(row.get("signature") or "").lower()
    doc = str(row.get("doc") or "").lower()
    low_path = path.lower()

    score = 0
    for term in terms:
        pola = (
            W_NAME * (term in name)
            + W_SIGNATURE * (term in signature)
            + W_DOC * (term in doc)
            + W_PATH * (term in low_path)
        )
        if pola:
            score += weights.get(term, 1) * pola
    return score


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
    rarity = term_rarity(entries, terms)
    ranked: list[dict] = []
    for entry in entries:
        path = str(entry["path"])
        for row in entry["symbols"]:  # type: ignore[index]
            score = score_symbol(path, row, terms, rarity)
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
    ranked: Sequence[Mapping[str, object]] | None = None,
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
        # Tylko OSError. Plik doszedl az tutaj przez collect_entries, wiec ma gramatyke
        # i da sie sparsowac — gdyby jednak nie dal, ma byc glosno, a nie po cichu.
        # To ta sama regula, ktora wytykamy scan_dir w ts_symbols.py (:282-283).
        try:
            idx = index_from_bytes(path, reader.read(path))
        except OSError:
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
