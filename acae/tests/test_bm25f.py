"""
Testy BM25F (M4.1).

Modul zostal ZMIERZONY I ODRZUCONY jako ranker domyslny — nie przeszedl prerejestrowanego
kryterium na zbiorze roboczym. Zostaje w repo jako wynik negatywny z dzialajaca
implementacja, zeby dalo sie go zmierzyc ponownie, gdy zmieni sie reszta pipeline'u.
Testy pilnuja, ze to co odrzucilismy bylo POPRAWNE — inaczej wynik negatywny nie znaczy nic.
"""

from __future__ import annotations

from conftest import MemoryLocator, MemoryReader

from acae.bm25f import Bm25fIndex, prepare_terms, split_identifier
from acae.core import collect_entries
from acae.retrieve import query_terms


def _index(blobs):
    entries, _ = collect_entries(MemoryLocator(sorted(blobs)), MemoryReader(blobs))
    return Bm25fIndex(entries), entries


def test_split_identifier_tnie_snake_case():
    assert split_identifier("get_memory_stats") == ["get", "memory", "stats"]


def test_split_identifier_tnie_camel_case():
    assert split_identifier("withProvenance") == ["with", "provenance"]


def test_split_identifier_radzi_sobie_z_akronimem_przed_slowem():
    """CBMSMemory ma granice miedzy akronimem a slowem — bez tego wyszedlby jeden token."""
    assert split_identifier("CBMSMemory/get_stats") == ["cbms", "memory", "get", "stats"]


def test_split_identifier_odrzuca_tokeny_jednoznakowe():
    assert "x" not in split_identifier("f_x_value")


def test_prepare_terms_deduplikuje_i_zachowuje_kolejnosc():
    assert prepare_terms(["memory_store", "memory"]) == ["memory", "store"]


def test_dokumentem_jest_symbol_a_nie_plik(blobs):
    """Recall na poziomie pliku nie odroznilby dwoch funkcji w tym samym module."""
    index, entries = _index(blobs)
    assert index.n == sum(len(e["symbols"]) for e in entries)


def test_zapytanie_dokladna_nazwa_stawia_symbol_pierwszy(blobs):
    index, _ = _index(blobs)
    assert index.rank(query_terms("delta"), 3)[0]["row"]["name_path"] == "delta"


def test_ranking_jest_powtarzalny(blobs):
    index, _ = _index(blobs)
    first = [i["row"]["name_path"] for i in index.rank(["alpha", "beta"], 5)]
    assert first == [i["row"]["name_path"] for i in index.rank(["alpha", "beta"], 5)]


def test_brak_terminow_daje_pusty_ranking(blobs):
    index, _ = _index(blobs)
    assert index.rank([], 5) == []


def test_termin_nieobecny_nie_generuje_trafien(blobs):
    index, _ = _index(blobs)
    assert index.rank(["nieobecnytermin"], 5) == []


def test_idf_maleje_wraz_z_czestoscia(blobs):
    """Termin czesty musi wazyc mniej niz rzadki — to jest cale IDF."""
    index, _ = _index(blobs)
    czesty = max(index.df, key=lambda t: index.df[t])
    rzadki = min(index.df, key=lambda t: (index.df[t], t))
    assert index.idf(rzadki) >= index.idf(czesty)


def test_nasycenie_dziala_czyli_powtorzenia_nie_skaluja_sie_liniowo():
    """
    Dziesiate wystapienie terminu nie moze wazyc tyle co pierwsze.

    Bez nasycenia dlugi symbol wygrywalby samym powtarzaniem nazwy.
    """
    jeden = {"pkg/a.py": b"def memory():\n    return 1\n"}
    wiele = {"pkg/b.py": b"def memory_memory_memory_memory():\n    return 1\n"}
    idx_jeden, _ = _index(jeden)
    idx_wiele, _ = _index(wiele)
    s1 = idx_jeden.rank(["memory"], 1)[0]["score"]
    s4 = idx_wiele.rank(["memory"], 1)[0]["score"]
    assert s4 < 4 * s1
