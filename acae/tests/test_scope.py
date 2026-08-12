"""
test_scope.py — M6 Scope Gate.

Modul zostal ZMIERZONY I ODRZUCONY (STATE.md 2026-08-12T03:10), ale zostaje w repo jako
udokumentowany eksperyment. Testy maja dwa zadania:

1. Chronic czesci, ktore sa poprawne i moga sie przydac ponownie: higiene commitow,
   determinizm zbiorow rozlacznych, normalizacje sciezek, fallback bramki.
2. **Przypiac wady, ktore pomiar ujawnil**, zeby nikt ich nie „naprawil" przypadkiem
   i nie uznal, ze M6 nagle dziala. Testy `test_wada_*` opisuja zachowanie ZMIERZONE,
   nie pozadane. Jesli kiedys powstanie M6b, te testy MUSZA zostac swiadomie zmienione
   razem z nowa prerejestracja — i to jest ich cel.
"""

from __future__ import annotations

import json
import subprocess

import pytest

from acae.canon import normalize_source
from acae.scope import MAX_COMMIT_FILES, MIN_COCHANGE, ScopeIndex, _norm_path, _Union

SRC_HELPER = (
    b"def pomocnik(x):\n"
    b"    return x + 1\n"
)

SRC_UZYTKOWNIK = (
    b"def uzytkownik():\n"
    b"    return pomocnik(1)\n"
)

SRC_OSOBNY = (
    b"def osobny():\n"
    b"    return 0\n"
)


class DiskReader:
    """Reader nad prawdziwym drzewem. Normalizuje tak samo jak wersja produkcyjna."""

    def __init__(self, root) -> None:
        self._root = root

    def read(self, rel: str) -> bytes:
        return normalize_source((self._root / rel).read_bytes())


def _git(root, *args: str) -> None:
    proc = subprocess.run(["git", *args], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if proc.returncode != 0:
        raise RuntimeError(proc.stdout.decode("utf-8", "replace"))


def _entries(paths):
    """Minimalne wpisy. `route`/`gate` nie zagladaja do symboli, tylko do sciezek."""
    return [{"path": p, "symbols": []} for p in sorted(paths)]


@pytest.fixture
def repo_git(tmp_path):
    """
    Mini-repo z prawdziwa historia git:
      - trzy commity dotykajace a.py i b.py razem  -> para osiaga MIN_COCHANGE
      - jeden commit `checkpoint:`                 -> musi zostac pominiety
      - jeden commit szerszy niz MAX_COMMIT_FILES  -> musi zostac pominiety
    """
    root = tmp_path / "repo"
    (root / "pkg").mkdir(parents=True)
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "config", "user.name", "test")

    (root / "pkg" / "a.py").write_bytes(SRC_HELPER)
    (root / "pkg" / "b.py").write_bytes(SRC_UZYTKOWNIK)
    (root / "pkg" / "c.py").write_bytes(SRC_OSOBNY)

    for i, temat in enumerate(("maszyna zapisuje pamiec", "maszyna poprawka", "maszyna dokladka")):
        (root / "pkg" / "a.py").write_bytes(SRC_HELPER + f"# {i}\n".encode())
        (root / "pkg" / "b.py").write_bytes(SRC_UZYTKOWNIK + f"# {i}\n".encode())
        _git(root, "add", "pkg/a.py", "pkg/b.py")
        _git(root, "commit", "-q", "-m", temat)

    _git(root, "add", "pkg/c.py")
    _git(root, "commit", "-q", "-m", "checkpoint: przed edycja szeptem")

    szerokie = []
    for i in range(MAX_COMMIT_FILES + 1):
        rel = f"pkg/w{i:02d}.py"
        (root / rel).write_bytes(b"def w():\n    return 0\n")
        szerokie.append(rel)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "wielkiwymiatacz przebudowa wszystkiego")

    return root, ["pkg/a.py", "pkg/b.py", "pkg/c.py", *szerokie]


@pytest.fixture
def index(repo_git):
    root, paths = repo_git
    return ScopeIndex(_entries(paths), DiskReader(root), str(root))


# --------------------------------------------------------------- czesci poprawne


def test_union_niezalezny_od_kolejnosci():
    """Skladowe musza byc te same niezaleznie od kolejnosci laczenia — inaczej pada determinizm."""
    pary = [("b", "c"), ("a", "b"), ("d", "e")]
    a, b = _Union(), _Union()
    for x, y in pary:
        a.union(x, y)
    for x, y in reversed(pary):
        b.union(x, y)
    czlonkowie = ["a", "b", "c", "d", "e"]
    assert a.groups(czlonkowie) == b.groups(czlonkowie)


@pytest.mark.parametrize(
    "surowa, oczekiwana",
    [
        ("pkg" + chr(92) + "a.py", "pkg/a.py"),
        ("E:/server wiedzy/pkg/a.py", "pkg/a.py"),
        ("e:/SERVER WIEDZY/pkg/a.py", "pkg/a.py"),
        ("${AIONS_ROOT}/pkg/a.py", "pkg/a.py"),
        ("pkg/a.py", "pkg/a.py"),
    ],
)
def test_norm_path(surowa, oczekiwana):
    assert _norm_path(surowa) == oczekiwana


def test_commity_pomijaja_checkpointy_i_wielkie(index):
    """Higiena danych z docstringu modulu ma faktycznie dzialac."""
    komunikaty = [msg for _, msg, _ in index._commits()]
    assert not any(m.lower().startswith("checkpoint:") for m in komunikaty)
    assert not any("wielkiwymiatacz" in m for m in komunikaty)
    assert sum("maszyna" in m for m in komunikaty) == 3


