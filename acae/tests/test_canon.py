"""Testy warstwy kanonizujacej. Kazdy z nich pilnuje jednej przyczyny niedeterminizmu."""

from __future__ import annotations

import pytest

from acae.canon import canonical_json, content_hash, normalize_source, to_posix_rel


def test_content_hash_ma_nazwany_prefiks_i_jest_powtarzalny():
    first = content_hash(b"abc")
    assert first == content_hash(b"abc")
    assert first.startswith("blake2b256:")
    # 11 znakow prefiksu z dwukropkiem + 64 znaki hex
    assert len(first) == len("blake2b256:") + 64


def test_content_hash_zalezy_wylacznie_od_tresci():
    assert content_hash(b"abc") != content_hash(b"abd")


def test_normalize_source_sprowadza_konce_linii_do_lf():
    assert normalize_source(b"a\r\nb\rc\n") == b"a\nb\nc\n"


def test_normalize_source_nie_rozdmuchuje_crlf_na_dwie_linie():
    """Kolejnosc podmian: najpierw CRLF, potem samotne CR. Odwrotna dawalaby \\n\\n."""
    assert normalize_source(b"a\r\nb") == b"a\nb"


def test_normalize_source_scina_bom():
    assert normalize_source(b"\xef\xbb\xbfdef f():\n") == b"def f():\n"


def test_ten_sam_plik_z_crlf_i_lf_ma_ten_sam_hash():
    """To jest sedno: bez tego pack_hash rozjezdzalby sie miedzy Windowsem a Linuksem."""
    assert content_hash(normalize_source(b"x = 1\r\ny = 2\r\n")) == content_hash(
        normalize_source(b"x = 1\ny = 2\n")
    )


def test_canonical_json_sortuje_klucze():
    assert canonical_json({"b": 1, "a": 2}) == b'{"a":2,"b":1}\n'


def test_canonical_json_nie_escapuje_znakow_spoza_ascii():
    assert "ó".encode("utf-8") in canonical_json({"k": "ó"})


def test_canonical_json_odrzuca_floaty():
    with pytest.raises(TypeError):
        canonical_json({"a": 1.5})


def test_canonical_json_odrzuca_floaty_w_zagniezdzeniu():
    with pytest.raises(TypeError):
        canonical_json({"a": {"b": [1, 2, 3.0]}})


def test_canonical_json_jest_powtarzalny_niezaleznie_od_kolejnosci_wstawiania():
    first = {}
    first["z"] = 1
    first["a"] = 2
    second = {}
    second["a"] = 2
    second["z"] = 1
    assert canonical_json(first) == canonical_json(second)


@pytest.mark.parametrize(
    "path,root,expected",
    [
        ("E:\\repo\\a\\b.py", "E:\\repo", "a/b.py"),
        ("/repo/a/b.py", "/repo", "a/b.py"),
        ("E:\\repo\\x.py", "E:\\repo", "x.py"),
    ],
)
def test_to_posix_rel_daje_jedna_pisownie(path, root, expected):
    assert to_posix_rel(path, root) == expected
