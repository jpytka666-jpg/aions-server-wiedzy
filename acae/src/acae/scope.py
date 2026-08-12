"""
scope.py — M6. Zawezanie przestrzeni zamiast rozszerzania zapytania.

DLACZEGO TO NIE JEST OSMY WARIANT TEGO SAMEGO
---------------------------------------------
Siedem poprzednich mechanizmow DODAWALO terminy do zapytania i kazdy z nich obnizyl
albo zostawil bez zmian `MRR`. Przyczyna: dodany termin sciaga do rankingu symbole,
ktore pasuja TYLKO do niego, i te wypychaja wlasciwa odpowiedz w dol.

Ten modul nie dodaje ani jednego slowa. On **usuwa konkurencje**: wybiera podzbior plikow,
a ranking bazowy dziala wylacznie w nim, na oryginalnych tokenach pytania.

CO MOWI POMIAR DIAGNOSTYCZNY
----------------------------
Z 30 pytan roboczych wlasciwy symbol lezy: w top-10 w 8 przypadkach, na pozycji 11+
w 11 (mediana 16), a w 11 ma wynik ZERO. Zawezanie moze odzyskac tylko te srodkowe 11 —
sufit tej dzwigni to 63,3%. Symbolu z zerowym wynikiem zadna bramka nie wciagnie.

TRZY WARSTWY ZAKRESU
--------------------
A. **Wspolzmiennosc commitow** — pliki zmieniane razem naleza do siebie. Pokrywa 100%
   plikow, w odroznieniu od CBMS (13%).
B. **Spojne skladowe grafu wywolan** — bez detekcji spolecznosci z ziarnem; spojne
   skladowe sa deterministyczne z definicji.
C. **Katalogi** — najprostszy i najstabilniejszy podzial.

ROUTOWANIE WYLACZNIE PO LUDZKIEJ PROZIE
---------------------------------------
Pytanie dopasowujemy do chunkow CBMS i komunikatow commitow — czyli do tekstu pisanego
przez czlowieka o tym systemie. NIGDY do kodu. Proza wskazuje ZAKRES, nie symbol.
Dzieki temu slowo `machine` nie musi wystepowac w kodzie: wystarczy, ze padlo
w komunikacie commita, ktory dotykal wlasciwego pliku.

HIGIENA DANYCH, NIE POKRETLA
----------------------------
Pomijamy commity `checkpoint:` (nasze wlasne artefakty z hooka, jeden ma 52 pliki)
oraz commity dotykajace wiecej niz `MAX_COMMIT_FILES` plikow — taki commit nie dotyczy
jednego pojecia i polaczylby wszystko ze wszystkim.
"""

from __future__ import annotations

import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Mapping, Sequence

from .symbols import NoGrammar, index_from_bytes

SCHEMA = "acae.scope.v1"

# Prerejestrowane, ustalone przed pomiarem.
MIN_COCHANGE = 3
TOP_SCOPES = 3

# Higiena danych — nie pokretla strojenia.
MAX_COMMIT_FILES = 20
SKIP_COMMIT_PREFIX = "checkpoint:"

TOKEN_RE = re.compile(r"[a-z_][a-z0-9_]{2,}")
_PREFIX_VAR = re.compile(r"^\$\{[^}]+\}/")
_PREFIX_DRIVE = re.compile(r"^[A-Za-z]:/")
_PREFIX_REPO = re.compile(r"^(?:e:/)?server wiedzy/", re.IGNORECASE)
BACKSLASH = chr(92)


@dataclass(frozen=True)
class ScopeHit:
    """Paragon jednego wybranego zakresu: skad sie wzial i ktore slowa go wskazaly."""

    scope_id: str
    kind: str
    score: int
    matched_terms: tuple[str, ...]
    evidence: tuple[str, ...]
    files: int

    def as_dict(self) -> dict:
        return {
            "rule": "scope_gate",
            "scope_id": self.scope_id,
            "kind": self.kind,
            "score": self.score,
            "matched_terms": list(self.matched_terms),
            "evidence": list(self.evidence),
            "files_in_scope": self.files,
        }


def _norm_path(raw: str) -> str:
    s = str(raw).replace(BACKSLASH, "/")
    s = _PREFIX_VAR.sub("", s)
    s = _PREFIX_DRIVE.sub("", s)
    s = _PREFIX_REPO.sub("", s)
    return s


class _Union:
    """Zbiory rozlaczne. Kolejnosc laczenia nie wplywa na sklad skladowych."""

    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, a: str) -> str:
        self.parent.setdefault(a, a)
        while self.parent[a] != a:
            self.parent[a] = self.parent[self.parent[a]]
            a = self.parent[a]
        return a

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            lo, hi = sorted((ra, rb))
            self.parent[hi] = lo

    def groups(self, members: Iterable[str]) -> dict[str, list[str]]:
        out: dict[str, list[str]] = defaultdict(list)
        for m in sorted(members):
            out[self.find(m)].append(m)
        return dict(out)


