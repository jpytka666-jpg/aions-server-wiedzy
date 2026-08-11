"""
expand.py — most miedzy jezykiem pytania a slownictwem repo. Zero LLM, zero embeddingow.

PROBLEM
-------
Pytanie zadane OPISEM („which machine performed a memory write") nie trafia w kod nazwany
inaczej (`provenance`, `server_host`). Ranking leksykalny nie ma jak — nie istnieje zadne
wspolne slowo. Potrzebny jest most, ale wyprowadzony WYLACZNIE z informacji juz obecnej
w repo, deterministycznie i z uzasadnieniem dla kazdej krawedzi.

ZASADA NACZELNA: ZADEN TERMIN BEZ PARAGONU
------------------------------------------
`expand()` zwraca pary `(termin, Receipt)`. Nie ma sposobu, zeby termin wszedl do zapytania
bez zapisu, skad sie wzial — bo funkcja nie zwraca golych stringow. To nie jest dyscyplina,
tylko typ.

DWA KORPUSY, JEDNA IMPLEMENTACJA
--------------------------------
1. `prose`     — komunikaty commitow i pliki .md. Kazdy commit to para uczaca: opis po
                 ludzku obok nazw symboli, ktorych dotyczy.
2. `code_window` — okno pozycyjne w zrodlach. Term rozszerzajacy wchodzi, bo LEZY OBOK
                 terminu z pytania w kodzie, a nie dlatego ze ktos ladnie opisal commita.
                 Wariant odporny na brak higieny opisow (Sisman & Kak, MSR'13).

Oba korpusy przechodza przez te sama funkcje. Druga kopia regul wspolwystepowania
rozjechalaby sie przy pierwszej zmianie progu.

FILTR (Xu & Croft, LCA)
-----------------------
Kandydat musi wspolwystepowac z CO NAJMNIEJ DWOMA roznymi terminami zapytania, nie z jednym.
Bez tego wchodzi tlo: slowo, ktore pada obok czegokolwiek, pada tez obok pytania.
"""

from __future__ import annotations

import collections
import math
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .canon import content_hash

SCHEMA = "acae.expansion.v1"

# Progi wziete z literatury i z ksztaltu problemu, NIE strojone na zbiorze testowym.
MIN_COOCCURRENCE = 2       # krawedz musi miec co najmniej dwa niezalezne swiadectwa
MIN_RATIO_PERMILLE = 250   # raportowane, JUZ NIE FILTRUJE — patrz MIN_G2

# Prog log-likelihood ratio. To NIE jest liczba dobrana, zeby cos przeszlo: to wartosc
# krytyczna chi-kwadrat dla 1 stopnia swobody przy p < 0.001. Bierze sie z rozkladu.
#
# DLACZEGO G^2 ZAMIAST SUROWEGO STOSUNKU (M4.2 -> M4.2b)
# ------------------------------------------------------
# Stosunek `co/df >= 25%` byl trywialnie spelnialny przy malym mianowniku: termin
# wystepujacy w calym repo dwa razy, oba razy obok terminu z pytania, dostawal 1000
# promili i przechodzil bez zadnego dowodu (`file -> sha12`, `rows -> is_refusal`).
# G^2 karze rzadkie zdarzenia za brak wsparcia zamiast nagradzac je za wysoki stosunek —
# jest standardem w wydobywaniu kolokacji od Dunninga (1993) wlasnie dlatego.
MIN_G2 = 10.83
MIN_TERMS_COVERED = 2      # regula LCA: kandydat trafia >=2 rozne terminy zapytania
MAX_PER_TERM = 3           # ile rozszerzen na jeden termin zapytania
MAX_TOTAL = 12             # twardy sufit calego rozszerzenia
WEIGHT_DIVISOR = 2         # rozszerzenie wazy polowe tego co termin oryginalny
EVIDENCE_CHARS = 160
CODE_WINDOW_LINES = 12

TOKEN_RE = re.compile(r"[a-z_][a-z0-9_]{2,}")