def test_pominiete_commity_nie_trafiaja_do_prozy(index):
    """Skoro commit odrzucony, jego slowa nie moga routowac."""
    assert "maszyna" in index.prose_index
    assert "wielkiwymiatacz" not in index.prose_index
    assert "szeptem" not in index.prose_index


def test_cochange_powstaje_dopiero_przy_progu(index):
    """a.py i b.py zmieniane razem 3x (== MIN_COCHANGE); c.py nigdy z nimi."""
    cochange = {k: v for k, v in index.scopes.items() if k.startswith("cochange:")}
    assert cochange, f"brak zakresu wspolzmiennosci przy MIN_COCHANGE={MIN_COCHANGE}"
    razem = next(v for v in cochange.values() if "pkg/a.py" in v)
    assert "pkg/b.py" in razem
    assert "pkg/c.py" not in razem


def test_callgraph_laczy_wywolujacego_z_definicja(index):
    """b.py wola `pomocnik` zdefiniowany w a.py — musza wyladowac w jednej skladowej."""
    skladowe = [v for k, v in index.scopes.items() if k.startswith("callgraph:")]
    assert any("pkg/a.py" in s and "pkg/b.py" in s for s in skladowe)


def test_katalogi_tylko_dla_wiecej_niz_jednego_pliku(index):
    katalogi = {k: v for k, v in index.scopes.items() if k.startswith("dir:")}
    assert "dir:pkg" in katalogi
    assert all(len(v) > 1 for v in katalogi.values())


def test_fallback_gdy_zadne_slowo_nie_trafia(index):
    """Bez fallbacku bramka mogłaby wyciac wszystko i zabic recall."""
    pliki, hits, fallback = index.gate(["nieistniejacyterminzupelnie"])
    assert fallback is True
    assert hits == []
    assert pliki == frozenset(index.files)


def test_gate_zwraca_podzbior_i_paragony(index):
    pliki, hits, fallback = index.gate(["maszyna"])
    assert fallback is False
    assert hits
    assert pliki <= frozenset(index.files)
    for hit in hits:
        d = hit.as_dict()
        assert d["rule"] == "scope_gate"
        assert d["matched_terms"], "paragon bez slowa, ktore wskazalo zakres, jest bezuzyteczny"
        assert d["files_in_scope"] == len(index.scopes[hit.scope_id])


def test_route_deterministyczne(index):
    """Ta sama lista terminow, w innej kolejnosci i wielkosci liter — ten sam wynik."""
    a = index.route(["maszyna", "pamiec"])
    b = index.route(["PAMIEC", "Maszyna"])
    assert [h.as_dict() for h in a] == [h.as_dict() for h in b]


def test_proza_czyta_referencje_cbms(tmp_path, repo_git):
    """Chunk CBMS wskazujacy plik po samej nazwie tez ma routowac."""
    root, paths = repo_git
    chunks = tmp_path / "chunks"
    chunks.mkdir()
    (chunks / "KTEST01.json").write_text(
        json.dumps({
            "concept": "prowieniencja zapisu",
            "content": "tutaj doklejamy identyfikator maszyny wykonujacej zapis",
            "references": ["E:/server wiedzy/pkg/a.py"],
        }),
        encoding="utf-8",
    )
    idx = ScopeIndex(_entries(paths), DiskReader(root), str(root), chunks_dir=str(chunks))
    assert "identyfikator" in idx.prose_index
    assert idx.prose_index["identyfikator"]["pkg/a.py"] >= 1


# ------------------------------------------------------- wady przypiete pomiarem


def test_wada_punktacja_nie_normalizowana_przez_rozmiar(index):
    """
    ZMIERZONA WADA, nie zachowanie pozadane.

    `route()` sumuje trafienia po plikach zakresu i nie dzieli przez rozmiar, wiec zakres
    szerszy zbiera wiecej punktow **z definicji**, niezaleznie od trafnosci. W pomiarze M6
    dalo to `dir:aions_core/server` (22 pliki, wynik 6) PONIZEJ skladowej na 139 plikow
    (wynik 7), i dlatego `cochange` nie zostalo wybrane ani razu.

    Test odtwarza to na malej skali: zakres nadrzedny zawierajacy zakres wezszy nigdy
    nie moze miec nizszego wyniku.
    """
    hits = {h.scope_id: h.score for h in index.route(["maszyna"], top=99)}
    wask = next(k for k in hits if k.startswith("cochange:"))
    szer = "dir:pkg"
    assert index.scopes[wask] < index.scopes[szer], "zalozenie testu: cochange jest podzbiorem katalogu"
    assert hits[szer] >= hits[wask], (
        "gdyby to przestalo zachodzic, punktacja zostala znormalizowana — "
        "to jest zmiana konstrukcji i wymaga nowej prerejestracji, nie poprawki testu"
    )


def test_wada_bramka_prawie_nie_zaweza(index):
    """
    ZMIERZONA WADA. W pomiarze M6 mediana rozmiaru bramki to 140 ze 169 plikow (83%).
    Przyczyna: skladowe grafu wywolan zlepiaja sie, a katalogi sa grube.

    Tu pilnujemy samej wlasnosci strukturalnej, ktora do tego prowadzi: `gate()` bierze
    SUME plikow z top-N zakresow, wiec jeden szeroki zakres w czolowce przekresla
    zawezenie wniesione przez pozostale.
    """
    pliki, hits, _ = index.gate(["maszyna"])
    najszerszy = max(len(index.scopes[h.scope_id]) for h in hits)
    assert len(pliki) >= najszerszy, "suma zakresow nie moze byc mniejsza niz najszerszy skladnik"
