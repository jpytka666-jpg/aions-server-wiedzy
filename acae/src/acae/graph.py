"""
graph.py — propagacja po grafie wywolan (M4.4). Zero LLM, zero embeddingow, zero floatow.

PROBLEM
-------
`ts_symbols.SymbolIndex` daje dla kazdego symbolu pole `refs` — zbior nazw wywolywanych
funkcji i importow. `symbols.outline_rows` zapisuje z tego TYLKO liczbe (`n_refs`),
a same krawedzie wyrzuca. Ranking leksykalny nie ma wiec dostepu do struktury: symbol
nazwany inaczej niz pytanie nie ma jak wyplynac, nawet jesli lezy jedno wywolanie
od symbolu, ktory ranker juz trafil.

DLACZEGO NIE PLASKA PROPAGACJA
------------------------------
Zmierzone w prototypie: plaskie rozlewanie punktow z tlumieniem 1/2 WZMACNIA szum.
`DifferentiableMemory/write` urosl z 873 na 1489 i dalej dominowal ranking — bo hub
dostaje wklad od wszystkiego, co go wola. Punkt rozlany rowno po sasiadach premiuje
stopien wierzcholka, a stopien wierzcholka nie jest trafnoscia.

HEURYSTYKI SUADE (Robillard, TOSEM'08)
-------------------------------------
Zamiast rownego rozlewania kazda krawedz jest wazona dwoma niezaleznymi wielkosciami:

  specificity(x)   — element wskazujacy na NIEWIELU sasiadow niesie sygnal; hub
                     wskazujacy na wszystkich nie niesie nic.  spec(x) = 1 / |N(x)|
  reinforcement(y) — element wskazywany przez WIELU juz-trafnych rosnie.
                     reinf(y) = |N(y) ∩ S| / |N(y)|,  gdzie S to zbior zainteresowania

  wklad krawedzi   = spec(x) ⊗ reinf(y)          (iloczyn)
  laczenie wkladow = x ⊕ y = x + y - x*y         (przedzial [0,1], monotoniczne,
                                                  nasycajace — dziesiec slabych krawedzi
                                                  nie przebije jednej mocnej)

To odwraca logike prototypu: hub jest teraz KARANY przez specificity swojego zrodla,
a nie nagradzany przez liczbe wchodzacych krawedzi.

ARYTMETYKA CALKOWITA
--------------------
Wszystko w PROMILACH (0..1000). Zaden float nie dotyka porzadkowania — inaczej
kolejnosc dwoch symboli o „tym samym" wyniku zalezalaby od bitow mantysy i wynik
pomiaru nie bylby odtwarzalny miedzy maszynami.

Iloczyn spec ⊗ reinf liczymy JEDNYM dzieleniem, nie dwoma:
    spec ⊗ reinf = (1/|N(x)|) * (k/|N(y)|) = k / (|N(x)| * |N(y)|)
    w promilach:   (1000 * k) // (|N(x)| * |N(y)|)
Dwa osobne dzielenia calkowite gubilyby na kazdym z nich; jedno gubi raz.

Laczenie ⊕ jest w liczbach rzeczywistych laczne, ale przy dzieleniu calkowitym
JUZ NIE — (a⊕b)⊕c moze roznic sie o 1 promil od a⊕(b⊕c). Dlatego wklady sa
skladane w USTALONEJ kolejnosci: malejaco po wartosci, remis po kluczu wezla.

WIELOZNACZNOSC `refs` — ROZSTRZYGNIETE JAWNIE
---------------------------------------------
`refs` to MIEKKIE wskazowki: gole nazwy, czasem kropkowane (`acae.canon.content_hash`,
`obj.method`). Ta sama nazwa liscia (`write`, `run`, `__init__`) pada w kilkunastu
plikach. ACAE nie ma resolvera i nie bedzie go udawac. Regula jest nastepujaca
i jest calkowicie deterministyczna:

  1. Token normalizujemy do OSTATNIEGO segmentu po kropce (`a.b.foo` -> `foo`).
     Dopasowanie jest doslowne (case-sensitive) do liscia `name_path`, bo i nazwy,
     i referencje pochodza z tego samego tekstu zrodlowego.
  2. Kandydatami sa wszystkie symbole o takim lisciu.
  3. LOKALNOSC WYGRYWA: jesli ktorykolwiek kandydat lezy w TYM SAMYM PLIKU co zrodlo,
     zostawiamy wylacznie kandydatow z tego pliku i konczymy. To jedyny przypadek,
     ktory da sie rozstrzygnac bez resolvera, i akurat najczestszy.
  4. W przeciwnym razie: jesli kandydatow jest WIECEJ NIZ `MAX_AMBIGUITY`, referencja
     jest ODRZUCANA W CALOSCI. Nazwa pasujaca do pieciu miejsc nie mowi nic o tym,
     do ktorego z nich; zachowanie wszystkich pieciu to dokladnie ten szum, ktory
     przewrocil prototyp.
  5. Jesli kandydatow jest 2..`MAX_AMBIGUITY`, zostaja WSZYSCY, kazdy jako osobna
     krawedz. Nie zgadujemy — ich liczba wchodzi do `specificity` zrodla, wiec
     referencja wieloznaczna sama sie rozciencza. To jest cala kara za niepewnosc.
  6. Petle wlasne (x -> x) sa odrzucane.

PARAMETRY — PREREJESTROWANE, USTALONE PRZED POMIAREM
----------------------------------------------------
  SEED_K         = 10   zbior zainteresowania S = 10 najlepszych z rankera leksykalnego
                        (dokladnie to, w co ranker aktualnie wierzy; recall@10 jest
                        naglowkowa metryka, wiec to naturalna granica)
  HOPS           = 2    ile skokow po grafie
  HOP2_K         = 25   S dla drugiego skoku = 25 najlepszych wynikow pierwszego
  DAMP_PERMILLE  = 500  wklad drugiego skoku tlumiony o polowe
  MAX_AMBIGUITY  = 4    powyzej tylu kandydatow referencja jest odrzucana (pkt 4)

Modul nie dotyka dysku: zrodla przychodza przez port Reader.
"""

