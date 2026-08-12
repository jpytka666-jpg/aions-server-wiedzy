"""
Testy warstwy opisow (M8).

Najwazniejszy test w tym pliku to `test_puste_opisy_daja_dokladnie_baseline`. Cala tabela
porownawcza dziesieciu pomiarow opiera sie na zalozeniu, ze M8 to baseline PLUS opisy —
jesli ranking z pustym korpusem opisow rozni sie od `retrieve.select` czymkolwiek,
lacznie z rozstrzyganiem remisow, to porownanie mierzy dwie rozne rzeczy.

Drugi co do wagi to `test_paragon_sumuje_sie_dokladnie_do_wkladu_opisu`. W `embed.py`
paragon KLAMAL — pomijal skladniki ujemne, wiec czolowka nie sumowala sie do wyniku —
i zdazylem opisac go Marcinowi jako „rozklad dokladny", zanim test to wywrocil.
Tu paragon jest jedynym narzedziem odrozniajacym „opis pomogl" od „leksyka i tak
by to znalazla", wiec musi sumowac sie co do jednostki.
"""

from __future__ import annotations

import json

import pytest
from conftest import MemoryLocator, MemoryReader

from acae.core import collect_entries
from acae.describe import (
    DescriptionsError,
    load_descriptions,
    rank_all,
    receipt,
    score_with_description,
    term_rarity_with_descriptions,
)
from acae.retrieve import W_PATH, score_symbol, select, term_rarity


@pytest.fixture
def entries(blobs):
    collected, _ = collect_entries(MemoryLocator(sorted(blobs)), MemoryReader(blobs))
    return collected


@pytest.fixture
def wiersz(entries):
    """Pierwszy symbol pierwszego pliku — konkretny obiekt do testow punktacji."""
    entry = entries[0]
    return str(entry["path"]), entry["symbols"][0]


# ------------------------------------------------------- zgodnosc z baseline'em

def test_puste_opisy_daja_dokladnie_baseline(entries):
    """
    Bez opisow M8 MUSI byc baseline'em — ten sam wynik i ta sama kolejnosc.

    To jest warunek uczciwosci calej tabeli porownawczej. Rozjazd tutaj znaczy,
    ze roznica miedzy M8 a baseline'em pochodzi z implementacji, nie z opisow.
    """
    terms = ["alpha", "beta", "delta", "gamma"]
    oczekiwany, _ = select(entries, terms, outline_limit=10_000, drill_limit=0)
    otrzymany, _ = rank_all(entries, terms, {})

    assert len(otrzymany) == len(oczekiwany)
    for a, b in zip(otrzymany, oczekiwany):
        assert a["score"] == b["score"]
        assert a["path"] == b["path"]
        assert a["row"]["name_path"] == b["row"]["name_path"]


def test_puste_opisy_daja_dokladnie_baselinowa_rzadkosc(entries):
    terms = ["alpha", "beta", "delta"]
    assert term_rarity_with_descriptions(entries, terms, {}) == term_rarity(entries, terms)


def test_plik_bez_opisu_punktowany_jak_w_baseline(entries, wiersz):
    """Opis jednego pliku nie moze zmieniac wyniku symboli z innego pliku."""
    path, row = wiersz
    terms = ["alpha"]
    rarity = term_rarity(entries, terms)
    opisy = {"pkg/zupelnie_inny.py": "alpha alpha alpha"}
    assert score_with_description(path, row, terms, rarity, opisy.get(path, "")) == \
        score_symbol(path, row, terms, rarity)


# ------------------------------------------------------------------ punktacja

def test_trafienie_w_opisie_dodaje_dokladnie_wage_sciezki(entries, wiersz):
    path, row = wiersz
    terms = ["maszyna"]
    rarity = {"maszyna": 7}
    bez = score_symbol(path, row, terms, rarity)
    z_opisem = score_with_description(path, row, terms, rarity, "opisuje maszyna i nic wiecej")
    assert z_opisem - bez == 7 * W_PATH


def test_powtorzony_termin_w_opisie_liczy_sie_raz(entries, wiersz):
    """
    Opis powtarzajacy slowo dziesiec razy nie moze dostac dziesieciu premii.

    Bez tego dlugosc opisu stalaby sie pokretlem: wystarczyloby kazac modelowi
    powtarzac slowa kluczowe, zeby „poprawic" wynik.
    """
    path, row = wiersz
    terms = ["maszyna"]
    rarity = {"maszyna": 5}
    raz = score_with_description(path, row, terms, rarity, "maszyna")
    dziesiec = score_with_description(path, row, terms, rarity, "maszyna " * 10)
    assert raz == dziesiec


