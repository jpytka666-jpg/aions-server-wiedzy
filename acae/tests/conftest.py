"""
conftest.py — wspolne przybory testow.

Mini-repo powstaje w tmp_path i znika po tescie. Nie ma katalogu fixtures/ z plikami
w repo: plik z podlozonym kluczem musialby tam lezec na stale, a guard_write.py i tak
zablokowalby jego zapis. Sekret budujemy w pamieci, w momencie testu.
"""

from __future__ import annotations

from typing import Mapping, Sequence

import pytest

from acae.canon import normalize_source

# Male, ale nie trywialne zrodla: klasa z metoda, funkcja modulowa, zagniezdzenie.
SRC_ALPHA = (
    b"class Alpha:\n"
    b"    def beta(self, x):\n"
    b"        return x + 1\n"
    b"\n"
    b"\n"
    b"def gamma():\n"
    b"    return 2\n"
)

SRC_DELTA = (
    b"def delta(a, b):\n"
    b'    """Suma."""\n'
    b"    return a + b\n"
)

# To samo co SRC_ALPHA, ale z koncami linii w stylu Windows — do testu normalizacji.
SRC_ALPHA_CRLF = SRC_ALPHA.replace(b"\n", b"\r\n")


class MemoryLocator:
    """Locator bez dysku. Przyjmuje liste w dowolnej kolejnosci — rdzen ma ja sam uporzadkowac."""

    def __init__(self, files: Sequence[str], skipped: Sequence[Mapping[str, object]] = ()) -> None:
        self._files = list(files)
        self._skipped = [dict(s) for s in skipped]

    def list_files(self) -> Sequence[str]:
        return list(self._files)

    def skipped(self) -> Sequence[Mapping[str, object]]:
        return list(self._skipped)


class MemoryReader:
    """Reader nad slownikiem bajtow. Normalizuje tak samo jak wersja dyskowa."""

    def __init__(self, blobs: Mapping[str, bytes]) -> None:
        self._blobs = dict(blobs)

    def read(self, rel: str) -> bytes:
        if rel not in self._blobs:
            raise OSError(f"brak w pamieci: {rel}")
        return normalize_source(self._blobs[rel])


@pytest.fixture
def blobs() -> dict[str, bytes]:
    return {
        "pkg/alpha.py": SRC_ALPHA,
        "pkg/delta.py": SRC_DELTA,
        "pkg/notes.md": b"# notatki\n",
    }


@pytest.fixture
def mini_repo(tmp_path):
    """Male drzewo na dysku: dwa zrodla z gramatyka, jedno bez."""
    root = tmp_path / "repo"
    (root / "pkg").mkdir(parents=True)
    (root / "pkg" / "alpha.py").write_bytes(SRC_ALPHA)
    (root / "pkg" / "delta.py").write_bytes(SRC_DELTA)
    (root / "pkg" / "notes.md").write_bytes(b"# notatki\n")
    return root


@pytest.fixture
def mini_config(tmp_path):
    """Config wskazujacy na mini-repo. Rooty wzgledne, jak w prawdziwym acae.toml."""
    cfg = tmp_path / "mini.toml"
    cfg.write_bytes(
        b"[pack]\n"
        b'roots = ["pkg"]\n'
        b'mode = "outline"\n'
        b"max_file_bytes = 1048576\n"
        b"\n"
        b"[baseline]\n"
        b"prune_dirs = []\n"
    )
    return cfg
