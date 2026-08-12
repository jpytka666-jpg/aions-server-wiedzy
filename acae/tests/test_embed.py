"""
test_embed.py — M7. Statyczny embedding.

Modul zostal ZMIERZONY I ODRZUCONY wobec kryterium (STATE.md 2026-08-12T21:05), ale jego
warstwa arytmetyczna jest tym, na czym stoi obietnica „bit w bit" zlozona Marcinowi.
Te testy pilnuja wlasnie jej.

Czesc testow wymaga artefaktu `_model/`, ktory jest gitignorowany (15 MB, odtwarzalny przez
`scripts/export_model.py`). Bez artefaktu sa pomijane, a nie wywalaja calego zestawu —
inaczej swiezy klon repo swiecilby czerwono z powodu braku pliku, ktory swiadomie
trzymamy poza historia.
"""

from __future__ import annotations

import json
import pathlib

import numpy as np
import pytest

from acae.embed import (
    ModelMismatch, StaticEmbedder, Pair, receipt, similarity_permille, symbol_text,
)

MODEL_DIR = pathlib.Path(__file__).resolve().parent.parent / "_model"
wymaga_modelu = pytest.mark.skipif(
    not (MODEL_DIR / "model_card.json").is_file() or not (MODEL_DIR / "vectors_int16.npy").is_file(),
    reason="brak artefaktu _model/ — odtworz przez scripts/export_model.py",
)


# --------------------------------------------------------- arytmetyka, bez modelu


def test_identyczne_wektory_daja_pelne_podobienstwo():
    v = np.array([3, -4, 12], dtype=np.int64)
    assert similarity_permille(v, v) == 1000


def test_prostopadle_daja_zero():
    a = np.array([1, 0, 0], dtype=np.int64)
    b = np.array([0, 1, 0], dtype=np.int64)
    assert similarity_permille(a, b) == 0


def test_przeciwne_scinane_do_zera():
    """Ujemne podobienstwo nie ma sensu w rankingu i zasmiecaloby paragon."""
    a = np.array([1, 2, 3], dtype=np.int64)
    assert similarity_permille(a, -a) == 0


def test_wektor_zerowy_nie_wywala():
    a = np.array([1, 2, 3], dtype=np.int64)
    zero = np.zeros(3, dtype=np.int64)
    assert similarity_permille(a, zero) == 0
    assert similarity_permille(zero, zero) == 0


def test_wynik_jest_intem_pythona_nie_floatem():
    """
    Kanoniczny JSON zabrania floatow, a `numpy.int64` nie jest serializowalny wprost.
    Wynik musi byc zwyklym `int`.
    """
    v = np.array([5, 5, 5], dtype=np.int64)
    wynik = similarity_permille(v, v)
    assert type(wynik) is int


def test_skala_nie_zmienia_podobienstwa():
    """Cosinus skraca staly czynnik — dlatego wolno sumowac wektory zamiast usredniac."""
    a = np.array([1, 2, 3], dtype=np.int64)
    b = np.array([2, 1, 1], dtype=np.int64)
    assert similarity_permille(a, b) == similarity_permille(a * 7, b * 13)


def test_powtarzalnosc_arytmetyki():
    """Ta sama para wektorow, sto razy — jeden wynik. Bez tego nie ma `pack_hash`."""
    rng = np.random.default_rng(0)
    a = rng.integers(-32767, 32767, size=256, dtype=np.int64)
    b = rng.integers(-32767, 32767, size=256, dtype=np.int64)
    assert len({similarity_permille(a, b) for _ in range(100)}) == 1


def test_brak_przepelnienia_na_skrajnych_wartosciach():
    """
    256 wymiarow po 32767 to najgorszy przypadek. Mnozenie przez 1000 przekracza int64,
    dlatego kod przechodzi na `int` Pythona — ten test pilnuje, ze przechodzi naprawde.
    """
    v = np.full(256, 32767, dtype=np.int64) * 50   # jakby 50 tokenow zsumowanych
    assert similarity_permille(v, v) == 1000


def test_symbol_text_rozbija_identyfikatory():
    row = {"name_path": "AIONS/_init_korean_compression", "signature": "def _init(self)", "doc": ""}
    tekst = symbol_text("aions_core/server/ts_symbols.py", row)
    for slowo in ("aions", "core", "server", "init", "korean", "compression"):
        assert slowo in tekst.split(), f"brak {slowo!r} w {tekst!r}"
    assert ".py" not in tekst