def test_termin_spoza_opisu_nic_nie_dodaje(entries, wiersz):
    path, row = wiersz
    terms = ["nieobecny"]
    rarity = {"nieobecny": 9}
    assert score_with_description(path, row, terms, rarity, "zupelnie co innego") == \
        score_symbol(path, row, terms, rarity)


def test_wielkosc_liter_w_opisie_nie_ma_znaczenia(entries, wiersz):
    path, row = wiersz
    terms = ["maszyna"]
    rarity = {"maszyna": 3}
    male = score_with_description(path, row, terms, rarity, "maszyna")
    duze = score_with_description(path, row, terms, rarity, "MASZYNA")
    assert male == duze
    assert male > score_symbol(path, row, terms, rarity)


def test_opis_nigdy_nie_odejmuje(entries, wiersz):
    """Przy tych samych wagach opis moze tylko dodac. Ujemny wklad znaczylby blad znaku."""
    path, row = wiersz
    terms = ["alpha", "beta", "maszyna"]
    rarity = term_rarity(entries, terms)
    for opis in ("", "maszyna", "alpha beta maszyna", "nic wspolnego"):
        assert score_with_description(path, row, terms, rarity, opis) >= \
            score_symbol(path, row, terms, rarity)


def test_wynik_jest_intem_nie_floatem(entries, wiersz):
    path, row = wiersz
    wynik = score_with_description(path, row, ["maszyna"], {"maszyna": 3}, "maszyna")
    assert isinstance(wynik, int) and not isinstance(wynik, bool)


def test_brak_terminow_daje_zero(entries, wiersz):
    path, row = wiersz
    assert score_with_description(path, row, [], {}, "cokolwiek tu stoi") == 0


# ------------------------------------------------- decyzja M8-a: opisy w rzadkosci

def test_slowo_wystepujace_TYLKO_w_opisach_nie_ma_zerowego_df(entries):
    """
    Sedno decyzji M8-a.

    `term_rarity` daje wage `total // (1 + df)` z sufitem. Termin o `df = 0` dostaje
    wage MAKSYMALNA. Slowa takie jak „maszyna" po dodaniu opisow wystepuja wylacznie
    w opisach — gdyby opisy nie liczyly sie do `df`, takie slowo mialoby wage sufitu
    zamiast wagi wynikajacej z jego czestosci. M8 wygladalby swietnie z powodu,
    ktorego nikt nie zapisal.
    """
    terms = ["maszyna"]
    opisy = {str(e["path"]): "maszyna wszedzie" for e in entries}

    bez_opisow = term_rarity(entries, terms)["maszyna"]
    z_opisami = term_rarity_with_descriptions(entries, terms, opisy)["maszyna"]

    assert z_opisami < bez_opisow, (
        "termin obecny w kazdym opisie musi byc TANSZY niz termin nieobecny nigdzie"
    )


def test_im_wiecej_opisow_z_terminem_tym_nizsza_waga(entries):
    """Waga ma maleć monotonicznie z liczba plikow, ktorych opis zawiera termin."""
    terms = ["maszyna"]
    sciezki = [str(e["path"]) for e in entries]
    wagi = []
    for ile in range(len(sciezki) + 1):
        opisy = {p: "maszyna" for p in sciezki[:ile]}
        wagi.append(term_rarity_with_descriptions(entries, terms, opisy)["maszyna"])
    assert wagi == sorted(wagi, reverse=True)


def test_rzadkosc_ma_sufit_jak_baseline(entries):
    """Sufit chroni przed literowka o df=1. M8 nie ma prawa go omijac."""
    from acae.retrieve import RARITY_CAP
    terms = ["zupelnieunikalnyterm"]
    waga = term_rarity_with_descriptions(entries, terms, {})["zupelnieunikalnyterm"]
    assert waga <= RARITY_CAP


# ----------------------------------------------------------------- ranking

def test_opis_potrafi_wciagnac_symbol_o_leksykalnym_zerze(entries):
    """
    Warunek, dla ktorego caly M8 powstal: symbol z wynikiem leksykalnym zero
    ma po dodaniu opisu wynik dodatni. Zero nie zamienia sie w dodatnie
    przez przewazenie — tylko przez pojawienie sie trafienia.
    """
    terms = ["maszyna"]
    assert rank_all(entries, terms, {})[0] == []

    cel = str(entries[0]["path"])
    ranked, _ = rank_all(entries, terms, {cel: "to dziala na maszyna uzytkownika"})
    assert ranked, "opis nie wciagnal zadnego symbolu"
    assert all(item["path"] == cel for item in ranked)


