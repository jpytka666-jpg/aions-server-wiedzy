"""
store.py — magazyn blokow ACAE. Jeden silnik, jedna transakcja.

DLACZEGO BLOBY SIEDZA W SQLITE, A NIE OBOK
------------------------------------------
PLAN v2 zakladal „SQLite + blobbing", czyli dwa magazyny. ADR-002 §5.4 ostrzega wprost,
ze silniki bez wspolnej transakcji wymagaja dwufazowego zapisu albo jednego magazynu,
a niezmiennik I4 zada, zeby blok byl widoczny we wszystkich indeksach albo w zadnym.
Osobny katalog blobow obok bazy to podrecznikowy dual-write: baza moze zapisac wiersz,
a plik nie powstanie (albo odwrotnie) i nie ma transakcji, ktora to cofnie.
Tresc idzie wiec do kolumny BLOB. Jeden silnik, jeden COMMIT, I4 spelnione z konstrukcji.

ZERO KONTAKTU Z CBMS
--------------------
Ten modul nie importuje niczego z `aions_core/memory/`, nie czyta `chunks/` i nie zna
Chromy. To jest operacyjna tresc decyzji D1 („zeby sie kociol nie robil z innymi blokami").

CZAS JEST WSTRZYKIWANY
----------------------
Kazda operacja zapisu przyjmuje `observed_at`. Bez tego testy zaleza od zegara, a `id`
bloku przestaje byc powtarzalne. Domyslnie brany jest czas systemowy — ale nigdy w srodku,
zawsze na brzegu wywolania.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Mapping, Sequence

from .canon import canonical_json, content_hash

SCHEMA_VERSION = 1

# ADR-002 §4.1 — wyliczenia normatywne, przepisane doslownie z dokumentu.
KINDS = ("fact", "episode", "procedure", "artifact", "observation", "belief")
SCOPE_RE = re.compile(r"^(global|project:[A-Za-z0-9._\-]+|session:[A-Za-z0-9._\-]+)$")

# UWAGA: ADR-002 NIE definiuje wartosci trust_tier. Podaje tylko przyklady T1 i T3 oraz
# to, ze tiery sa uporzadkowane, a T3 jest mniej zaufany niz T1. Ponizsza skala jest
# WYBOREM ACAE, nie cytatem z dokumentu — tak jest opisana w TERMS.md.
TRUST_TIERS = ("T0", "T1", "T2", "T3")

DDL = """
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Jedyne zrodlo prawdy (I1). Kazdy indeks musi dac sie odtworzyc z tej tabeli.
CREATE TABLE IF NOT EXISTS blocks (
    id            TEXT PRIMARY KEY,
    content_hash  TEXT NOT NULL,
    scope         TEXT NOT NULL,
    kind          TEXT NOT NULL,
    media_type    TEXT NOT NULL,
    content       BLOB NOT NULL,
    visibility    TEXT NOT NULL,
    trust_tier    TEXT NOT NULL,
    valid_from    TEXT NOT NULL,
    valid_to      TEXT,
    observed_at   TEXT NOT NULL,
    derived_from  TEXT NOT NULL,
    provenance    TEXT NOT NULL,
    UNIQUE (content_hash, scope)
);

