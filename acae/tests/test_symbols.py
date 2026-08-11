"""Testy adaptera na ts_symbols. Pilnuja tego, co ACAE zastepuje, a nie tego, co bierze."""

from __future__ import annotations

import pytest
from conftest import SRC_ALPHA, SRC_ALPHA_CRLF

from acae.canon import normalize_source
from acae.symbols import NoGrammar, lang_for, outline_from_bytes


def test_lang_for_rozpoznaje_rozszerzenia_bez_wzgledu_na_wielkosc_liter():
    assert lang_for("pkg/a.py") == "python"
    assert lang_for("pkg/a.PY") == "python"
    assert lang_for("pkg/notes.md") is None


def test_outline_wydobywa_klase_metode_i_funkcje_modulowa():
    paths = [row["name_path"] for row in outline_from_bytes("pkg/alpha.py", SRC_ALPHA)]
    assert "Alpha" in paths
    assert "Alpha/beta" in paths
    assert "gamma" in paths


def test_outline_niesie_sygnatury_a_nie_ciala():
    rows = outline_from_bytes("pkg/alpha.py", SRC_ALPHA)
    assert all("body" not in row for row in rows)
    signatures = " ".join(row["signature"] or "" for row in rows)
    assert "def beta(self, x):" in signatures
    assert "return x + 1" not in signatures


def test_body_hash_to_blake2b256_a_nie_sha12_z_ts_symbols():
    """sha12 to SHA-1 obciety do 48 bitow, liczony po stratnym decode. Zastapiony."""
    for row in outline_from_bytes("pkg/alpha.py", SRC_ALPHA):
        assert row["body_hash"].startswith("blake2b256:")
        assert len(row["body_hash"]) == len("blake2b256:") + 64


def test_konce_linii_nie_zmieniaja_outline():
    """Po normalizacji na brzegu wersja z CRLF i z LF musza byc nierozroznialne."""
    from_lf = outline_from_bytes("pkg/alpha.py", normalize_source(SRC_ALPHA))
    from_crlf = outline_from_bytes("pkg/alpha.py", normalize_source(SRC_ALPHA_CRLF))
    assert from_lf == from_crlf


def test_kolejnosc_symboli_jest_stabilna_i_rosnaca_po_liniach():
    rows = outline_from_bytes("pkg/alpha.py", SRC_ALPHA)
    assert rows == outline_from_bytes("pkg/alpha.py", SRC_ALPHA)
    lines = [row["line"] for row in rows]
    assert lines == sorted(lines)


def test_brak_gramatyki_podnosi_wyjatek_zamiast_polykac_plik():
    """scan_dir w ts_symbols lyka ValueError i plik znika bez sladu. Tu ma byc glosno."""
    with pytest.raises(NoGrammar):
        outline_from_bytes("pkg/notes.md", b"# notatki\n")