from __future__ import annotations

from typing import Iterable, Mapping, Sequence

from .ports import Reader
from .symbols import NoGrammar, index_from_bytes

SCHEMA = "acae.graph.v1"

SEED_K = 10
HOPS = 2
HOP2_K = 25
DAMP_PERMILLE = 500
MAX_AMBIGUITY = 4

# Klucz wezla. Sam `name_path` nie wystarcza — `__init__` istnieje w kazdym module,
# a to sa rozne funkcje. Sciezka jest czescia tozsamosci wezla, nie ozdoba.
NodeKey = tuple[str, str]


def combine(a: int, b: int) -> int:
    """
    Laczenie Suade w promilach: x ⊕ y = x + y - x*y.

    Nasycajace i monotoniczne w [0, 1000]: dowolna liczba slabych swiadectw nie
    przekroczy 1000, a dolozenie swiadectwa nigdy nie obniza wyniku. To jest wlasnie
    powod, dla ktorego Suade uzywa tego zamiast sumy — suma premiowalaby stopien.
    """
    return a + b - (a * b) // 1000


def _leaf(name_path: str) -> str:
    return name_path.rsplit("/", 1)[-1]


def _ref_token(ref: str) -> str:
    """Ostatni segment po kropce. `acae.canon.content_hash` -> `content_hash`."""
    return ref.strip().rsplit(".", 1)[-1].strip()


