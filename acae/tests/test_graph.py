"""
Testy propagacji po grafie wywolan (M4.4).

Mechanizm zostal ZMIERZONY I ODRZUCONY — nie przeszedl prerejestrowanego kryterium
na zbiorze roboczym. Testy pilnuja, ze to, co odrzucilismy, bylo POPRAWNE: wynik
negatywny z zepsuta implementacja nie znaczy nic.
"""

from __future__ import annotations

from conftest import MemoryLocator, MemoryReader

from acae.core import collect_entries
from acae.graph import CallGraph, build_graph, combine

A = ("pkg/a.py", "alpha")
B = ("pkg/a.py", "beta")
C = ("pkg/b.py", "gamma")
D = ("pkg/b.py", "delta")


def _graph(edges, nodes=None):
    nodes = nodes or sorted({n for edge in edges for n in edge})
    return CallGraph(edges, nodes)


# ------------------------------------------------------------------ laczenie Suade

def test_combine_jest_neutralne_dla_zera():
    assert combine(0, 400) == 400
    assert combine(400, 0) == 400


def test_combine_nie_przekracza_tysiaca():
    """Dowolna liczba slabych swiadectw nie moze przebic sufitu — inaczej wygrywa stopien."""
    acc = 0
    for _ in range(50):
        acc = combine(acc, 300)
    assert acc <= 1000


def test_combine_jest_monotoniczne():
    """Dolozenie swiadectwa nigdy nie obniza wyniku."""
    for a in (0, 100, 500, 900, 1000):
        for b in (0, 50, 250, 750):
            assert combine(a, b) >= a


# ------------------------------------------------------------------- tozsamosc wezla

def test_ten_sam_lisc_w_roznych_plikach_to_rozne_wezly():
    """`__init__` istnieje w kazdym module. Bez sciezki w kluczu byłby jednym wezlem."""
    x = ("pkg/a.py", "Klasa/__init__")
    y = ("pkg/b.py", "Klasa/__init__")
    graph = _graph([(x, A), (y, C)])
    z_x = graph.propagate([x])
    z_y = graph.propagate([y])
    assert A in z_x and A not in z_y
    assert C in z_y and C not in z_x


# -------------------------------------------------------------------- propagacja

def test_zasiew_nie_dostaje_premii():
    """Propagacja ma dokladac informacje, ktorej ranker NIE MA."""
    graph = _graph([(A, B)])
    assert A not in graph.propagate([A])


def test_sasiad_zasiewu_dostaje_premie():
    graph = _graph([(A, B)])
    assert graph.propagate([A]).get(B, 0) > 0


def test_specificity_karze_huby():
    """
    Zrodlo wskazujace na wielu sasiadow niesie slabszy sygnal na kazdego z nich
    niz zrodlo wskazujace na jednego. To jest cala roznica wobec plaskiego tlumienia,
    ktore w prototypie wzmacnialo szum.
    """
    waskie = _graph([(A, B)])
    szerokie = _graph([(A, B), (A, C), (A, D), (A, ("pkg/c.py", "eps")), (A, ("pkg/c.py", "zeta"))])
    assert waskie.propagate([A])[B] > szerokie.propagate([A])[B]


def test_reinforcement_nagradza_wskazywanie_przez_wielu():
    """Wezel wskazywany przez DWA trafione zrodla ma dostac wiecej niz wskazywany przez jedno."""
    graph = _graph([(A, D), (C, D)])
    jeden = graph.propagate([A]).get(D, 0)
    dwa = graph.propagate([A, C]).get(D, 0)
    assert dwa > jeden


def test_brak_krawedzi_to_brak_zmiany():
    graph = _graph([], nodes=[A, B])
    assert graph.propagate([A]) == {}


def test_pusty_zasiew_nic_nie_zwraca():
    assert _graph([(A, B)]).propagate([]) == {}


def test_cykl_nie_zawiesza_propagacji():
    """Graf wywolan bywa cykliczny. Propagacja ma sie zatrzymac na liczbie skokow."""
    graph = _graph([(A, B), (B, C), (C, A)])
    wynik = graph.propagate([A])
    assert isinstance(wynik, dict) and A not in wynik


def test_propagacja_jest_powtarzalna():
    graph = _graph([(A, B), (B, C), (A, D)])
    assert graph.propagate([A]) == graph.propagate([A])


def test_paragon_wskazuje_zrodla_wkladu():
    """Bez tego premia z grafu bylaby czarna skrzynka — nie wiadomo, skad przyszla."""
    graph = _graph([(A, B)])
    wartosc, zrodla = graph.propagate_with_sources([A])[B]
    assert wartosc > 0
    assert A in zrodla


# --------------------------------------------------------------- budowa z packa

def test_build_graph_czyta_refs_bez_ruszania_outline(blobs):
    """
    `refs` NIE moga trafic do wierszy outline'u — dopisanie pola zmienilo by pack_hash,
    a zaden mechanizm M4 nie ma prawa ruszyc artefaktu.
    """
    entries, _ = collect_entries(MemoryLocator(sorted(blobs)), MemoryReader(blobs))
    graph = build_graph(entries, MemoryReader(blobs))
    assert graph.n_edges >= 0
    for entry in entries:
        for row in entry["symbols"]:
            assert "refs" not in row


def test_build_graph_jest_powtarzalny(blobs):
    entries, _ = collect_entries(MemoryLocator(sorted(blobs)), MemoryReader(blobs))
    pierwszy = build_graph(entries, MemoryReader(blobs))
    drugi = build_graph(entries, MemoryReader(blobs))
    assert pierwszy.n_edges == drugi.n_edges
