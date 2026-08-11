"""
Cztery testy determinizmu z bramki M1, plus piaty o koncach linii.

PLAN v2 mial tu test "uruchom ponownie po 24 h". Te testy mierza te sama wlasnosc
ostrzej i daja sie uruchomic w kazdej chwili: kazdy z nich zmienia dokladnie jedna
rzecz, ktora NIE JEST trescia repo, i sprawdza, ze pack_hash sie nie poruszyl.
"""

from __future__ import annotations

import os
from pathlib import Path

from conftest import MemoryLocator, MemoryReader

from acae.core import PackRequest, build_pack
from acae.pack import FsLocator, FsReader


def _build_from_disk(root) -> str:
    locator = FsLocator(root=str(root), roots=["pkg"], prune_dirs=[], max_file_bytes=1 << 20)
    return build_pack(PackRequest(root=Path(root).name), locator, FsReader(str(root))).pack_hash


def test_powtorzenie_daje_ten_sam_pack_hash(mini_repo):
    assert _build_from_disk(mini_repo) == _build_from_disk(mini_repo)


def test_odwrocona_kolejnosc_z_locatora_daje_ten_sam_pack_hash(blobs):
    """
    Rdzen nie moze UFAC, ze Locator sortuje — ma sortowac sam.

    Gdyby polegal na kontrakcie portu, ten test przechodzilby przez przypadek.
    """
    rosnaco = sorted(blobs)
    a = build_pack(PackRequest(root="repo"), MemoryLocator(rosnaco), MemoryReader(blobs))
    b = build_pack(PackRequest(root="repo"), MemoryLocator(list(reversed(rosnaco))), MemoryReader(blobs))
    assert a.pack_hash == b.pack_hash


def test_zmiana_mtime_nie_zmienia_pack_hash(mini_repo):
    """Hash ma pochodzic z tresci. mtime to metadana systemu plikow, nie tresc."""
    before = _build_from_disk(mini_repo)
    os.utime(mini_repo / "pkg" / "alpha.py", (1_600_000_000, 1_600_000_000))
    assert _build_from_disk(mini_repo) == before


def test_inny_katalog_roboczy_nie_zmienia_pack_hash(mini_repo, tmp_path, monkeypatch):
    before = _build_from_disk(mini_repo)
    gdzie_indziej = tmp_path / "gdzie_indziej"
    gdzie_indziej.mkdir()
    monkeypatch.chdir(gdzie_indziej)
    assert _build_from_disk(mini_repo) == before


def test_konce_linii_na_dysku_nie_zmieniaja_pack_hash(mini_repo):
    """
    To jest warunek porownywalnosci miedzy maszynami.

    Repo ma core.autocrlf=true, wiec ten sam commit lezy na dysku z CRLF na Windowsie
    i z LF na Linuksie. Bez normalizacji na brzegu pack_hash bylby wlasnoscia systemu
    operacyjnego, a nie tresci kodu.
    """
    before = _build_from_disk(mini_repo)
    target = mini_repo / "pkg" / "alpha.py"
    target.write_bytes(target.read_bytes().replace(b"\n", b"\r\n"))
    assert _build_from_disk(mini_repo) == before