def test_remisy_rozstrzygane_jak_w_retrieve(entries):
    """
    Ten sam wynik u wielu symboli musi ustawiac sie wg (sciezka, linia, name_path),
    a nie wg kolejnosci wstawiania. Inaczej ranking zalezy od kolejnosci plikow na dysku.
    """
    terms = ["maszyna"]
    opisy = {str(e["path"]): "maszyna" for e in entries}
    ranked, _ = rank_all(entries, terms, opisy)
    klucze = [(r["path"], r["row"]["line"], r["row"]["name_path"]) for r in ranked]
    assert klucze == sorted(klucze)


def test_ranking_powtarzalny(entries):
    terms = ["alpha", "maszyna"]
    opisy = {str(e["path"]): "maszyna i alpha" for e in entries}
    a, _ = rank_all(entries, terms, opisy)
    b, _ = rank_all(entries, terms, opisy)
    assert [(r["path"], r["row"]["name_path"], r["score"]) for r in a] == \
        [(r["path"], r["row"]["name_path"], r["score"]) for r in b]


def test_symbole_z_zerem_nie_wchodza_do_rankingu(entries):
    terms = ["maszyna"]
    cel = str(entries[0]["path"])
    ranked, _ = rank_all(entries, terms, {cel: "maszyna"})
    assert all(item["score"] > 0 for item in ranked)


# ----------------------------------------------------------------- paragon

def test_paragon_sumuje_sie_dokladnie_do_wkladu_opisu(entries):
    """
    Odpowiednik bledu z `embed.py`: paragon musi sumowac sie do tego, co naprawde
    wpadlo do wyniku. Tam czolowka przekraczala calosc, bo pomijal skladniki ujemne.
    """
    terms = ["alpha", "maszyna"]
    opisy = {str(e["path"]): "maszyna oraz alpha" for e in entries}
    ranked, rarity = rank_all(entries, terms, opisy)
    pozycje = receipt(ranked, terms, opisy, rarity, limit=len(ranked))[0]["top"]

    for item, wpis in zip(ranked, pozycje):
        bez_opisu = score_symbol(str(item["path"]), item["row"], terms, rarity)
        assert wpis["from_description"] == item["score"] - bez_opisu


def test_paragon_wymienia_tylko_slowa_faktycznie_obecne_w_opisie(entries):
    terms = ["alpha", "nieobecny"]
    opisy = {str(e["path"]): "tylko alpha tutaj" for e in entries}
    ranked, rarity = rank_all(entries, terms, opisy)
    for wpis in receipt(ranked, terms, opisy, rarity)[0]["top"]:
        assert "nieobecny" not in wpis["terms_in_description"]


def test_paragon_pusty_gdy_brak_opisow(entries):
    terms = ["alpha"]
    ranked, rarity = rank_all(entries, terms, {})
    for wpis in receipt(ranked, terms, {}, rarity)[0]["top"]:
        assert wpis["terms_in_description"] == []
        assert wpis["from_description"] == 0


# ------------------------------------------------------- wczytywanie artefaktu

def _artefakt(tmp_path, pack_hash="blake2b256:aaa", opisy=None):
    plik = tmp_path / "descriptions.json"
    plik.write_text(json.dumps({
        "provenance": {"model": "test", "pack_hash": pack_hash, "count": 1},
        "descriptions": opisy if opisy is not None else {"pkg/alpha.py": "opis"},
    }), encoding="utf-8")
    return plik


def test_wczytanie_zwraca_opisy_i_prowieniencje(tmp_path):
    opisy, prov = load_descriptions(_artefakt(tmp_path))
    assert opisy == {"pkg/alpha.py": "opis"}
    assert prov["model"] == "test"


def test_niezgodny_pack_hash_zatrzymuje_pomiar(tmp_path):
    """
    Opisy wyprodukowane dla innego stanu repo nie moga cicho przezyc jego zmiany.
    Liczby wygladalyby sensownie, opisujac kod, ktorego juz nie ma.
    """
    with pytest.raises(DescriptionsError):
        load_descriptions(_artefakt(tmp_path, pack_hash="blake2b256:stary"),
                          expected_pack_hash="blake2b256:nowy")


def test_zgodny_pack_hash_przechodzi(tmp_path):
    opisy, _ = load_descriptions(_artefakt(tmp_path, pack_hash="blake2b256:ten_sam"),
                                 expected_pack_hash="blake2b256:ten_sam")
    assert opisy


def test_pusta_mapa_opisow_to_wyjatek_nie_cisza(tmp_path):
    with pytest.raises(DescriptionsError):
        load_descriptions(_artefakt(tmp_path, opisy={}))


def test_brak_klucza_descriptions_to_wyjatek(tmp_path):
    plik = tmp_path / "zle.json"
    plik.write_text(json.dumps({"provenance": {}}), encoding="utf-8")
    with pytest.raises(DescriptionsError):
        load_descriptions(plik)