def test_symbol_text_stabilny():
    """Regula tekstu dokumentu byla ustalona w prerejestracji — nie wolno jej dryfowac."""
    row = {"name_path": "A/b_c", "signature": "def b_c(x)", "doc": "opis"}
    assert symbol_text("pkg/mod.py", row) == symbol_text("pkg/mod.py", dict(row))


def test_pair_serializuje_sie_plasko():
    p = Pair("machine", "host", 340)
    assert p.as_dict() == {"query_token": "machine", "doc_token": "host", "permille": 340}


# ------------------------------------------------------------ z artefaktem modelu


@wymaga_modelu
def test_karta_zgadza_sie_z_plikami():
    """Konstruktor weryfikuje hashe. Jesli to przestanie dzialac, wraca cicha halucynacja."""
    e = StaticEmbedder(MODEL_DIR)
    assert e.matrix.dtype == np.int16
    assert e.dim == e.matrix.shape[1]
    assert e.card["source_model"] == "minishlab/potion-base-8M"


@wymaga_modelu
def test_podmieniona_karta_zatrzymuje_start(tmp_path):
    """Lepiej stanac niz policzyc cos, co wyglada sensownie i jest falszywe."""
    for name in ("vectors_int16.npy", "tokenizer.json"):
        (tmp_path / name).write_bytes((MODEL_DIR / name).read_bytes())
    card = json.loads((MODEL_DIR / "model_card.json").read_text(encoding="utf-8"))
    card["files"]["vectors_int16.npy"] = "blake2b256:" + "0" * 64
    (tmp_path / "model_card.json").write_text(json.dumps(card), encoding="utf-8")

    with pytest.raises(ModelMismatch):
        StaticEmbedder(tmp_path)


@wymaga_modelu
def test_brak_artefaktu_to_wyjatek_nie_cisza(tmp_path):
    with pytest.raises(ModelMismatch):
        StaticEmbedder(tmp_path / "nie_ma_takiego")


@wymaga_modelu
def test_ten_sam_tekst_ten_sam_wektor():
    e = StaticEmbedder(MODEL_DIR)
    a = e.vector("how is provenance recorded on every memory write")
    b = e.vector("how is provenance recorded on every memory write")
    assert np.array_equal(a, b)
    assert a.dtype == np.int64


@wymaga_modelu
def test_pusty_tekst_daje_wektor_zerowy():
    e = StaticEmbedder(MODEL_DIR)
    assert not e.vector("").any()


@wymaga_modelu
def test_bliskie_znaczeniowo_bije_odlegle():
    """
    Minimalny test sensu: zdanie o pamieci ma byc blizej dokumentu o pamieci niz
    dokumentu o obsludze myszy. Bez tego caly modul moglby liczyc szum.
    """
    e = StaticEmbedder(MODEL_DIR)
    q = e.vector("how is provenance recorded on every memory write")
    bliski = e.vector("aions core server cbms memory record provenance host agent")
    daleki = e.vector("desktop provider click mouse keyboard screenshot window")
    assert similarity_permille(q, bliski) > similarity_permille(q, daleki)


@wymaga_modelu
def test_paragon_rozklada_sie_dokladnie():
    """
    Sedno audytowalnosci: suma wkladow WSZYSTKICH par musi rownac sie podobienstwu.
    Test bierze pelny rozklad (limit rowny liczbie par), a nie tylko czolowke.
    """
    e = StaticEmbedder(MODEL_DIR)
    q = "which machine performed a memory write"
    d = "server host agent memory write provenance"
    pary = receipt(e, q, d, limit=10_000)
    assert pary, "rozklad nie moze byc pusty dla pasujacych tekstow"

    calosc = similarity_permille(e.vector(q), e.vector(d))
    suma = sum(p.permille for p in pary)
    # Kazda para jest dzielona calkowicie osobno, wiec suma moze byc co najwyzej
    # o liczbe par mniejsza niz calosc. Ujemne pary sa pominiete, wiec nie przekroczy.
    assert suma <= calosc
    assert calosc - suma <= len(pary)


@wymaga_modelu
def test_paragon_posortowany_malejaco():
    e = StaticEmbedder(MODEL_DIR)
    pary = receipt(e, "which machine performed a memory write", "server host agent memory write")
    assert [p.permille for p in pary] == sorted((p.permille for p in pary), reverse=True)
