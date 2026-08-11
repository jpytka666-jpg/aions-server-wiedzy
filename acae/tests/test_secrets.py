"""
Testy skanera sekretow.

Zadnego prawdziwego ani prawdziwie wygladajacego klucza nie ma w tym pliku na stale —
tokeny testowe sa sklejane z kawalkow w czasie wykonania. Chodzi o to, zeby repo nie
zawieralo ciagu, ktory skaner sekretow (czyjkolwiek) uzna za wyciek.
"""

from __future__ import annotations

from acae.secrets import has_secret, scan_text

FAKE_ANTHROPIC = "sk-" + "ant-" + "A" * 30
FAKE_AWS = "AKIA" + "B" * 16
FAKE_GITHUB = "gh" + "p_" + "C" * 40


def _rules(text: str) -> set[str]:
    return {hit["rule"] for hit in scan_text(text)}


def test_wykrywa_przypisanie_klucza():
    assert "assignment" in _rules('api_key = "ABCDEFGHIJKLMNOP"')


def test_wykrywa_token_anthropic_bez_slowa_key_obok():
    assert "anthropic_key" in _rules(f'x = "{FAKE_ANTHROPIC}"')


def test_wykrywa_klucz_aws():
    assert "aws_access_key" in _rules(f'x = "{FAKE_AWS}"')


def test_wykrywa_token_github():
    assert "github_token" in _rules(f'x = "{FAKE_GITHUB}"')


def test_wykrywa_blok_klucza_prywatnego():
    assert "private_key_block" in _rules("-----BEGIN RSA PRIVATE KEY-----")


def test_odczyt_ze_srodowiska_nie_jest_wyciekiem():
    """To jest wzorzec, ktorego chcemy — nie wolno go karac."""
    assert scan_text('api_key = os.getenv("API_KEY", "")') == []


def test_placeholder_w_dokumentacji_nie_jest_wyciekiem():
    assert scan_text('api_key = "your-key-goes-here"') == []
    assert scan_text('api_key = "xxxxxxxxxxxxxxxx"') == []


def test_raport_nie_cytuje_tresci_trafienia():
    """Skaner, ktory przepisuje sekret do raportu, przenosi wyciek zamiast go zatrzymac."""
    hits = scan_text(f'x = "{FAKE_ANTHROPIC}"')
    assert hits
    for hit in hits:
        assert set(hit.keys()) == {"rule", "line"}
        assert FAKE_ANTHROPIC not in str(hit)


def test_numer_linii_wskazuje_wlasciwy_wiersz():
    text = "a = 1\n" + f'b = "{FAKE_AWS}"\n' + "c = 3\n"
    assert [h["line"] for h in scan_text(text)] == [2]


def test_has_secret_dziala_na_bajtach():
    assert has_secret(f'x = "{FAKE_AWS}"'.encode("utf-8"))
    assert not has_secret(b"def f():\n    return 1\n")
