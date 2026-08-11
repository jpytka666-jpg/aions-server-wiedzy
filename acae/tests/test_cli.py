"""
CLI dziala samo — bez serwera MCP, bez demona, bez sieci.

To jest bramka M1 "CLI bez MCP". Reguly z PLAN v2 §6: pack nigdy nie wraca trescia
przez transport, tylko sciezka — wiec musi istniec droga, ktora w ogole transportu
nie potrzebuje.
"""

from __future__ import annotations

import json

from acae.cli import main


def _pack(root, config, out, extra=()):
    return main(["pack", "--root", str(root), "--config", str(config), "--out", str(out), *extra])


def test_cli_buduje_pack_i_konczy_zerem(mini_repo, mini_config, tmp_path):
    out = tmp_path / "out"
    assert _pack(mini_repo, mini_config, out) == 0
    assert (out / "content.txt").exists()
    assert (out / "manifest.json").exists()


def test_manifest_ma_oczekiwany_ksztalt(mini_repo, mini_config, tmp_path):
    out = tmp_path / "out"
    _pack(mini_repo, mini_config, out)
    manifest = json.loads((out / "manifest.json").read_bytes())
    assert manifest["schema"] == "acae.pack.v1"
    assert manifest["mode"] == "outline"
    assert manifest["counts"]["files"] == 2
    assert manifest["pack_hash"].startswith("blake2b256:")
    assert manifest["files"] == sorted(manifest["files"], key=lambda f: f["path"])


def test_dwa_uruchomienia_daja_pliki_identyczne_co_do_bajta(mini_repo, mini_config, tmp_path):
    first, second = tmp_path / "a", tmp_path / "b"
    _pack(mini_repo, mini_config, first)
    _pack(mini_repo, mini_config, second)
    assert (first / "content.txt").read_bytes() == (second / "content.txt").read_bytes()
    assert (first / "manifest.json").read_bytes() == (second / "manifest.json").read_bytes()


def test_artefakty_nie_maja_crlf_nawet_na_windowsie(mini_repo, mini_config, tmp_path):
    """Zapis idzie bajtowo; tryb tekstowy wstawilby \\r\\n i uniewaznil hash."""
    out = tmp_path / "out"
    _pack(mini_repo, mini_config, out)
    assert b"\r\n" not in (out / "content.txt").read_bytes()
    assert b"\r\n" not in (out / "manifest.json").read_bytes()


def test_przekroczony_budzet_tokenow_konczy_sie_jedynka(mini_repo, mini_config, tmp_path):
    assert _pack(mini_repo, mini_config, tmp_path / "c", extra=("--budget", "1")) == 1


def test_zmieszczony_budzet_konczy_sie_zerem(mini_repo, mini_config, tmp_path):
    assert _pack(mini_repo, mini_config, tmp_path / "d", extra=("--budget", "100000")) == 0