-- I8: skasowanie jest tombstonem, nie zniknieciem. Fakt istnienia zostaje.
CREATE TABLE IF NOT EXISTS tombstones (
    block_id TEXT PRIMARY KEY,
    at       TEXT NOT NULL,
    reason   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS journal (
    seq      INTEGER PRIMARY KEY AUTOINCREMENT,
    at       TEXT NOT NULL,
    op       TEXT NOT NULL,
    block_id TEXT NOT NULL,
    detail   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS edges (
    src        TEXT NOT NULL,
    dst        TEXT NOT NULL,
    rel        TEXT NOT NULL,
    valid_from TEXT NOT NULL,
    valid_to   TEXT,
    PRIMARY KEY (src, dst, rel, valid_from)
);
"""

# Indeksy sa POCHODNE. Trzymane osobno od DDL, zeby test C4 mogl je skasowac
# i odbudowac, dowodzac ze tabela blokow jest samowystarczalna.
INDEX_DDL = (
    "CREATE INDEX IF NOT EXISTS idx_blocks_kind_scope ON blocks (kind, scope)",
    "CREATE INDEX IF NOT EXISTS idx_blocks_hash ON blocks (content_hash)",
    "CREATE INDEX IF NOT EXISTS idx_blocks_valid ON blocks (valid_to)",
)
INDEX_NAMES = ("idx_blocks_kind_scope", "idx_blocks_hash", "idx_blocks_valid")


class StoreError(ValueError):
    """Naruszenie kontraktu magazynu. Glosne, nigdy ciche."""


@dataclass(frozen=True)
class Provenance:
    """
    ADR-002 §4.1 opisuje `provenance` jako „zrodlo, job, narzedzie, trust tier —
    nigdy nietracone". NAZW PODPOL dokument nie podaje; ponizsze sa wyborem ACAE.
    """

    source_uri: str
    job_id: str
    tool: str
    trust_tier: str = "T1"

    def as_dict(self) -> dict:
        if self.trust_tier not in TRUST_TIERS:
            raise StoreError(f"nieznany trust_tier: {self.trust_tier!r}; dozwolone {TRUST_TIERS}")
        return {
            "source_uri": self.source_uri,
            "job_id": self.job_id,
            "tool": self.tool,
            "trust_tier": self.trust_tier,
        }


@dataclass(frozen=True)
class PutResult:
    id: str
    content_hash: str
    created: bool
    merged: bool


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _lowest_tier(tiers: Iterable[str]) -> str:
    """
    I7: blok wyprowadzony dziedziczy NAJNIZSZY tier zrodel.

    „Najnizszy" znaczy najmniej zaufany, czyli najdalszy w TRUST_TIERS. Domyslnie T0,
    zeby pusty zbior zrodel nie obnizal niczego sztucznie.
    """
    worst = 0
    for tier in tiers:
        if tier not in TRUST_TIERS:
            raise StoreError(f"nieznany trust_tier: {tier!r}")
        worst = max(worst, TRUST_TIERS.index(tier))
    return TRUST_TIERS[worst]


def _merge_provenance(existing: Sequence[Mapping], incoming: Sequence[Mapping]) -> list[dict]:
    """
    I6: scalenie daje SUME prowenancji, nigdy wybor jednej.

    Deduplikacja po postaci kanonicznej, sortowanie po tej samej postaci — zeby dwa
    zapisy tych samych zrodel w innej kolejnosci dawaly identyczny wiersz.
    """
    seen: dict[bytes, dict] = {}
    for record in list(existing) + list(incoming):
        seen[canonical_json(record)] = dict(record)
    return [seen[key] for key in sorted(seen)]


class BlockStore:
    """Magazyn blokow. Cale I/O w jednym silniku, kazdy zapis w jednej transakcji."""

    def __init__(self, path: str) -> None:
        self._db = sqlite3.connect(path)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys = ON")
        # Wymuszony zapis na dysk przed potwierdzeniem — bez tego I4 obowiazuje
        # tylko do pierwszej utraty zasilania.
        self._db.execute("PRAGMA synchronous = FULL")
        with self._db:
            self._db.executescript(DDL)
            self._db.execute(
                "INSERT OR IGNORE INTO meta (key, value) VALUES ('schema_version', ?)",
                (str(SCHEMA_VERSION),),
            )
        self.rebuild_indexes()

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> "BlockStore":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # ------------------------------------------------------------------ indeksy

    def rebuild_indexes(self) -> None:
        """
        C4: indeksy sa w pelni pochodne. Skasowanie ich i odbudowa nie moze zmienic
        ani jednej odpowiedzi — bo odpowiedzi pochodza z tabeli blokow, nie z indeksu.
        """
        with self._db:
            for statement in INDEX_DDL:
                self._db.execute(statement)

    def drop_indexes(self) -> None:
        with self._db:
            for name in INDEX_NAMES:
                self._db.execute(f"DROP INDEX IF EXISTS {name}")

    # ------------------------------------------------------------------- zapis

    def put(
        self,
        *,
        content: bytes,
        kind: str,
        scope: str,
        provenance: Sequence[Provenance],
        media_type: str = "application/octet-stream",
        visibility: str = "owner",
        derived_from: Sequence[str] = (),
        valid_from: str | None = None,
        observed_at: str | None = None,
    ) -> PutResult:
        """
        Zapis idempotentny wzgledem `(content_hash, scope)` — I5.

        Powtorka NIE tworzy duplikatu i NIE nadpisuje: dokleja prowenancje do istniejacego
        bloku (I6) i zwraca `created=False, merged=True`. Cala operacja w jednej transakcji,
        wiec blok jest widoczny w calosci albo wcale (I4).
        """
        if kind not in KINDS:
            raise StoreError(f"nieznany kind: {kind!r}; dozwolone {KINDS}")
        if not SCOPE_RE.match(scope):
            raise StoreError(f"zly scope: {scope!r}; oczekiwano global | project:<id> | session:<id>")
        if not provenance:
            raise StoreError("prowenancja jest wymagana — I6 nie pozwala jej nie miec")

        digest = content_hash(content)
        prov = [p.as_dict() for p in provenance]
        tier = _lowest_tier(p["trust_tier"] for p in prov)
        stamp = observed_at or _now_iso()
        began = valid_from or stamp
        block_id = f"{stamp}-{digest.split(':', 1)[1][:16]}"

        with self._db:  # jedna transakcja = I4
            row = self._db.execute(
                "SELECT id, provenance, trust_tier FROM blocks WHERE content_hash = ? AND scope = ?",
                (digest, scope),
            ).fetchone()

            if row is not None:
                merged = _merge_provenance(
                    __import__("json").loads(row["provenance"]), prov
                )
                self._db.execute(
                    "UPDATE blocks SET provenance = ?, trust_tier = ? WHERE id = ?",
                    (
                        canonical_json(merged).decode("utf-8"),
                        _lowest_tier([row["trust_tier"], tier]),
                        row["id"],
                    ),
                )
                self._journal(stamp, "merge", row["id"], {"added": len(prov)})
                return PutResult(id=row["id"], content_hash=digest, created=False, merged=True)

            self._db.execute(
                "INSERT INTO blocks (id, content_hash, scope, kind, media_type, content,"
                " visibility, trust_tier, valid_from, valid_to, observed_at, derived_from, provenance)"
                " VALUES (?,?,?,?,?,?,?,?,?,NULL,?,?,?)",
                (
                    block_id, digest, scope, kind, media_type, content,
                    visibility, tier, began, stamp,
                    canonical_json(sorted(derived_from)).decode("utf-8"),
                    canonical_json(prov).decode("utf-8"),
                ),
            )
            self._journal(stamp, "put", block_id, {"kind": kind, "scope": scope, "bytes": len(content)})
        return PutResult(id=block_id, content_hash=digest, created=True, merged=False)

    def revise(
        self,
        block_id: str,
        *,
        content: bytes,
        provenance: Sequence[Provenance],
        observed_at: str | None = None,
    ) -> PutResult:
        """
        I2: brak mutacji w miejscu. Rewizja tworzy NOWY blok, staremu ustawia `valid_to`.

        Nowy blok NIE dziedziczy id (ADR-002 tego nie gwarantuje) — powiazanie idzie
        przez `derived_from`. Trust tier nowego bloku spada do najnizszego ze zrodel (I7).
        """
        stamp = observed_at or _now_iso()
        old = self.get(block_id)
        if old is None:
            raise StoreError(f"nie ma bloku {block_id!r} albo jest tombstonowany")

        result = self.put(
            content=content,
            kind=old["kind"],
            scope=old["scope"],
            provenance=provenance,
            media_type=old["media_type"],
            visibility=old["visibility"],
            derived_from=[block_id],
            observed_at=stamp,
        )
        with self._db:
            self._db.execute(
                "UPDATE blocks SET valid_to = ? WHERE id = ? AND valid_to IS NULL", (stamp, block_id)
            )
            self._db.execute(
                "UPDATE blocks SET trust_tier = ? WHERE id = ?",
                (_lowest_tier([old["trust_tier"]] + [p.trust_tier for p in provenance]), result.id),
            )
            self._journal(stamp, "revise", result.id, {"supersedes": block_id})
        return result

    def forget(self, block_id: str, *, reason: str, observed_at: str | None = None) -> bool:
        """
        I8: tombstone plus wpis w journalu. Tresc znika z odczytow, fakt istnienia zostaje.

        ADR-002 NIE gwarantuje fizycznego usuniecia i my tez go nie obiecujemy — kolumna
        `content` zostaje nietknieta, zeby `forget` bylo odwracalne przez audyt.
        """
        stamp = observed_at or _now_iso()
        with self._db:
            exists = self._db.execute("SELECT 1 FROM blocks WHERE id = ?", (block_id,)).fetchone()
            if exists is None:
                return False
            self._db.execute(
                "INSERT OR IGNORE INTO tombstones (block_id, at, reason) VALUES (?,?,?)",
                (block_id, stamp, reason),
            )
            self._journal(stamp, "forget", block_id, {"reason": reason})
        return True

    def _journal(self, at: str, op: str, block_id: str, detail: Mapping) -> None:
        self._db.execute(
            "INSERT INTO journal (at, op, block_id, detail) VALUES (?,?,?,?)",
            (at, op, block_id, canonical_json(detail).decode("utf-8")),
        )

    # ------------------------------------------------------------------ odczyt

    def _row_to_block(self, row: sqlite3.Row) -> dict:
        import json

        return {
            "id": row["id"],
            "content_hash": row["content_hash"],
            "scope": row["scope"],
            "kind": row["kind"],
            "media_type": row["media_type"],
            "content": row["content"],
            "visibility": row["visibility"],
            "trust_tier": row["trust_tier"],
            "valid_from": row["valid_from"],
            "valid_to": row["valid_to"],
            "observed_at": row["observed_at"],
            "derived_from": json.loads(row["derived_from"]),
            "provenance": json.loads(row["provenance"]),
        }

    def get(self, block_id: str) -> dict | None:
        row = self._db.execute(
            "SELECT b.* FROM blocks b LEFT JOIN tombstones t ON t.block_id = b.id"
            " WHERE b.id = ? AND t.block_id IS NULL",
            (block_id,),
        ).fetchone()
        return None if row is None else self._row_to_block(row)

    def by_content(self, digest: str, scope: str) -> dict | None:
        row = self._db.execute(
            "SELECT b.* FROM blocks b LEFT JOIN tombstones t ON t.block_id = b.id"
            " WHERE b.content_hash = ? AND b.scope = ? AND t.block_id IS NULL",
            (digest, scope),
        ).fetchone()
        return None if row is None else self._row_to_block(row)

    def list_blocks(self, *, kind: str | None = None, scope: str | None = None,
                    include_superseded: bool = False) -> list[dict]:
        sql = ["SELECT b.* FROM blocks b LEFT JOIN tombstones t ON t.block_id = b.id",
               "WHERE t.block_id IS NULL"]
        args: list[str] = []
        if kind is not None:
            sql.append("AND b.kind = ?"); args.append(kind)
        if scope is not None:
            sql.append("AND b.scope = ?"); args.append(scope)
        if not include_superseded:
            sql.append("AND b.valid_to IS NULL")
        sql.append("ORDER BY b.id")
        return [self._row_to_block(r) for r in self._db.execute(" ".join(sql), args)]

    def journal(self) -> list[dict]:
        import json

        return [
            {"seq": r["seq"], "at": r["at"], "op": r["op"],
             "block_id": r["block_id"], "detail": json.loads(r["detail"])}
            for r in self._db.execute("SELECT * FROM journal ORDER BY seq")
        ]

    def stats(self) -> dict:
        """
        I9: jedna odpowiedz na „ile pamietam", zgodna z pelnym skanem.

        Liczone SKANEM, nie z licznika. ADR-002 nie wymaga O(1), wymaga prawdy —
        a cache'owany licznik to najkrotsza droga do dwoch roznych odpowiedzi.
        """
        live = self._db.execute(
            "SELECT COUNT(*) c FROM blocks b LEFT JOIN tombstones t ON t.block_id = b.id"
            " WHERE t.block_id IS NULL AND b.valid_to IS NULL"
        ).fetchone()["c"]
        return {
            "blocks_total": self._db.execute("SELECT COUNT(*) c FROM blocks").fetchone()["c"],
            "blocks_live": live,
            "superseded": self._db.execute(
                "SELECT COUNT(*) c FROM blocks WHERE valid_to IS NOT NULL"
            ).fetchone()["c"],
            "tombstoned": self._db.execute("SELECT COUNT(*) c FROM tombstones").fetchone()["c"],
            "journal_entries": self._db.execute("SELECT COUNT(*) c FROM journal").fetchone()["c"],
            "bytes_stored": self._db.execute(
                "SELECT COALESCE(SUM(LENGTH(content)), 0) s FROM blocks"
            ).fetchone()["s"],
        }
