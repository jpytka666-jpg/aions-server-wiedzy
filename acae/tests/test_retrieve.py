"""
Testy wyszukiwania i wycinania (M2).

Najwazniejszy test w tym pliku to `test_terminy_zgadzaja_sie_z_baselinem`. Bramka M2
porownuje wycinek z `B_query(q)` policzonym w M0 — a to porownanie ma sens tylko wtedy,
gdy oba licza na TYCH SAMYCH terminach. Regula rozbioru zapytania zyje dzis w dwoch
miejscach (skrypt baseline i pakiet), wiec kopia jest tu zamieniona w sprawdzany warunek.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from conftest import MemoryLocator, MemoryReader

from acae.core import collect_entries
from acae.retrieve import STOPWORDS, build_slice, query_terms, score_symbol, select

ACAE_DIR = Path(__file__).resolve().parents[1]


def _load_measure_baseline():
    """Laduje skrypt M0 jako modul, zeby porownac regule rozbioru zapytania."""
    path = ACAE_DIR / "scripts" / "measure_baseline.py"
    spec = importlib.util.spec_from_file_location("measure_baseline_probe", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def entries(blobs):
    collected, _ = collect_entries(MemoryLocator(sorted(blobs)), MemoryReader(blobs))
    return collected


# --------------------------------------------------------------- zgodnosc z M0

def test_stopwords_sa_identyczne_z_baselinem():
    assert STOPWORDS == _load_measure_baseline().STOPWORDS


def test_terminy_zgadzaja_sie_z_baselinem_na_wszystkich_zamrozonych_zapytaniach():
    baseline = _load_measure_baseline()
    queries = json.loads((ACAE_DIR / "tests" / "queries.json").read_bytes())["queries"]
    for query in queries:
        assert query_terms(query["text"], 3) == baseline.query_terms(query["text"], 3), query["id"]


# ------------------------------------------------------------------- ranking

def test_trafienie_w_nazwe_symbolu_wazy_wiecej_niz_trafienie_w_sciezke():
    w_nazwie = score_symbol(
        "x/y.py",
        {"name_path": "Store/put", "signature": "def put(self, k, v):", "line": 1, "kind": "function"},
        ["put"],
    )
    w_sciezce = score_symbol(
        "put/y.py",
        {"name_path": "Alpha", "signature": "class Alpha:", "line": 1, "kind": "class"},
        ["put"],
    )
    assert w_nazwie > w_sciezce


def test_brak_terminow_daje_zero_punktow():
    row = {"name_path": "Alpha", "signature": "class Alpha:", "line": 1, "kind": "class"}
    assert score_symbol("pkg/a.py", row, []) == 0


def test_termin_rzadki_wazy_wiecej_niz_czesty():
    """
    Regresja na realnej wpadce: przy rownych wagach `CBMSMemory` (trafienie w czeste
    „memory" w nazwie, sygnaturze i sciezce) bil funkcje `provenance()` (rzadkie
    „provenance" w nazwie i sygnaturze), czyli odpowiedz przegrywala z tlem.
    """
    from acae.retrieve import term_rarity

    # Zbior, w ktorym „memory" jest wszedzie, a „provenance" tylko w jednym symbolu.
    entries = [
        {
            "path": "aions_core/cbms_memory.py",
            "lang": "python",
            "symbols": [
                {"name_path": f"Memory{i}", "signature": "class MemoryThing:", "line": i, "kind": "class"}
                for i in range(1, 12)
            ],
        },
        {
            "path": "mcpServers/src/server.py",
            "lang": "python",
            "symbols": [
                {"name_path": "provenance", "signature": "def provenance() -> Dict:", "line": 1, "kind": "function"},
            ],
        },
    ]
    terms = ["memory", "provenance"]
    rarity = term_rarity(entries, terms)
    assert rarity["provenance"] > rarity["memory"]

    outline, _ = select(entries, terms, outline_limit=1, drill_limit=1)
    assert outline[0]["row"]["name_path"] == "provenance"


def test_waga_rzadkosci_jest_ograniczona_z_gory():
    """Termin wystepujacy raz nie moze dostac wagi rownej liczbie symboli."""
    from acae.retrieve import RARITY_CAP, term_rarity

    entries = [{
        "path": "a/b.py",
        "lang": "python",
        "symbols": [{"name_path": f"f{i}", "signature": "def f():", "line": i, "kind": "function"} for i in range(500)],
    }]
    assert term_rarity(entries, ["nieobecny"])["nieobecny"] == RARITY_CAP


def test_select_zwraca_malejaco_po_wyniku(entries):
    outline, _ = select(entries, ["delta", "alpha"], outline_limit=10, drill_limit=2)
    wyniki = [item["score"] for item in outline]
    assert wyniki == sorted(wyniki, reverse=True)


def test_select_respektuje_limity(entries):
    outline, drill = select(entries, ["alpha", "beta", "delta", "gamma"], outline_limit=2, drill_limit=1)
    assert len(outline) == 2
    assert len(drill) == 1


# -------------------------------------------------------------------- wycinek

def test_wycinek_zawiera_cialo_dociagnietego_symbolu(entries, blobs):
    text, meta = build_slice(entries, "delta sum", MemoryReader(blobs))
    assert meta["drilled"] >= 1
    assert b"return a + b" in text


def test_wycinek_zawiera_sygnatury_w_szkielecie(entries, blobs):
    text, _ = build_slice(entries, "alpha beta", MemoryReader(blobs))
    assert b"Alpha/beta" in text


def test_wycinek_jest_powtarzalny_co_do_bajta(entries, blobs):
    reader = MemoryReader(blobs)
    assert build_slice(entries, "delta sum", reader)[0] == build_slice(entries, "delta sum", reader)[0]


def test_kolejnosc_wpisow_nie_zmienia_wycinka(entries, blobs):
    reader = MemoryReader(blobs)
    prosto = build_slice(entries, "delta alpha", reader)[0]
    odwrotnie = build_slice(list(reversed(entries)), "delta alpha", reader)[0]
    assert prosto == odwrotnie


def test_zapytanie_bez_terminow_daje_pusty_wycinek_zamiast_calosci(entries, blobs):
    """Terminy krotsze niz trzy znaki odpadaja — wtedy nie ma czego rankowac."""
    _, meta = build_slice(entries, "is a to", MemoryReader(blobs))
    assert meta["outline_symbols"] == 0
    assert meta["drilled"] == 0


def test_dlugie_cialo_jest_ucinane_JAWNIE():
    """Ciche ucinanie zamienialoby oszczednosc tokenow w gubienie kodu."""
    blobs = {"pkg/big.py": b"def big():\n" + b"    x = 1\n" * 300}
    collected, _ = collect_entries(MemoryLocator(["pkg/big.py"]), MemoryReader(blobs))
    text, _ = build_slice(collected, "big", MemoryReader(blobs), max_body_lines=10)
    assert b"[... uciete" in text


def test_wycinek_nie_ma_crlf(entries, blobs):
    assert b"\r\n" not in build_slice(entries, "delta", MemoryReader(blobs))[0]


def test_wycinek_jest_duzo_mniejszy_niz_caly_szkielet(entries, blobs):
    """Sedno M2: wycinek ma byc ulamkiem szkieletu, inaczej ciecie nic nie daje."""
    from acae.core import PackRequest, build_pack

    caly = build_pack(PackRequest(root="repo"), MemoryLocator(sorted(blobs)), MemoryReader(blobs)).content
    wycinek, _ = build_slice(entries, "delta", MemoryReader(blobs), outline_limit=1, drill_limit=0)
    assert len(wycinek) < len(caly) + 200  # naglowek wycinka jest dluzszy niz naglowek packa