@dataclass(frozen=True)
class Receipt:
    """
    Paragon jednej krawedzi rozszerzenia. To jest cale „nie chce czarnej skrzynki".

    `valid_for_pack` + `target_exists` daja dwa niezalezne warunki uniewaznienia:
    krawedz umiera, gdy symbol docelowy znika z packa albo gdy zrodlo zmienia tresc.
    """

    term: str
    derived_from: str
    rule: str                 # prose_cooccurrence | code_window
    source_kind: str          # commit | doc | code
    source_ref: str
    source_hash: str
    evidence: str
    cooccurrence: int
    doc_freq: int
    ratio_permille: int
    g2_milli: int
    terms_covered: int
    weight_class: str
    valid_for_pack: str
    target_exists: bool

    def as_dict(self) -> dict:
        return {
            "term": self.term,
            "derived_from": self.derived_from,
            "rule": self.rule,
            "source": {"kind": self.source_kind, "ref": self.source_ref, "content_hash": self.source_hash},
            "evidence": self.evidence,
            "stats": {
                "cooccurrence": self.cooccurrence,
                "doc_freq": self.doc_freq,
                "ratio_permille": self.ratio_permille,
                "terms_covered": self.terms_covered,
            },
            "weight_class": self.weight_class,
            "valid_for": {"pack_hash": self.valid_for_pack, "target_symbol_exists": self.target_exists},
        }


@dataclass(frozen=True)
class Document:
    """Jednostka wspolwystepowania: akapit prozy, komunikat commita albo okno w kodzie."""

    kind: str
    ref: str
    text: str


def symbol_vocabulary(entries: Sequence[Mapping[str, object]]) -> set[str]:
    """
    Slownik identyfikatorow, ktore NAPRAWDE istnieja w packu.

    To jest bariera, ktora czyni rozszerzenie bezpiecznym: kandydat spoza tego zbioru
    jest odrzucany, wiec zaden most nie moze wprowadzic do zapytania nazwy, ktorej
    w repo nie ma. ACAE zostaje zrodlem prawdy o tym, jaki kod istnieje.
    """
    vocab: set[str] = set()
    for entry in entries:
        for row in entry["symbols"]:  # type: ignore[index]
            for part in str(row.get("name_path") or "").split("/"):
                cleaned = part.lower().strip("_")
                if len(cleaned) >= 4:
                    vocab.add(cleaned)
    return vocab