class CallGraph:
    """
    Graf wywolan nad symbolami packa. Zbudowany raz, uzywany przez wszystkie zapytania.

    Trzyma obie strony kazdej krawedzi, bo Suade propaguje w obie: „to, co wola
    trafiony symbol" i „to, co trafiony symbol wola" sa dwoma roznymi swiadectwami
    i musza byc liczone osobno.
    """

    def __init__(self, edges: Iterable[tuple[NodeKey, NodeKey]], nodes: Iterable[NodeKey]) -> None:
        self.nodes: tuple[NodeKey, ...] = tuple(sorted(set(nodes)))
        out: dict[NodeKey, set[NodeKey]] = {}
        inc: dict[NodeKey, set[NodeKey]] = {}
        for src, dst in edges:
            if src == dst:
                continue
            out.setdefault(src, set()).add(dst)
            inc.setdefault(dst, set()).add(src)
        # frozenset + posortowana krotka: iterujemy po krotce, testujemy po zbiorze.
        self.out: dict[NodeKey, tuple[NodeKey, ...]] = {k: tuple(sorted(v)) for k, v in out.items()}
        self.inc: dict[NodeKey, tuple[NodeKey, ...]] = {k: tuple(sorted(v)) for k, v in inc.items()}
        self._out_set: dict[NodeKey, frozenset[NodeKey]] = {k: frozenset(v) for k, v in out.items()}
        self._inc_set: dict[NodeKey, frozenset[NodeKey]] = {k: frozenset(v) for k, v in inc.items()}

    @property
    def n_edges(self) -> int:
        return sum(len(v) for v in self.out.values())

    def _spread(self, interest: frozenset[NodeKey]) -> dict[NodeKey, tuple[int, list[NodeKey]]]:
        """
        Jeden skok Suade. Zwraca wezel -> (wynik w promilach, zrodla wkladu).

        Zrodla wkladu ida do paragonu: krawedz bez zapisu, skad sie wziela, jest
        nieodrozninalna od zgadywania.
        """
        raw: dict[NodeKey, list[tuple[int, NodeKey]]] = {}

        def add(target: NodeKey, value: int, source: NodeKey) -> None:
            if value > 0:
                raw.setdefault(target, []).append((value, source))

        # W PRZOD: x nalezy do S, x wola y. spec liczona po WYCHODZACYCH z x,
        # reinf po WCHODZACYCH do y.
        for x in sorted(interest):
            outs = self.out.get(x, ())
            if not outs:
                continue
            for y in outs:
                if y in interest:
                    continue
                ins_y = self._inc_set.get(y, frozenset())
                if not ins_y:
                    continue
                k = len(ins_y & interest)
                add(y, (1000 * k) // (len(outs) * len(ins_y)), x)

        # WSTECZ: y nalezy do S, x wola y. spec liczona po WCHODZACYCH do y,
        # reinf po WYCHODZACYCH z x. Symetryczne, ale to inne swiadectwo:
        # „ktos wola trafiony symbol" nie znaczy tego samego co „trafiony symbol wola".
        for y in sorted(interest):
            ins = self.inc.get(y, ())
            if not ins:
                continue
            for x in ins:
                if x in interest:
                    continue
                outs_x = self._out_set.get(x, frozenset())
                if not outs_x:
                    continue
                k = len(outs_x & interest)
                add(x, (1000 * k) // (len(ins) * len(outs_x)), y)

        result: dict[NodeKey, tuple[int, list[NodeKey]]] = {}
        for node, items in raw.items():
            # Kolejnosc skladania ustalona: malejaco po wartosci, remis po kluczu.
            # Bez tego (a⊕b)⊕c i a⊕(b⊕c) roznia sie o promil przy dzieleniu calkowitym.
            items.sort(key=lambda it: (-it[0], it[1]))
            acc = 0
            for value, _ in items:
                acc = combine(acc, value)
            result[node] = (acc, [src for _, src in items])
        return result

    def propagate(
        self,
        seeds: Iterable[NodeKey],
        hops: int = HOPS,
        hop2_k: int = HOP2_K,
        damp_permille: int = DAMP_PERMILLE,
    ) -> dict[NodeKey, int]:
        """
        Wynik propagacji w promilach dla kazdego wezla SPOZA zbioru zasiewu.

        Zasiew nie dostaje nic: to sa symbole, ktore ranker leksykalny juz znalazl,
        a propagacja ma dokladac informacje, ktorej ranker NIE MA. Doliczanie punktow
        temu, co i tak jest na gorze, tylko rozciagaloby skale.
        """
        return {node: value for node, (value, _) in self.propagate_with_sources(
            seeds, hops=hops, hop2_k=hop2_k, damp_permille=damp_permille,
        ).items()}

    def propagate_with_sources(
        self,
        seeds: Iterable[NodeKey],
        hops: int = HOPS,
        hop2_k: int = HOP2_K,
        damp_permille: int = DAMP_PERMILLE,
    ) -> dict[NodeKey, tuple[int, list[NodeKey]]]:
        """Jak `propagate`, ale z lista wezlow, ktore wnioslyy wklad — do paragonu."""
        seed_set = frozenset(seeds)
        if not seed_set or hops < 1:
            return {}

        first = self._spread(seed_set)
        total: dict[NodeKey, tuple[int, list[NodeKey]]] = dict(first)

        if hops >= 2 and first:
            ordered = sorted(first.items(), key=lambda it: (-it[1][0], it[0]))
            interest2 = frozenset(node for node, _ in ordered[:hop2_k])
            if interest2:
                for node, (value, sources) in self._spread(interest2).items():
                    if node in seed_set:
                        continue
                    damped = (value * damp_permille) // 1000
                    if damped <= 0:
                        continue
                    prev_value, prev_sources = total.get(node, (0, []))
                    merged = sorted(set(prev_sources) | set(sources))
                    total[node] = (combine(prev_value, damped), merged)

        return {node: pair for node, pair in total.items() if node not in seed_set and pair[0] > 0}


def build_graph(
    entries: Sequence[Mapping[str, object]],
    reader: Reader,
    max_ambiguity: int = MAX_AMBIGUITY,
) -> CallGraph:
    """
    Graf z `refs`. Pliki parsowane RAZ, po jednym parsowaniu na plik.

    `refs` nie ma w wierszach outline'u i CELOWO tam nie trafia: dopisanie pola do
    `outline_rows` zmienilo by `pack_hash`, a zaden mechanizm M4 nie ma prawa ruszyc
    artefaktu. Dlatego graf odczytuje je z wlasnego przebiegu po tych samych bajtach.

    Wieloznacznosc rozstrzygana wedlug reguly opisanej w docstringu modulu.
    """
    nodes: list[NodeKey] = []
    # lisc -> wezly o tym lisciu; posortowane, zeby kolejnosc krawedzi byla ustalona
    by_leaf: dict[str, list[NodeKey]] = {}
    refs_of: dict[NodeKey, tuple[str, ...]] = {}

    for entry in entries:
        rel = str(entry["path"])
        try:
            raw = reader.read(rel)
        except OSError:
            continue
        try:
            idx = index_from_bytes(rel, raw)
        except NoGrammar:
            continue
        for name_path, sym in idx.symbols.items():
            key = (rel, name_path)
            nodes.append(key)
            by_leaf.setdefault(_leaf(name_path), []).append(key)
            refs_of[key] = tuple(sorted(sym.refs or ()))

    for leaf in by_leaf:
        by_leaf[leaf].sort()

    edges: list[tuple[NodeKey, NodeKey]] = []
    for key in sorted(refs_of):
        src_path, src_name = key
        for ref in refs_of[key]:
            token = _ref_token(ref)
            if not token:
                continue
            candidates = by_leaf.get(token)
            if not candidates:
                continue
            local = [c for c in candidates if c[0] == src_path and c[1] != src_name]
            if local:
                targets = local                      # regula 3: lokalnosc wygrywa
            elif len(candidates) > max_ambiguity:
                continue                             # regula 4: nazwa-hub odrzucona
            else:
                targets = [c for c in candidates if c != key]   # regula 5
            for dst in targets:
                edges.append((key, dst))

    return CallGraph(edges, nodes)
