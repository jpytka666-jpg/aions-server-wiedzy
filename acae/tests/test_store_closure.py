"""
Domkniecie M3 — trwalosc przez granice procesu.

DLACZEGO OSOBNY PLIK
--------------------
Wszystkie czternascie testow w `test_store.py` jedzie na `BlockStore(":memory:")`.
Sprawdzaja NIEZMIENNIKI (I2, I5-I9, C4), ale zaden nie zamyka bazy i nie otwiera jej
ponownie. Magazyn, ktory nigdy nie zostal ponownie otwarty, nie jest magazynem —
jest cache'em, ktory przypadkiem ma API magazynu.

Ten plik przechodzi pelny cykl na PLIKU:
    zapis -> zamkniecie -> ponowne otwarcie -> odczyt -> rewizja -> zamkniecie ->
    ponowne otwarcie -> tombstone -> zamkniecie -> ponowne otwarcie -> weryfikacja

Kazdy krok sprawdza to, co ADR-002 obiecuje PO restarcie, nie w trakcie jednej sesji:
tresc, prowenancje, trust tier, `valid_to` rewizji, journal i zgodnosc `stats` ze skanem.
"""

from __future__ import annotations

from acae.store import BlockStore, Provenance

P1 = Provenance(source_uri="acae://pack/1", job_id="j1", tool="acae.pack", trust_tier="T1")
P3 = Provenance(source_uri="acae://doc/2", job_id="j2", tool="acae.bridge", trust_tier="T3")
T0 = "2026-08-11T08:00:00Z"
T1 = "2026-08-11T09:00:00Z"
T2 = "2026-08-11T10:00:00Z"


def _db(tmp_path):
    return str(tmp_path / "acae_store.sqlite3")


def test_tresc_i_prowenancja_przezywaja_reopen(tmp_path):
    path = _db(tmp_path)
    with BlockStore(path) as store:
        result = store.put(
            content=b"tresc bloku", kind="artifact", scope="project:acae",
            provenance=[P1], observed_at=T0,
        )
        block_id, digest = result.id, result.content_hash
        assert result.created is True

    with BlockStore(path) as store:
        block = store.get(block_id)
        assert block is not None, "blok zniknal po ponownym otwarciu bazy"
        assert block["content"] == b"tresc bloku"
        assert block["content_hash"] == digest
        assert [p["source_uri"] for p in block["provenance"]] == ["acae://pack/1"]
        assert block["trust_tier"] == "T1"
        assert store.by_content(digest, "project:acae")["id"] == block_id


def test_i5_i_i6_dzialaja_MIEDZY_sesjami(tmp_path):
    """
    Idempotencja i sumowanie prowenancji musza dzialac takze wtedy, gdy powtorny
    zapis przychodzi z INNEGO uruchomienia — inaczej dedup jest wlasnoscia sesji,
    a nie magazynu.
    """
    path = _db(tmp_path)
    with BlockStore(path) as store:
        first = store.put(
            content=b"to samo", kind="fact", scope="project:acae",
            provenance=[P1], observed_at=T0,
        )

    with BlockStore(path) as store:
        second = store.put(
            content=b"to samo", kind="fact", scope="project:acae",
            provenance=[P3], observed_at=T1,
        )
        assert second.created is False and second.merged is True
        assert second.id == first.id

    with BlockStore(path) as store:
        block = store.get(first.id)
        sources = sorted(p["source_uri"] for p in block["provenance"])
        assert sources == ["acae://doc/2", "acae://pack/1"], "prowenancja zgubiona przez reopen"
        # I7: tier schodzi do najnizszego ze zrodel, takze po scaleniu miedzy sesjami.
        assert block["trust_tier"] == "T3"
        assert store.stats()["blocks"] == 1


def test_rewizja_i_valid_to_przezywaja_reopen(tmp_path):
    path = _db(tmp_path)
    with BlockStore(path) as store:
        original = store.put(
            content=b"wersja pierwsza", kind="artifact", scope="project:acae",
            provenance=[P1], observed_at=T0,
        )

    with BlockStore(path) as store:
        revised = store.revise(
            original.id, content=b"wersja druga", provenance=[P1], observed_at=T1,
        )

    with BlockStore(path) as store:
        # I2: stary blok nie znika, dostaje valid_to; nowy ma wlasne id.
        assert revised.id != original.id
        stary = store.list_blocks(include_superseded=True)
        po_id = {b["id"]: b for b in stary}
        assert po_id[original.id]["valid_to"] is not None, "valid_to nie przetrwalo reopenu"
        assert po_id[revised.id]["valid_to"] is None
        assert po_id[revised.id]["content"] == b"wersja druga"
        assert original.id in po_id[revised.id]["derived_from"]


def test_tombstone_i_journal_przezywaja_reopen(tmp_path):
    """
    I8: usuniecie to tombstone plus wpis w journalu. Jesli journal nie przezywa
    restartu, „tombstone" jest tylko skasowaniem z opoznieniem.
    """
    path = _db(tmp_path)
    with BlockStore(path) as store:
        block = store.put(
            content=b"do skasowania", kind="observation", scope="session:s1",
            provenance=[P1], observed_at=T0,
        )

    with BlockStore(path) as store:
        assert store.forget(block.id, reason="test domkniecia", observed_at=T2) is True

    with BlockStore(path) as store:
        assert store.get(block.id) is None, "blok widoczny mimo tombstone"
        operacje = [entry["op"] for entry in store.journal()]
        assert "forget" in operacje, "fakt usuniecia zginal razem z blokiem"
        wpis = [e for e in store.journal() if e["op"] == "forget"][0]
        assert wpis["block_id"] == block.id
        assert wpis["detail"].get("reason") == "test domkniecia"


def test_i9_stats_zgadza_sie_ze_skanem_po_reopenie(tmp_path):
    path = _db(tmp_path)
    with BlockStore(path) as store:
        for i in range(5):
            store.put(
                content=f"blok {i}".encode(), kind="fact", scope="project:acae",
                provenance=[P1], observed_at=T0,
            )
        do_usuniecia = store.list_blocks()[0]["id"]
        store.forget(do_usuniecia, reason="kontrola", observed_at=T1)

    with BlockStore(path) as store:
        assert store.stats()["blocks"] == len(store.list_blocks()) == 4


def test_c4_odbudowa_indeksow_dziala_na_bazie_z_dysku(tmp_path):
    """
    C4 na PLIKU, nie w pamieci: skasowanie indeksow i odbudowa z tabeli blokow
    nie moze zmienic odpowiedzi. To jest test tego, ze tabela blokow jest
    samowystarczalna, a indeksy sa czysto pochodne.
    """
    path = _db(tmp_path)
    with BlockStore(path) as store:
        wynik = store.put(
            content=b"tresc kontrolna", kind="artifact", scope="project:acae",
            provenance=[P1], observed_at=T0,
        )

    with BlockStore(path) as store:
        przed = store.by_content(wynik.content_hash, "project:acae")
        store.drop_indexes()
        store.rebuild_indexes()
        assert store.by_content(wynik.content_hash, "project:acae") == przed

    with BlockStore(path) as store:
        assert store.by_content(wynik.content_hash, "project:acae") == przed