class ScopeIndex:
    """
    Trzy warstwy zakresu plus odwrocony indeks ludzkiej prozy. Budowany raz.

    `route()` zwraca zakresy, `gate()` zwraca zbior plikow do przeszukania.
    Gdy zaden zakres nie trafi — `gate()` zwraca CALY zbior i oznacza to jako fallback.
    Bez tego bramka mogłaby wyciac wlasciwy plik i obnizyc recall ponizej baseline.
    """

    def __init__(
        self,
        entries: Sequence[Mapping[str, object]],
        reader,
        repo_root: str,
        chunks_dir: str | None = None,
        descriptions: Mapping[str, str] | None = None,
    ) -> None:
        self.repo_root = Path(repo_root)
        self.files: list[str] = sorted(str(e["path"]) for e in entries)
        self.symbols_by_file: dict[str, list] = {
            str(e["path"]): list(e["symbols"]) for e in entries  # type: ignore[arg-type]
        }
        self.scopes: dict[str, frozenset[str]] = {}
        self._build_cochange()
        self._build_callgraph(entries, reader)
        self._build_directories()
        self.prose_index, self.prose_docs = self._build_prose(chunks_dir, descriptions)

    # ------------------------------------------------------------ zakresy

    def _git(self, args: list[str]) -> str:
        proc = subprocess.run(
            ["git", *args], cwd=self.repo_root,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        return proc.stdout.decode("utf-8", "replace") if proc.returncode == 0 else ""

    def _commits(self) -> list[tuple[str, str, list[str]]]:
        """(sha, komunikat, pliki .py w zakresie). Z higiena opisana w docstringu modulu."""
        raw = self._git(["log", "--name-only", "--format=%x1e%H%x1f%s%n%b%x1f"])
        w_zakresie = set(self.files)
        out: list[tuple[str, str, list[str]]] = []
        for block in raw.split("\x1e"):
            if "\x1f" not in block:
                continue
            sha, _, rest = block.partition("\x1f")
            message, _, names = rest.partition("\x1f")
            if message.strip().lower().startswith(SKIP_COMMIT_PREFIX):
                continue
            pliki = [n.strip() for n in names.splitlines() if n.strip() in w_zakresie]
            if not pliki or len(pliki) > MAX_COMMIT_FILES:
                continue
            out.append((sha.strip()[:12], message.strip(), sorted(set(pliki))))
        return out

    def _build_cochange(self) -> None:
        pary: Counter = Counter()
        for _, _, pliki in self._commits():
            for i, a in enumerate(pliki):
                for b in pliki[i + 1:]:
                    pary[(a, b)] += 1
        u = _Union()
        for (a, b), n in pary.items():
            if n >= MIN_COCHANGE:
                u.union(a, b)
        for korzen, czlonkowie in u.groups(u.parent).items():
            if len(czlonkowie) > 1:
                self.scopes[f"cochange:{korzen}"] = frozenset(czlonkowie)

    def _build_callgraph(self, entries, reader) -> None:
        po_lisciu: dict[str, set[str]] = defaultdict(set)
        refs_pliku: dict[str, set[str]] = {}
        for entry in entries:
            rel = str(entry["path"])
            try:
                idx = index_from_bytes(rel, reader.read(rel))
            except (OSError, NoGrammar):
                continue
            wychodzace: set[str] = set()
            for name_path, sym in idx.symbols.items():
                po_lisciu[name_path.rsplit("/", 1)[-1].lower()].add(rel)
                for ref in sym.refs or ():
                    wychodzace.add(ref.strip().rsplit(".", 1)[-1].lower())
            refs_pliku[rel] = wychodzace

        u = _Union()
        for rel, wychodzace in refs_pliku.items():
            u.find(rel)
            for token in wychodzace:
                cele = po_lisciu.get(token, set())
                if 0 < len(cele) <= 3:      # wieloznaczny ref nie niesie sygnalu
                    for cel in cele:
                        if cel != rel:
                            u.union(rel, cel)
        for korzen, czlonkowie in u.groups(refs_pliku).items():
            if len(czlonkowie) > 1:
                self.scopes[f"callgraph:{korzen}"] = frozenset(czlonkowie)

    def _build_directories(self) -> None:
        po_katalogu: dict[str, list[str]] = defaultdict(list)
        for rel in self.files:
            po_katalogu[str(PurePosixPath(rel).parent)].append(rel)
        for katalog, pliki in po_katalogu.items():
            if len(pliki) > 1:
                self.scopes[f"dir:{katalog}"] = frozenset(sorted(pliki))

    # -------------------------------------------------------------- proza

    def _build_prose(self, chunks_dir: str | None, descriptions: Mapping[str, str] | None = None):
        """Odwrocony indeks: termin z ludzkiej prozy -> pliki, o ktorych ta proza mowi."""
        docs: list[tuple[str, str, frozenset[str]]] = []

        if descriptions is not None:
            # M9c: routing po wygenerowanych opisach ZAMIAST po commitach i chunkach CBMS.
            #
            # M6 przegral m.in. dlatego, ze zrodlem routingu bylo 22 dokumenty na 169 plikow,
            # a pokrycie CBMS to 13% repo — bramka nie miala czym rozroznic plikow i zostawiala
            # mediane 140 ze 169. Opis jest po jednym na KAZDY plik i wskazuje dokladnie
            # jeden plik, wiec przypiecie jest doskonale, a pokrycie pelne.
            #
            # Zrodla zakresow (A/B/C) oraz progi zostaja nietkniete — zmienia sie wylacznie
            # tekst, po ktorym idzie routing. To jest warunek „mechanizm nietkniety" z M9.
            for path, opis in sorted(descriptions.items()):
                if opis.strip():
                    docs.append((f"desc:{path}", opis, frozenset({path})))
            indeks: dict[str, Counter] = defaultdict(Counter)
            for ref, tekst, cele in docs:
                for token in set(TOKEN_RE.findall(tekst.lower())):
                    for plik in cele:
                        indeks[token][plik] += 1
            return indeks, docs

        for sha, message, pliki in self._commits():
            docs.append((f"commit:{sha}", message, frozenset(pliki)))

        katalog = Path(chunks_dir) if chunks_dir else self.repo_root / "aions_core" / "memory" / "chunks"
        if katalog.is_dir():
            import json
            w_zakresie = set(self.files)
            po_nazwie = {PurePosixPath(f).name: f for f in self.files}
            for p in sorted(katalog.glob("*.json")):
                try:
                    d = json.loads(p.read_text(encoding="utf-8", errors="replace"))
                except (OSError, ValueError):
                    continue
                cele: set[str] = set()
                for r in d.get("references") or []:
                    s = _norm_path(r)
                    if s in w_zakresie:
                        cele.add(s)
                    elif PurePosixPath(s).name in po_nazwie:
                        cele.add(po_nazwie[PurePosixPath(s).name])
                if cele:
                    tekst = f"{d.get('concept', '')} {d.get('content', '')}"
                    docs.append((f"cbms:{p.stem}", tekst, frozenset(cele)))

        indeks: dict[str, Counter] = defaultdict(Counter)
        for ref, tekst, cele in docs:
            for token in set(TOKEN_RE.findall(tekst.lower())):
                for plik in cele:
                    indeks[token][plik] += 1
        return indeks, docs

    # ------------------------------------------------------------ routing

    def route(self, terms: Sequence[str], top: int = TOP_SCOPES) -> list[ScopeHit]:
        """
        Zakresy wskazane przez ludzka proze. Pytanie NIE dotyka kodu na tym etapie.
        """
        punkty: dict[str, int] = defaultdict(int)
        slowa: dict[str, set[str]] = defaultdict(set)
        for term in sorted({t.lower() for t in terms if t}):
            liczniki = self.prose_index.get(term)
            if not liczniki:
                continue
            for scope_id, pliki in self.scopes.items():
                trafienia = sum(liczniki[f] for f in pliki if f in liczniki)
                if trafienia:
                    punkty[scope_id] += trafienia
                    slowa[scope_id].add(term)

        ranked = sorted(punkty.items(), key=lambda kv: (-kv[1], kv[0]))[:top]
        out: list[ScopeHit] = []
        for scope_id, score in ranked:
            kind = scope_id.split(":", 1)[0]
            dowody = tuple(
                ref for ref, _, cele in self.prose_docs
                if cele & self.scopes[scope_id]
            )[:3]
            out.append(ScopeHit(
                scope_id=scope_id, kind=kind, score=score,
                matched_terms=tuple(sorted(slowa[scope_id])),
                evidence=dowody, files=len(self.scopes[scope_id]),
            ))
        return out

    def gate(self, terms: Sequence[str], top: int = TOP_SCOPES) -> tuple[frozenset[str], list[ScopeHit], bool]:
        """Zwraca (pliki do przeszukania, paragony, czy zadzialal fallback)."""
        hits = self.route(terms, top)
        if not hits:
            return frozenset(self.files), [], True
        pliki: set[str] = set()
        for hit in hits:
            pliki |= self.scopes[hit.scope_id]
        if not pliki:
            return frozenset(self.files), hits, True
        return frozenset(pliki), hits, False
