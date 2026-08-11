"""Testy magazynu M3. Kazdy odpowiada niezmiennikowi z ADR-002 §4.2."""

from __future__ import annotations

import pytest

from acae.store import BlockStore, Provenance, StoreError

P1 = Provenance(source_uri="acae://pack/1", job_id="j1", tool="acae.pack", trust_tier="T1")
P3 = Provenance(source_uri="acae://doc/2", job_id="j2", tool="acae.bridge", trust_tier="T3")
T = "2026-08-11T08:00:00Z"


@pytest.fixture
def store():
    with BlockStore(":memory:") as s:
        yield s


def _put(s, content=b"abc", **kw):
    kw.setdefault("kind", "artifact")
    kw.setdefault("scope", "project:acae")
    kw.setdefault("provenance", [P1])
    kw.setdefault("observed_at", T)
    return s.put(content=content, **kw)


def test_zapis_i_odczyt_zwraca_te_sama_tresc(store):
    r = _put(store)
    assert r.created and store.get(r.id)["content"] == b"abc"


def test_i5_powtorny_zapis_nie_tworzy_duplikatu(store):
    a = _put(store)
    b = _put(store)
    assert a.id == b.id and b.merged and not b.created
    assert store.stats()["blocks_total"] == 1


def test_i6_prowenancja_jest_sumowana_nigdy_wybierana(store):
    r = _put(store, provenance=[P1])
    _put(store, provenance=[P3])
    tools = {p["tool"] for p in store.get(r.id)["provenance"]}
    assert tools == {"acae.pack", "acae.bridge"}


def test_i7_trust_tier_spada_do_najnizszego_ze_zrodel(store):
    r = _put(store, provenance=[P1, P3])
    assert store.get(r.id)["trust_tier"] == "T3"


def test_i2_rewizja_tworzy_nowy_blok_a_stary_dostaje_valid_to(store):
    a = _put(store, content=b"v1")
    b = store.revise(a.id, content=b"v2", provenance=[P1], observed_at="2026-08-11T09:00:00Z")
    assert b.id != a.id
    assert store.get(b.id)["derived_from"] == [a.id]
    stary = store.list_blocks(include_superseded=True)
    assert any(x["id"] == a.id and x["valid_to"] is not None for x in stary)
    assert [x["id"] for x in store.list_blocks()] == [b.id]


def test_i8_forget_to_tombstone_a_nie_zniknecie(store):
    r = _put(store)
    assert store.forget(r.id, reason="test", observed_at=T)
    assert store.get(r.id) is None
    assert store.stats()["blocks_total"] == 1
    assert any(e["op"] == "forget" for e in store.journal())


def test_i9_stats_zgadza_sie_z_pelnym_skanem(store):
    for i in range(5):
        _put(store, content=f"x{i}".encode())
    store.forget(_put(store, content=b"x0").id, reason="r", observed_at=T)
    s = store.stats()
    assert s["blocks_live"] == len(store.list_blocks())
    assert s["blocks_total"] == 5 and s["tombstoned"] == 1


def test_c4_skasowanie_indeksow_i_odbudowa_nie_zmienia_odpowiedzi(store):
    for i in range(4):
        _put(store, content=f"y{i}".encode())
    przed = store.list_blocks(kind="artifact", scope="project:acae")
    store.drop_indexes()
    bez_indeksu = store.list_blocks(kind="artifact", scope="project:acae")
    store.rebuild_indexes()
    assert przed == bez_indeksu == store.list_blocks(kind="artifact", scope="project:acae")


def test_journal_rosnie_i_zapisuje_operacje(store):
    r = _put(store)
    store.forget(r.id, reason="r", observed_at=T)
    ops = [e["op"] for e in store.journal()]
    assert ops == ["put", "forget"]


def test_by_content_znajduje_po_hashu_i_scope(store):
    r = _put(store)
    assert store.by_content(r.content_hash, "project:acae")["id"] == r.id
    assert store.by_content(r.content_hash, "global") is None


def test_id_jest_sortowalny_czasowo_i_wyprowadzony_z_tresci(store):
    a = _put(store, content=b"a", observed_at="2026-08-11T08:00:00Z")
    b = _put(store, content=b"b", observed_at="2026-08-11T09:00:00Z")
    assert a.id < b.id and a.content_hash.split(":")[1][:16] in a.id


@pytest.mark.parametrize("kw", [{"kind": "nieznany"}, {"scope": "byle co"}, {"provenance": []}])
def test_kontrakt_jest_egzekwowany_glosno(store, kw):
    with pytest.raises(StoreError):
        _put(store, **kw)


def test_nieznany_trust_tier_jest_odrzucony(store):
    with pytest.raises(StoreError):
        _put(store, provenance=[Provenance("u", "j", "t", trust_tier="T9")])


def test_magazyn_nie_dotyka_cbms():
    """D1 w postaci wykonywalnej: zaden import z aions_core nie moze wejsc do store.py."""
    import ast
    import pathlib

    src = pathlib.Path(__file__).resolve().parents[1] / "src" / "acae" / "store.py"
    drzewo = ast.parse(src.read_bytes())
    moduly = set()
    for node in ast.walk(drzewo):
        if isinstance(node, ast.Import):
            moduly.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            moduly.add(node.module)
    zakazane = [m for m in moduly if "aions_core" in m or "chroma" in m.lower() or "cbms" in m.lower()]
    assert not zakazane, f"store.py importuje zakazane moduly: {zakazane}"