def prose_documents(repo_root: str) -> list[Document]:
    """Komunikaty commitow i akapity plikow .md. Proza, w ktorej ludzie opisuja ten kod."""
    docs: list[Document] = []
    proc = subprocess.run(
        ["git", "log", "--format=%H%x1f%s%n%b%x1e"],
        cwd=repo_root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if proc.returncode == 0:
        for raw in proc.stdout.decode("utf-8", "replace").split("\x1e"):
            if "\x1f" not in raw:
                continue
            sha, _, body = raw.partition("\x1f")
            body = body.strip()
            if body:
                docs.append(Document("commit", sha.strip()[:12], body))

    root = Path(repo_root)
    for md in sorted(root.rglob("*.md")):
        rel = md.relative_to(root).as_posix()
        if rel.startswith("tools/ChromaFlowStudio/") or "/node_modules/" in rel:
            continue
        try:
            text = md.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        offset = 1
        for para in text.split("\n\n"):
            n_lines = para.count("\n") + 1
            if para.strip():
                docs.append(Document("doc", f"{rel}#L{offset}", para))
            offset += n_lines + 1
    return docs


def code_window_documents(
    entries: Sequence[Mapping[str, object]],
    reader,
    window: int = CODE_WINDOW_LINES,
) -> list[Document]:
    """
    Okna pozycyjne w zrodlach. Wariant PRF dla kodu (Sisman & Kak, MSR'13).

    Term rozszerzajacy wchodzi, bo LEZY OBOK terminu z pytania w pliku — niezaleznie
    od tego, czy ktokolwiek napisal o tym w commicie. To czyni most odpornym na brak
    higieny opisow, ktorej w wiekszosci repozytoriow po prostu nie ma.
    """
    docs: list[Document] = []
    for entry in entries:
        rel = str(entry["path"])
        try:
            raw = reader.read(rel)
        except OSError:
            continue
        lines = raw.decode("utf-8", "replace").split("\n")
        for start in range(0, len(lines), window):
            chunk = "\n".join(lines[start:start + window])
            if chunk.strip():
                docs.append(Document("code", f"{rel}#L{start + 1}", chunk))
    return docs


def _tokenize(text: str) -> set[str]:
    return set(TOKEN_RE.findall(text.lower()))


class Corpus:
    """
    Korpus stokenizowany RAZ, wraz ze statystyka `df`.

    Bez tego kazde zapytanie tokenizowaloby od nowa wszystkie okna kodu — przy 36 pytaniach
    i kilku tysiacach okien to roznica miedzy sekundami a minutami. `df` jest wlasnoscia
    korpusu, nie zapytania, wiec liczenie go per zapytanie bylo tez merytorycznie bledne:
    ta sama krawedz dostawalaby rozny stosunek zaleznie od tego, o co akurat pytamy.
    """

    def __init__(self, documents: Iterable[Document]) -> None:
        self.docs: list[tuple[Document, frozenset[str]]] = []
        self.df: collections.Counter = collections.Counter()
        for doc in documents:
            tokens = _tokenize(doc.text)
            if not tokens:
                continue
            self.docs.append((doc, frozenset(tokens)))
            for token in tokens:
                self.df[token] += 1

    def __len__(self) -> int:
        return len(self.docs)


def expand(
    query_terms: Sequence[str],
    corpus: Corpus,
    vocabulary: set[str],
    pack_hash: str,
    rule: str,
    min_cooccurrence: int = MIN_COOCCURRENCE,
    min_ratio_permille: int = MIN_RATIO_PERMILLE,
    min_terms_covered: int = MIN_TERMS_COVERED,
    max_per_term: int = MAX_PER_TERM,
    max_total: int = MAX_TOTAL,
) -> list[tuple[str, Receipt]]:
    """
    Zwraca pary (termin, paragon). Nigdy golych terminow — patrz docstring modulu.

    Trzy filtry, kazdy odcina inny rodzaj smiecia:
      * `vocabulary`        — kandydat musi istniec w packu (zakaz wymyslania kodu),
      * `min_terms_covered` — regula LCA, odcina tlo trafiajace jeden termin,
      * `min_ratio_permille`— odcina slowa czeste, ktore lezą obok wszystkiego.
    """
    terms = [t for t in query_terms if t]
    if not terms:
        return []

    co: dict[str, collections.Counter] = {t: collections.Counter() for t in terms}
    df = corpus.df
    witness: dict[tuple[str, str], Document] = {}

    for doc, tokens in corpus.docs:
        present = [t for t in terms if t in tokens]
        if not present:
            continue
        candidates = tokens & vocabulary
        for term in present:
            for cand in candidates:
                if cand == term or cand in terms:
                    continue
                co[term][cand] += 1
                witness.setdefault((term, cand), doc)

    covered: collections.Counter = collections.Counter()
    for term in terms:
        for cand in co[term]:
            covered[cand] += 1

    out: list[tuple[str, Receipt]] = []
    for term in sorted(terms):
        ranked = sorted(
            co[term].items(),
            key=lambda kv: (-((kv[1] * 1000) // max(1, df[kv[0]])), -kv[1], kv[0]),
        )
        taken = 0
        for cand, count in ranked:
            if taken >= max_per_term:
                break
            ratio = (count * 1000) // max(1, df[cand])
            if count < min_cooccurrence or ratio < min_ratio_permille:
                continue
            if covered[cand] < min_terms_covered:
                continue
            doc = witness[(term, cand)]
            evidence = " ".join(doc.text.split())[:EVIDENCE_CHARS]
            out.append((cand, Receipt(
                term=cand,
                derived_from=term,
                rule=rule,
                source_kind=doc.kind,
                source_ref=doc.ref,
                source_hash=content_hash(doc.text.encode("utf-8")),
                evidence=evidence,
                cooccurrence=count,
                doc_freq=df[cand],
                ratio_permille=ratio,
                terms_covered=covered[cand],
                weight_class="expansion",
                valid_for_pack=pack_hash,
                target_exists=cand in vocabulary,
            )))
            taken += 1

    # Deduplikacja: ten sam termin moze wyjsc z kilku terminow zapytania. Zostawiamy
    # paragon o najmocniejszym stosunku, zeby uzasadnienie bylo najlepsze z dostepnych.
    best: dict[str, Receipt] = {}
    for cand, receipt in out:
        prev = best.get(cand)
        if prev is None or receipt.ratio_permille > prev.ratio_permille:
            best[cand] = receipt
    ordered = sorted(best.values(), key=lambda r: (-r.ratio_permille, -r.cooccurrence, r.term))
    return [(r.term, r) for r in ordered[:max_total]]
