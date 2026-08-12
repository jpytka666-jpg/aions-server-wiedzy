"""
Testy semantycznego codebooka (M5).

Mechanizm ZMIERZONY I ODRZUCONY — nie przeszedl prerejestrowanego kryterium.
Testy pilnuja, ze odrzucilismy cos POPRAWNEGO, a nie wlasny blad.
"""

from __future__ import annotations

import json

from conftest import MemoryLocator, MemoryReader

from acae.concepts import Codebook, ConceptHit, SymbolTokens
from acae.core import collect_entries


def _codebook(tmp_path, concepts):
    path = tmp_path / "cb.json"
    path.write_bytes(json.dumps({"schema": "acae.codebook.v1", "concepts": concepts}).encode("utf-8"))
    return Codebook(path)


def test_wczytuje_prawdziwy_codebook_z_repo():
    cb = Codebook()
    assert len(cb) > 20
    assert all({"id", "surface", "code"} <= set(c) for c in cb.concepts)


def test_dopasowanie_tylko_po_pelnym_slowie(tmp_path):
    """`form` nie moze trafiac przez `performance` — to byla realna wada pomiaru."""
    cb = _codebook(tmp_path, [{"id": "f", "eo": None, "surface": ["form"], "code": ["form"]}])
    assert cb.lookup(["form"])
    assert cb.lookup(["performance"]) == []
    assert cb.lookup(["formatting"]) == []


def test_zwraca_pary_z_paragonem(tmp_path):
    cb = _codebook(tmp_path, [{"id": "m", "eo": "maŝino", "surface": ["machine"], "code": ["host"]}])
    pary = cb.lookup(["machine"])
    assert [t for t, _ in pary] == ["host"]
    hit = pary[0][1]
    assert isinstance(hit, ConceptHit)
    assert hit.concept == "m"
    assert hit.query_term == "machine"
    assert hit.code_tokens == ("host",)


def test_paragon_niesie_pojecie_slowo_i_eo(tmp_path):
    cb = _codebook(tmp_path, [{"id": "m", "eo": "maŝino", "surface": ["machine"], "code": ["host"]}])
    d = cb.lookup(["machine"])[0][1].as_dict()
    assert d["concept"] == "m"
    assert d["derived_from"] == "machine"
    assert d["eo"] == "maŝino"
    assert d["code_tokens"] == ["host"]


def test_token_z_dwoch_pojec_nie_dubluje_sie(tmp_path):
    cb = _codebook(tmp_path, [
        {"id": "a", "eo": None, "surface": ["read"], "code": ["load"]},
        {"id": "b", "eo": None, "surface": ["fetch"], "code": ["load"]},
    ])
    assert [t for t, _ in cb.lookup(["read", "fetch"])] == ["load"]


def test_lookup_jest_powtarzalny(tmp_path):
    cb = _codebook(tmp_path, [
        {"id": "z", "eo": None, "surface": ["alpha"], "code": ["one", "two"]},
        {"id": "a", "eo": None, "surface": ["alpha"], "code": ["three"]},
    ])
    assert cb.lookup(["alpha"]) == cb.lookup(["alpha"])


def test_brak_dopasowania_daje_pusto(tmp_path):
    cb = _codebook(tmp_path, [{"id": "m", "eo": None, "surface": ["machine"], "code": ["host"]}])
    assert cb.lookup(["banana"]) == []


# --------------------------------------------------------------- SymbolTokens

def test_symboltokens_dopasowuje_cale_tokeny(blobs):
    entries, _ = collect_entries(MemoryLocator(sorted(blobs)), MemoryReader(blobs))
    st = SymbolTokens(entries)
    assert st.n == sum(len(e["symbols"]) for e in entries)
    # kazdy symbol ma jakiekolwiek tokeny
    assert all(name or sig for _, _, name, sig, _ in st.docs)


def test_symboltokens_nie_trafia_podciagiem():
    blobs = {"pkg/perf.py": b"class PerformanceMetric:\n    def run(self):\n        return 1\n"}
    entries, _ = collect_entries(MemoryLocator(sorted(blobs)), MemoryReader(blobs))
    st = SymbolTokens(entries)
    assert st.score(0, ["performance"]) > 0
    assert st.score(0, ["form"]) == 0, "podciag `form` trafil w `Performance`"


def test_rarity_karze_token_czesty():
    blobs = {"pkg/a.py": b"".join(
        f"def get_thing_{i}():\n    return {i}\n".encode() for i in range(20)
    )}
    entries, _ = collect_entries(MemoryLocator(sorted(blobs)), MemoryReader(blobs))
    st = SymbolTokens(entries)
    assert st.rarity("get") < st.rarity("nieobecny")


def test_score_rosnie_z_liczba_trafionych_pol():
    blobs = {"pkg/host.py": b"def host_lookup(host):\n    return host\n"}
    entries, _ = collect_entries(MemoryLocator(sorted(blobs)), MemoryReader(blobs))
    st = SymbolTokens(entries)
    assert st.score(0, ["host"]) > st.score(0, ["lookup"])
