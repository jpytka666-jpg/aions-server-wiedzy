"""
pack.py — adaptery dyskowe portow oraz zapis artefaktu.

Tu i tylko tu wolno dotknac dysku, gita i systemu plikow. Rdzen o niczym z tego nie wie.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path, PurePosixPath
from typing import Iterable, Mapping, Sequence

from .canon import canonical_json, normalize_source
from .core import PackResult


class FsLocator:
    """
    Wyznacza zakres na prawdziwym drzewie plikow.

    Kolejnosc wykluczen ma znaczenie i jest celowa:
      1. przyciecie katalogow (venv, __pycache__, node_modules) — zanim cokolwiek zapytamy,
      2. submoduly — git check-ignore ODMAWIA obslugi sciezek w ich wnetrzu (zwraca 128),
      3. .gitignore przez samego gita — git jest autorytetem dla wlasnego formatu,
      4. rozmiar,
      5. brak gramatyki.
    """

    def __init__(
        self,
        root: str,
        roots: Sequence[str],
        prune_dirs: Iterable[str],
        max_file_bytes: int,
    ) -> None:
        self._root = Path(root).resolve()
        self._roots = list(roots)
        self._prune = set(prune_dirs)
        self._max_bytes = max_file_bytes
        self._files: list[str] = []
        self._skipped: list[dict] = []
        self._scanned = False

    # ------------------------------------------------------------------ git

    def _git(self, args: list[str], stdin: bytes | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", *args],
            cwd=self._root,
            input=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def _submodules(self) -> list[str]:
        """Sciezki submodulow z indeksu (tryb 160000). Osobne repo — nie nasza tresc."""
        proc = self._git(["ls-files", "--stage"])
        if proc.returncode != 0:
            return []
        out = []
        for line in proc.stdout.decode("utf-8", "replace").split("\n"):
            if line.startswith("160000 "):
                _, _, rest = line.partition("\t")
                if rest.strip():
                    out.append(rest.strip())
        return sorted(out)

    def _ignored(self, rels: Sequence[str]) -> set[str]:
        if not rels:
            return set()
        payload = "\0".join(rels).encode("utf-8") + b"\0"
        proc = self._git(["check-ignore", "--stdin", "-z"], stdin=payload)
        if proc.returncode not in (0, 1):
            # Brak gita albo inny blad — nie zgadujemy regul .gitignore samodzielnie.
            return set()
        return {p for p in proc.stdout.decode("utf-8").split("\0") if p}

    # ----------------------------------------------------------------- scan

    def _scan(self) -> None:
        if self._scanned:
            return
        self._scanned = True

        sub_prefixes = tuple(f"{s}/" for s in self._submodules())
        candidates: list[str] = []

        for name in self._roots:
            base = self._root / name
            if not base.is_dir():
                continue
            # `os.walk` zamiast `rglob("*")`, zeby przycinac katalogi W TRAKCIE chodzenia,
            # a nie po fakcie. `rglob` wchodzil do `venv`, `node_modules` i `__pycache__`,
            # wyliczal wszystko w srodku i dopiero potem to odrzucal.
            #
            # Zmierzone przed zmiana: 6276 ms na wyznaczenie 1038 kandydatow, czyli szesc
            # milisekund na plik. Sam submodul `tools/ChromaFlowStudio` ma w venvie prawie
            # czternascie tysiecy plikow .py, ktore byly enumerowane po to, zeby je wyrzucic.
            #
            # Zbior wynikowy jest IDENTYCZNY: przycinane katalogi i tak byly odrzucane
            # bez sladu w `skipped`, wiec niewejscie do nich nie zmienia niczego widocznego.
            # Pliki submodulu NADAL sa enumerowane, bo one trafiaja do `skipped` i licza sie
            # do manifestu — dlatego `sub_prefixes` sprawdzamy dalej, a nie przycinamy.
            for dirpath, dirnames, filenames in os.walk(base):
                dirnames[:] = [d for d in dirnames if d not in self._prune]
                for fname in filenames:
                    path = Path(dirpath) / fname
                    rel_parts = path.relative_to(self._root).parts
                    if any(part in self._prune for part in rel_parts[:-1]):
                        continue
                    rel = PurePosixPath(*rel_parts).as_posix()
                    if rel.startswith(sub_prefixes):
                        self._skipped.append({"path": rel, "reason": "submodule"})
                        continue
                    candidates.append(rel)

        candidates.sort()
        ignored = self._ignored(candidates)

        for rel in candidates:
            if rel in ignored:
                self._skipped.append({"path": rel, "reason": "ignored"})
                continue
            try:
                size = (self._root / rel).stat().st_size
            except OSError:
                self._skipped.append({"path": rel, "reason": "unreadable"})
                continue
            if size > self._max_bytes:
                self._skipped.append({"path": rel, "reason": "too_large", "bytes": size})
                continue
            self._files.append(rel)

    def list_files(self) -> Sequence[str]:
        self._scan()
        return list(self._files)

    def skipped(self) -> Sequence[Mapping[str, object]]:
        self._scan()
        return list(self._skipped)


class FsReader:
    """Czyta z dysku i normalizuje NA BRZEGU — dalej w glab ida juz tylko bajty z LF."""

    def __init__(self, root: str) -> None:
        self._root = Path(root).resolve()

    def read(self, rel: str) -> bytes:
        return normalize_source((self._root / rel).read_bytes())


class FsStore:
    """Zapis bajtowy, bez trybu tekstowego — inaczej Windows wstawilby CRLF."""

    def __init__(self, out_dir: str) -> None:
        self._out = Path(out_dir)

    def write(self, name: str, data: bytes) -> str:
        target = self._out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return target.as_posix()


def write_pack(result: PackResult, store: FsStore) -> dict:
    """Artefakt to dwa pliki: tresc dla modelu i manifest dla maszyny."""
    return {
        "content": store.write("content.txt", result.content),
        "manifest": store.write("manifest.json", canonical_json(result.manifest)),
    }
