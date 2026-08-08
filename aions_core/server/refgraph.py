"""
refgraph.py v2 — miekki graf referencji dla CBMS.

ZMIANA WOBEC v1 (i powod jej istnienia)
---------------------------------------
v1 traktowala pole `references` jak twardy wskaznik: string musial sie zgadzac
co do znaku, inaczej krawedz byla martwa. To jest sztywne. Zmienisz id, przeniesiesz
plik, zaparkujesz chunk w kwarantannie — i graf sie sypie, mimo ze wiedza nie zniknela.
Na zywym store v1 raportowala 596 "martwych" krawedzi. Wiekszosc z nich nie byla martwa.
Cele siedzialy w `chunks_quarantine/`.

v2: referencja to WSKAZOWKA, nie wskaznik. Kazda krawedz przechodzi lancuch resolverow
i dostaje `confidence` + `resolver` + `note`. Nierozstrzygnieta krawedz NIE ginie —
degraduje sie do wskazowki z zachowanym oryginalem. Graf nie ma stanu "martwy",
ma stan "slabo rozstrzygniety", a to jest informacja, nie awaria.

LANCUCH RESOLVEROW (malejaca pewnosc)
    exact       1.00  id obecne w aktywnym store
    manifest    0.95  id obecne w knowledge_manifest.chunk_index
    parked      0.80  id obecne w chunks_quarantine — KRAWEDZ ZYJE, wezel zaparkowany
    normalized  0.75  trafienie po normalizacji (wielkosc liter, biale znaki, prefiks)
    file        0.70  referencja plikowa dopasowana po nazwie w drzewie projektu
    concept     0.60  raw pokrywa sie z nazwa konceptu
    semantic    0.30-0.55  pokrycie tokenow wzgledem concept + poczatek content
    unresolved  0.00  zachowana jako wskazowka

Zero zaleznosci poza stdlib. Nie importuje AIONS. Nic nie zapisuje w pamieci CBMS.
Dziala na Pythonie 3.9+ (venv AIONS ma 3.11.9).

CLI
    python refgraph.py --stats
    python refgraph.py --at-risk          # chunki aktywne cytujace zaparkowane <-- to jest realny problem
    python refgraph.py --who-refs KCBMSPIPE001
    python refgraph.py --resolve "server/crla_core.py"
    python refgraph.py --unresolved
    python refgraph.py --strict            # zachowanie v1, do porownania
    python refgraph.py --build-index memory/refgraph_index.json

MODUL
    from refgraph import SoftGraph
    g = SoftGraph.build(CHUNKS, quarantine=QUAR, manifest=MAN, project_root=ROOT)
    for ref in g.who_references("KCBMSPIPE001"):
        print(ref.source, ref.resolver, ref.confidence)
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict

BASE = r"E:\server wiedzy\aions_core\memory"
DEF_CHUNKS = os.path.join(BASE, "chunks")
DEF_QUAR = os.path.join(BASE, "chunks_quarantine")
DEF_MANIFEST = os.path.join(BASE, "knowledge_manifest.json")

ID_RE = re.compile(r"^K[A-Z0-9_]{3,}$", re.IGNORECASE)
TOKEN_RE = re.compile(r"[a-z0-9_]{3,}")
STOP = {"the", "and", "for", "with", "from", "this", "that", "chunks", "based",
        "knowledge", "jest", "sie", "nie", "oraz", "przez", "ktore", "dla"}


def tokens(text: str, limit: int = 400) -> set:
    return {t for t in TOKEN_RE.findall((text or "")[:limit].lower()) if t not in STOP}


def is_id_like(value: str) -> bool:
    v = (value or "").strip()
    if not v or "/" in v or "\\" in v:
        return False
    if v.lower().endswith((".py", ".md", ".json", ".jsonl", ".txt", ".yml", ".yaml")):
        return False
    return bool(ID_RE.match(v))


class SoftRef:
    """Jedna krawedz. Zawsze zachowuje oryginal, niezaleznie od tego, czy sie rozstrzygnela."""

    __slots__ = ("source", "raw", "target", "kind", "resolver", "confidence", "note")

    def __init__(self, source, raw, target=None, kind="unknown",
                 resolver="unresolved", confidence=0.0, note=""):
        self.source = source
        self.raw = raw
        self.target = target
        self.kind = kind
        self.resolver = resolver
        self.confidence = confidence
        self.note = note

    @property
    def alive(self) -> bool:
        return self.confidence > 0.0

    def as_dict(self) -> dict:
        return {"source": self.source, "raw": self.raw, "target": self.target,
                "kind": self.kind, "resolver": self.resolver,
                "confidence": round(self.confidence, 2), "note": self.note}

    def __repr__(self):
        return f"<{self.source} -> {self.target or self.raw} [{self.resolver} {self.confidence:.2f}]>"


class SoftGraph:
    def __init__(self):
        self.active = {}        # id -> metadane chunka aktywnego
        self.parked = {}        # id -> metadane chunka z kwarantanny
        self.manifest_ids = set()
        self.concepts = defaultdict(set)     # concept -> {id}
        self.norm_index = {}                 # znormalizowane id -> id
        self.file_index = defaultdict(set)   # basename -> {sciezka wzgledna}
        self.edges = []                      # list[SoftRef]
        self.out = defaultdict(list)         # id -> [SoftRef]
        self.inc = defaultdict(list)         # id -> [SoftRef]
        self.dirs = {}
        self.strict = False

    # ------------------------------------------------------------------ build

    @classmethod
    def build(cls, chunks, quarantine=None, manifest=None,
              project_root=None, strict=False):
        g = cls()
        g.strict = strict
        g.dirs = {"chunks": chunks, "quarantine": quarantine,
                  "manifest": manifest, "project_root": project_root}

        g.active = g._load_dir(chunks)
        if quarantine and os.path.isdir(quarantine) and not strict:
            g.parked = g._load_dir(quarantine)

        if manifest and os.path.isfile(manifest) and not strict:
            try:
                with open(manifest, encoding="utf-8") as fh:
                    man = json.load(fh)
                g.manifest_ids = set((man.get("chunk_index") or {}).keys())
            except (OSError, json.JSONDecodeError):
                pass

        for cid, meta in g.active.items():
            g.concepts[str(meta.get("concept") or "")].add(cid)
            g.norm_index[cls._norm(cid)] = cid
        for cid in g.parked:
            g.norm_index.setdefault(cls._norm(cid), cid)

        if project_root and os.path.isdir(project_root) and not strict:
            g._index_files(project_root)

        for cid, meta in g.active.items():
            for raw in meta.get("_refs", []):
                ref = g._resolve(cid, raw)
                g.edges.append(ref)
                g.out[cid].append(ref)
                if ref.target:
                    g.inc[ref.target].append(ref)
        return g

    @staticmethod
    def _norm(value: str) -> str:
        return re.sub(r"[^a-z0-9]", "", (value or "").lower())

    def _load_dir(self, path):
        store = {}
        if not path or not os.path.isdir(path):
            return store
        for fp in sorted(glob.glob(os.path.join(path, "*.json"))):
            try:
                with open(fp, encoding="utf-8") as fh:
                    d = json.load(fh)
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(d, dict):
                continue
            cid = str(d.get("id") or os.path.splitext(os.path.basename(fp))[0])
            refs = d.get("references")
            store[cid] = {
                "id": cid,
                "concept": d.get("concept"),
                "path": fp,
                "_refs": [r for r in refs if isinstance(r, str) and r.strip()]
                         if isinstance(refs, list) else [],
                "_tok": tokens((str(d.get("concept") or "") + " " + str(d.get("content") or ""))),
            }
        return store

    def _index_files(self, root, max_files=8000):
        n = 0
        skip = {".git", "__pycache__", "venv", "node_modules", "chunks",
                "chunks_quarantine", ".mypy_cache"}
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in skip]
            for fn in filenames:
                rel = os.path.relpath(os.path.join(dirpath, fn), root).replace("\\", "/")
                self.file_index[fn.lower()].add(rel)
                n += 1
                if n >= max_files:
                    return

    # --------------------------------------------------------------- resolvers

    def _resolve(self, source, raw):
        r = raw.strip()

        if is_id_like(r):
            if r in self.active:
                return SoftRef(source, raw, r, "chunk", "exact", 1.00)
            if self.strict:
                return SoftRef(source, raw, None, "chunk", "unresolved", 0.0,
                               "tryb strict: brak w aktywnym store")
            if r in self.manifest_ids:
                return SoftRef(source, raw, r, "chunk", "manifest", 0.95,
                               "w manifescie, brak pliku w chunks/")
            if r in self.parked:
                return SoftRef(source, raw, r, "chunk", "parked", 0.80,
                               "cel w chunks_quarantine — krawedz zyje, wezel zaparkowany")
            hit = self.norm_index.get(self._norm(r))
            if hit:
                return SoftRef(source, raw, hit, "chunk", "normalized", 0.75,
                               f"dopasowano po normalizacji do {hit}")
            return self._semantic(source, raw, r)

        if not self.strict:
            base = os.path.basename(r.replace("\\", "/")).lower()
            cands = self.file_index.get(base)
            if cands:
                exact = {c for c in cands if c.lower().endswith(r.replace("\\", "/").lower())}
                pick = sorted(exact or cands)[0]
                conf = 0.70 if exact else 0.55
                return SoftRef(source, raw, pick, "file", "file", conf,
                               f"{len(cands)} kandydat(ow) po nazwie pliku")

        if r in self.concepts and self.concepts[r]:
            targets = sorted(self.concepts[r])
            return SoftRef(source, raw, targets[0], "concept", "concept", 0.60,
                           f"koncept obejmuje {len(targets)} chunk(ow)")

        if self.strict:
            return SoftRef(source, raw, None, "file", "unresolved", 0.0, "tryb strict")
        return self._semantic(source, raw, r)

    def _semantic(self, source, raw, needle):
        """Ostatnia deska: pokrycie tokenow. Deterministyczne, bez zaleznosci."""
        want = tokens(needle.replace("_", " ").replace("-", " "), 200)
        if not want:
            return SoftRef(source, raw, None, "unknown", "unresolved", 0.0, "brak tokenow")
        best, score = None, 0.0
        for cid, meta in self.active.items():
            if cid == source:
                continue
            have = meta.get("_tok") or set()
            if not have:
                continue
            j = len(want & have) / float(len(want))
            if j > score:
                best, score = cid, j
        if best and score >= 0.34:
            conf = min(0.55, 0.30 + score * 0.25)
            return SoftRef(source, raw, best, "semantic", "semantic", conf,
                           f"pokrycie tokenow {score:.0%}")
        return SoftRef(source, raw, None, "unknown", "unresolved", 0.0,
                       "brak dopasowania powyzej progu")

    # ----------------------------------------------------------------- queries

    def who_references(self, cid, min_conf=0.0):
        return sorted([r for r in self.inc.get(cid, []) if r.confidence >= min_conf],
                      key=lambda r: -r.confidence)

    def references_of(self, cid, min_conf=0.0):
        return sorted([r for r in self.out.get(cid, []) if r.confidence >= min_conf],
                      key=lambda r: -r.confidence)

    def at_risk(self):
        """Aktywne chunki cytujace zaparkowane. TO jest realny dlug, nie 'martwe krawedzie'."""
        out = defaultdict(list)
        for r in self.edges:
            if r.resolver == "parked":
                out[r.source].append(r.target)
        return {k: sorted(v) for k, v in sorted(out.items(), key=lambda kv: -len(kv[1]))}

    def unresolved(self):
        return [r for r in self.edges if not r.alive]

    def orphans(self, min_conf=0.5):
        return sorted(c for c in self.active
                      if not any(r.confidence >= min_conf for r in self.inc.get(c, [])))

    def hubs(self, top=15, min_conf=0.5):
        scored = [(c, sum(1 for r in self.inc.get(c, []) if r.confidence >= min_conf))
                  for c in self.active]
        scored = [s for s in scored if s[1] > 0]
        scored.sort(key=lambda x: (-x[1], x[0]))
        return [(c, n, self.active[c].get("concept")) for c, n in scored[:top]]

    def stats(self):
        by_resolver = Counter(r.resolver for r in self.edges)
        alive = sum(1 for r in self.edges if r.alive)
        total = len(self.edges) or 1
        ar = self.at_risk()
        return {
            "mode": "strict" if self.strict else "soft",
            "active_chunks": len(self.active),
            "parked_chunks": len(self.parked),
            "manifest_entries": len(self.manifest_ids),
            "edges_total": len(self.edges),
            "edges_resolved": alive,
            "pct_resolved": round(100.0 * alive / total, 1),
            "mean_confidence": round(sum(r.confidence for r in self.edges) / total, 3),
            "by_resolver": dict(by_resolver.most_common()),
            "at_risk_chunks": len(ar),
            "at_risk_edges": sum(len(v) for v in ar.values()),
            "orphans_conf50": len(self.orphans()),
        }

    def to_index(self):
        return {"dirs": self.dirs, "stats": self.stats(),
                "edges": [r.as_dict() for r in self.edges]}

    def save_index(self, path):
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self.to_index(), fh, ensure_ascii=False, indent=2)
        with open(tmp, encoding="utf-8") as fh:
            json.load(fh)
        os.replace(tmp, path)
        return path


def main(argv=None):
    ap = argparse.ArgumentParser(description="Miekki graf referencji CBMS")
    ap.add_argument("--chunks", default=DEF_CHUNKS)
    ap.add_argument("--quarantine", default=DEF_QUAR)
    ap.add_argument("--manifest", default=DEF_MANIFEST)
    ap.add_argument("--project-root", default=None)
    ap.add_argument("--strict", action="store_true", help="wylacz miekkie resolvery (zachowanie v1)")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--at-risk", action="store_true")
    ap.add_argument("--who-refs", metavar="ID")
    ap.add_argument("--refs-of", metavar="ID")
    ap.add_argument("--resolve", metavar="RAW")
    ap.add_argument("--unresolved", action="store_true")
    ap.add_argument("--orphans", action="store_true")
    ap.add_argument("--hubs", type=int, metavar="N")
    ap.add_argument("--build-index", metavar="PATH")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--max-items", type=int, default=15)
    a = ap.parse_args(argv)

    if not os.path.isdir(a.chunks):
        print("BLAD: brak katalogu " + a.chunks, file=sys.stderr)
        return 2

    root = a.project_root or os.path.dirname(os.path.dirname(os.path.abspath(a.chunks)))
    g = SoftGraph.build(a.chunks, a.quarantine, a.manifest, root, strict=a.strict)

    picked = any([a.at_risk, a.who_refs, a.refs_of, a.resolve, a.unresolved,
                  a.orphans, a.hubs, a.build_index])
    out = {}
    if a.stats or not picked:
        out["stats"] = g.stats()
    if a.at_risk:
        out["at_risk"] = g.at_risk()
    if a.who_refs:
        out["who_references"] = [r.as_dict() for r in g.who_references(a.who_refs)]
    if a.refs_of:
        out["references_of"] = [r.as_dict() for r in g.references_of(a.refs_of)]
    if a.resolve:
        out["resolve"] = g._resolve("(cli)", a.resolve).as_dict()
    if a.unresolved:
        out["unresolved"] = [r.as_dict() for r in g.unresolved()]
    if a.orphans:
        out["orphans"] = g.orphans()
    if a.hubs:
        out["hubs"] = [{"id": i, "incoming": n, "concept": c} for i, n, c in g.hubs(a.hubs)]
    if a.build_index:
        out["index_written"] = g.save_index(a.build_index)

    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    for section, payload in out.items():
        print("== " + section.upper() + " ==")
        if isinstance(payload, dict):
            for k, v in list(payload.items())[:a.max_items * 3]:
                print("  %-22s %s" % (k, v))
            if len(payload) > a.max_items * 3:
                print("  ... i %d wiecej" % (len(payload) - a.max_items * 3))
        elif isinstance(payload, list):
            for item in payload[:a.max_items]:
                print("  " + str(item))
            if len(payload) > a.max_items:
                print("  ... i %d wiecej" % (len(payload) - a.max_items))
        else:
            print("  " + str(payload))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
