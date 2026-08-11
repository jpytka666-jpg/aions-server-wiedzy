"""
Rdzen bez dysku.

Kazdy test w tym pliku dziala na slowniku bajtow. Zaden nie tworzy pliku, nie wola gita
i nie zna katalogu roboczego. To jest bramka M1 "rdzen bez dysku" w postaci wykonywalnej.
"""

from __future__ import annotations

from conftest import MemoryLocator, MemoryReader

from acae.canon import canonical_json
from acae.core import PackRequest, build_pack


def _build(blobs, files=None, skipped=()):
    listing = sorted(blobs) if files is None else files
    return build_pack(
        PackRequest(root="repo"),
        MemoryLocator(listing, skipped),
        MemoryReader(blobs),
    )


def test_rdzen_sklada_pack_bez_dotykania_dysku(blobs):
    result = _build(blobs)
    assert result.manifest["counts"]["files"] == 2  # alpha.py i delta.py; notes.md odpada
    assert result.manifest["counts"]["symbols"] > 0
    assert result.pack_hash.startswith("blake2b256:")


def test_plik_bez_gramatyki_trafia_do_skipped_z_powodem(blobs):
    reasons = {s["path"]: s["reason"] for s in _build(blobs).manifest["skipped"]}
    assert reasons["pkg/notes.md"] == "no_grammar"


def test_plik_z_sekretem_nie_wchodzi_do_packa():
    result = _build({"pkg/leak.py": b'api_key = "ABCDEFGHIJKLMNOP"\n'})
    assert result.manifest["counts"]["files"] == 0
    entry = result.manifest["skipped"][0]
    assert entry["reason"] == "secret"
    assert entry["rules"] == ["assignment"]
    assert "ABCDEFGHIJKLMNOP" not in canonical_json(result.manifest).decode("utf-8")


def test_plik_binarny_odpada_zanim_dojdzie_do_parsera():
    assert _build({"pkg/bin.py": b"\x00\x01\x02"}).manifest["skipped"][0]["reason"] == "binary"


def test_brak_tresci_w_readerze_daje_unreadable():
    result = build_pack(PackRequest(root="repo"), MemoryLocator(["pkg/ghost.py"]), MemoryReader({}))
    assert result.manifest["skipped"][0]["reason"] == "unreadable"


def test_pominiecia_z_locatora_trafiaja_do_manifestu(blobs):
    result = _build(blobs, skipped=[{"path": "vendor/x.py", "reason": "ignored"}])
    reasons = {s["path"]: s["reason"] for s in result.manifest["skipped"]}
    assert reasons["vendor/x.py"] == "ignored"


def test_tresc_packa_ma_sygnatury_bez_cial(blobs):
    text = _build(blobs).content.decode("utf-8")
    assert "def gamma():" in text
    assert "return 2" not in text


def test_manifest_przechodzi_kanonizacje_czyli_nie_ma_w_nim_floatow(blobs):
    canonical_json(_build(blobs).manifest)


def test_pack_hash_zalezy_od_tresci(blobs):
    zmienione = dict(blobs)
    zmienione["pkg/delta.py"] = b"def delta(a, b):\n    return a - b\n"
    assert _build(blobs).pack_hash != _build(zmienione).pack_hash
