"""
Testy trwalego cache sparsowanych outline'ow.

Najwazniejszy test w tym pliku to `test_cache_nie_zmienia_pack_hash`. Cache istnieje
WYLACZNIE po to, zeby bylo szybciej — w chwili, w ktorej zmienia artefakt, przestaje
byc optymalizacja i staje sie bledem. `pack_hash` jest przypiety w CONTRACT.md
i porownywalny miedzy dwudziestoma kilkoma pomiarami; gdyby cache go ruszyl,
cala tabela przestalaby cokolwiek znaczyc.

Drugi co do wagi to `test_zmiana_wersji_gramatyk_wyrzuca_caly_cache`. To jest ryzyko R9
z kontraktu: inna wersja gramatyki daje inny outline dla NIEZMIENIONEGO pliku.
Bez uniewaznienia po wersji cache podawalby stary ksztalt i `pack_hash` przestalby
opisywac to, co narzedzie naprawde widzi — po cichu, bez zadnego bledu.
"""

from __future__ import annotations

import json

import pytest
from conftest import MemoryLocator, MemoryReader

from acae.core import PackRequest, build_pack, collect_entries
from acae.parsecache import SCHEMA, load, save, wersje_gramatyk


@pytest.fixture
def porty(blobs):
    return MemoryLocator(sorted(blobs)), MemoryReader(blobs)


# ---------------------------------------------------- rownowaznosc z brakiem cache

def test_cache_nie_zmienia_pack_hash(porty):
    loc, rd = porty
    bez = build_pack(PackRequest(root="repo"), loc, rd)

    cache: dict = {}
    collect_entries(loc, rd, outline_cache=cache)   # zapelnia cache
    assert cache, "cache nie zostal zapelniony"

    # Drugi przebieg czyta juz WYLACZNIE z cache.
    entries_z, skipped_z = collect_entries(loc, rd, outline_cache=cache)
    entries_bez, skipped_bez = collect_entries(loc, rd)
    assert entries_z == entries_bez
    assert skipped_z == skipped_bez
    assert bez.pack_hash == build_pack(PackRequest(root="repo"), loc, rd).pack_hash


def test_cache_po_przejsciu_przez_json_daje_te_same_wpisy(porty, tmp_path):
    """
    Cache leci na dysk jako JSON, wiec musi przezyc serializacje BEZ ZMIANY TYPOW.
    Krotka zamieniona na liste albo liczba na tekst zmienilaby `pack_hash` po cichu.
    """
    loc, rd = porty
    cache: dict = {}
    entries_pierwsze, _ = collect_entries(loc, rd, outline_cache=cache)

    plik = tmp_path / "parse_cache.json"
    save(plik, cache)
    odczytany = load(plik)
    assert odczytany == cache

    entries_drugie, _ = collect_entries(loc, rd, outline_cache=odczytany)
    assert entries_drugie == entries_pierwsze


def test_pusty_cache_daje_ten_sam_wynik_co_brak_cache(porty):
    loc, rd = porty
    a, _ = collect_entries(loc, rd, outline_cache={})
    b, _ = collect_entries(loc, rd)
    assert a == b


# ------------------------------------------------------------ uniewaznianie

def test_zmiana_tresci_pliku_to_chybienie(blobs):
    """Jeden zmieniony bajt musi wymusic ponowne sparsowanie, nie odczyt ze starego wpisu."""
    loc = MemoryLocator(sorted(blobs))
    cache: dict = {}
    collect_entries(loc, MemoryReader(blobs), outline_cache=cache)
    klucze_przed = set(cache)

    zmienione = dict(blobs)
    zmienione["pkg/alpha.py"] = blobs["pkg/alpha.py"] + b"\ndef nowa():\n    return 3\n"
    entries, _ = collect_entries(loc, MemoryReader(zmienione), outline_cache=cache)

    assert set(cache) > klucze_przed, "cache nie dostal nowego wpisu"
    alpha = next(e for e in entries if e["path"] == "pkg/alpha.py")
    assert any(str(r["name_path"]) == "nowa" for r in alpha["symbols"])


def test_zmiana_wersji_gramatyk_wyrzuca_caly_cache(tmp_path):
    """
    Ryzyko R9: inna wersja gramatyki = inny outline dla niezmienionego pliku.
    Cache MUSI wtedy zostac odrzucony w calosci, a nie podac starego ksztaltu.
    """
    plik = tmp_path / "parse_cache.json"
    plik.write_text(json.dumps({
        "schema": SCHEMA,
        "grammars": {"tree-sitter": "0.0.1-inna", "tree-sitter-language-pack": "0.0.1-inna"},
        "entries": {"pkg/alpha.py\x00blake2b256:cokolwiek": [{"line": 1}]},
    }), encoding="utf-8")
    assert load(plik) == {}


def test_inny_schemat_wyrzuca_cache(tmp_path):
    plik = tmp_path / "parse_cache.json"
    plik.write_text(json.dumps({
        "schema": "acae.parsecache.v0",
        "grammars": wersje_gramatyk(),
        "entries": {"x": []},
    }), encoding="utf-8")
    assert load(plik) == {}


# ------------------------------------------------------------- odpornosc

def test_brak_pliku_to_pusty_cache_nie_wyjatek(tmp_path):
    assert load(tmp_path / "nie_ma_takiego.json") == {}


def test_uszkodzony_plik_to_pusty_cache_nie_wyjatek(tmp_path):
    plik = tmp_path / "parse_cache.json"
    plik.write_text("{to nie jest json", encoding="utf-8")
    assert load(plik) == {}


def test_zapis_do_niezapisywalnej_sciezki_nie_wywala(tmp_path):
    """Cache to tylko szybkosc. Nieudany zapis ma byc cichy, a nie przerwac prace."""
    save(tmp_path / "nie" / "ma" / "takiego" / "katalogu" / "c.json", {"a": []})


def test_zapisany_cache_ma_wersje_gramatyk(tmp_path):
    plik = tmp_path / "parse_cache.json"
    save(plik, {"k": []})
    dane = json.loads(plik.read_text(encoding="utf-8"))
    assert dane["schema"] == SCHEMA
    assert dane["grammars"] == wersje_gramatyk()
    assert set(dane["grammars"]) == {"tree-sitter", "tree-sitter-language-pack"}
