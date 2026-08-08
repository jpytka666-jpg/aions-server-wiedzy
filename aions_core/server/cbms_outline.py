"""
cbms_outline.py — progresywne ujawnianie tresci dla CBMS.

To jest brakujaca polowa mechaniki Sereny. `refgraph.py` przeniosl nawigacje po
krawedziach (find_referencing_symbols). Ten plik przenosi to, co daje realna
oszczednosc kontekstu: get_symbols_overview + find_symbol(include_body=True).

ZASADA
    Nie zwracaj tresci, dopoki nie wiadomo, ktora tresc jest potrzebna.

    Krok 1  OUTLINE  — szkielet N chunkow: id, concept, tier, rozmiar, stopien
                       wejsciowy, jedna linia streszczenia. Bez cial.
    Krok 2  DRILL    — pelna tresc 1-2 chunkow, ktore wybrales po szkielecie.

    Koszt kroku 1 rosnie z LICZBA chunkow, nie z ich objetoscia. Na zywym store:
    167 chunkow w outline ~ 12 KB. Te same 167 z trescia ~ 210 KB. Rzad wielkosci.

BUDZET
    --budget N przycina outline tak, zeby zmiescil sie w N znakach, sortujac po
    trafnosci. Pomyslane pod `aions-mouth` (num_ctx 4096) — tam nie ma miejsca na
    "5-7 chunkow z pelna trescia", jest miejsce na szkielet i jeden drill.

TIERY
    active     memory/chunks              — normalny store
    parked     memory/chunks_quarantine   — zaparkowane, NIE skasowane
    Outline pokazuje oba i oznacza tier. Zaparkowany chunk widoczny w szkielecie
    kosztuje tyle co linijka, a bez tego nie wiesz, ze wiedza istnieje.

Zero zaleznosci poza stdlib. Nie importuje AIONS. Tylko odczyt.

CLI
    python cbms_outline.py --outline
    python cbms_outline.py --outline --search "crla turniej" --budget 2000
    python cbms_outline.py --outline --concept crla_pattern
    python cbms_outline.py --drill KCBMSPIPE001
    python cbms_outline.py --drill KCBMSPIPE001 KGUARD001 --json
    python cbms_outline.py --compare          # ile bys zaoszczedzil

MODUL
    from cbms_outline import Store
    s = Store.load()
    s.outline(search="crla", budget=2000)   -> list[dict]  (bez tresci)
    s.drill(["KCBMSPIPE001"])               -> list[dict]  (z trescia)
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from collections import defaultdict

BASE = r"E:\server wiedzy\aions_core\memory"
DEF_CHUNKS = os.path.join(BASE, "chunks")
DEF_QUAR = os.path.join(BASE, "chunks_quarantine")

ID_RE = re.compile(r"^K[A-Z0-9_]{3,}$", re.IGNORECASE)
TOKEN_RE = re.compile(r"[a-z0-9_]{3,}")
STOP = {"the", "and", "for", "with", "from", "this", "that", "jest", "sie",
        "nie", "oraz", "przez", "ktore", "dla", "jak", "sa", "byc"}


def toks(text: str) -> set:
    return {t for t in TOKEN_RE.findall((text or "").lower()) if t not in STOP}


def is_id_like(v: str) -> bool:
    v = (v or "").strip()
    if not v or "/" in v or "\\" in v:
        return False
    if v.lower().endswith((".py", ".md", ".json", ".jsonl", ".txt")):
        return False
    return bool(ID_RE.match(v))


def summarize(content: str, width: int = 110) -> str:
    """Jedna linia. Pierwsze zdanie albo pierwsza niepusta linia, przyciete."""
    if not isinstance(content, str):
        return ""
    for line in content.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"\s+", " ", line)
        return line[:width] + ("..." if len(line) > width else "")
    return ""


class Store:
    """Magazyn chunkow z dwoma tierami i dwoma trybami odczytu."""

    def __init__(self):
        self.meta: dict[str, dict] = {}      # id -> szkielet (BEZ content)
        self.paths: dict[str, str] = {}      # id -> sciezka na dysku
        self.indeg: dict[str, int] = defaultdict(int)

    # ------------------------------------------------------------- ladowanie

    @classmethod
    def load(cls, chunks: str = DEF_CHUNKS, quarantine: str | None = DEF_QUAR) -> "Store":
        s = cls()
        raw_refs: dict[str, list[str]] = {}
        for tier, path in (("active", chunks), ("parked", quarantine)):
            if not path or not os.path.isdir(path):
                continue
            for fp in sorted(glob.glob(os.path.join(path, "*.json"))):
                try:
                    with open(fp, encoding="utf-8") as fh:
                        d = json.load(fh)
                except (OSError, json.JSONDecodeError):
                    continue
                if not isinstance(d, dict):
                    continue
                cid = str(d.get("id") or os.path.splitext(os.path.basename(fp))[0])
                if cid in s.meta:            # aktywny wygrywa z zaparkowanym
                    continue
                content = d.get("content") if isinstance(d.get("content"), str) else ""
                refs = d.get("references")
                refs = [r for r in refs if isinstance(r, str)] if isinstance(refs, list) else []
                raw_refs[cid] = refs
                s.paths[cid] = fp
                s.meta[cid] = {
                    "id": cid,
                    "tier": tier,
                    "concept": d.get("concept"),
                    "chars": len(content),
                    "n_refs": len(refs),
                    "access_count": d.get("access_count") or 0,
                    "created": d.get("created"),
                    "summary": summarize(content),
                    "_tok": toks((str(d.get("concept") or "")) + " " + content[:600]),
                }
        for cid, refs in raw_refs.items():
            for r in refs:
                if is_id_like(r):
                    s.indeg[r.strip()] += 1
        for cid, m in s.meta.items():
            m["indeg"] = s.indeg.get(cid, 0)
        return s

    # ------------------------------------------------------------ krok 1: szkielet

    def outline(self, search: str | None = None, concept: str | None = None,
                tier: str | None = None, budget: int | None = None,
                limit: int | None = None) -> list[dict]:
        """Szkielet. NIGDY nie zwraca pola content."""
        q = toks(search) if search else set()
        rows = []
        for cid, m in self.meta.items():
            if concept and str(m.get("concept") or "").lower() != concept.lower():
                continue
            if tier and m["tier"] != tier:
                continue
            score = 0.0
            if q:
                hit = q & m["_tok"]
                if not hit:
                    continue
                score = len(hit) / len(q)
            # stopien wejsciowy jako sygnal wagi: chunk cytowany przez wielu jest nosny
            score += min(m["indeg"], 20) * 0.02
            if m["tier"] == "active":
                score += 0.05
            row = {k: v for k, v in m.items() if not k.startswith("_")}
            row["score"] = round(score, 3)
            rows.append(row)

        rows.sort(key=lambda r: (-r["score"], -r["indeg"], r["id"]))
        if limit:
            rows = rows[:limit]
        if budget:
            out, used = [], 0
            for r in rows:
                cost = len(r["id"]) + len(str(r.get("concept") or "")) + len(r["summary"]) + 24
                if used + cost > budget:
                    break
                out.append(r)
                used += cost
            rows = out
        return rows

    # -------------------------------------------------------------- krok 2: drill

    def drill(self, ids: list[str]) -> list[dict]:
        """Pelna tresc, tylko dla wskazanych id. To jedyne miejsce czytajace content."""
        out = []
        for cid in ids:
            path = self.paths.get(cid)
            if not path:
                out.append({"id": cid, "error": "nie znaleziono w zadnym tierze"})
                continue
            try:
                with open(path, encoding="utf-8") as fh:
                    d = json.load(fh)
            except (OSError, json.JSONDecodeError) as exc:
                out.append({"id": cid, "error": f"blad odczytu: {exc}"})
                continue
            d["_tier"] = self.meta[cid]["tier"]
            d["_indeg"] = self.meta[cid]["indeg"]
            d["_path"] = path
            out.append(d)
        return out

    # ------------------------------------------------------------------ pomiar

    def compare(self) -> dict:
        total_content = sum(m["chars"] for m in self.meta.values())
        outline_cost = sum(len(m["id"]) + len(str(m.get("concept") or ""))
                           + len(m["summary"]) + 24 for m in self.meta.values())
        top7 = sorted(self.meta.values(), key=lambda m: -m["indeg"])[:7]
        legacy = sum(m["chars"] for m in top7)
        new = outline_cost + (top7[0]["chars"] if top7 else 0)
        return {
            "chunks": len(self.meta),
            "active": sum(1 for m in self.meta.values() if m["tier"] == "active"),
            "parked": sum(1 for m in self.meta.values() if m["tier"] == "parked"),
            "all_content_chars": total_content,
            "full_outline_chars": outline_cost,
            "outline_vs_full_ratio": round(total_content / outline_cost, 1) if outline_cost else 0,
            "legacy_top7_with_content_chars": legacy,
            "outline_plus_one_drill_chars": new,
            "saving_vs_legacy_pct": round(100 * (1 - new / legacy), 1) if legacy else 0,
        }


def render_outline(rows: list[dict]) -> str:
    if not rows:
        return "  (brak trafien)\n"
    w = max(len(r["id"]) for r in rows)
    lines = []
    for r in rows:
        flag = " " if r["tier"] == "active" else "P"
        lines.append("  %s %-*s  in:%-3d %5dz  %-22s %s" % (
            flag, w, r["id"], r["indeg"], r["chars"],
            str(r.get("concept") or "")[:22], r["summary"][:80]))
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Progresywne ujawnianie tresci CBMS")
    ap.add_argument("--chunks", default=DEF_CHUNKS)
    ap.add_argument("--quarantine", default=DEF_QUAR)
    ap.add_argument("--no-parked", action="store_true", help="pomin kwarantanne")
    ap.add_argument("--outline", action="store_true")
    ap.add_argument("--drill", nargs="+", metavar="ID")
    ap.add_argument("--search", metavar="TEKST")
    ap.add_argument("--concept", metavar="NAZWA")
    ap.add_argument("--tier", choices=["active", "parked"])
    ap.add_argument("--budget", type=int, metavar="ZNAKI")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    if not os.path.isdir(a.chunks):
        print(f"BLAD: brak katalogu {a.chunks}", file=sys.stderr)
        return 2

    s = Store.load(a.chunks, None if a.no_parked else a.quarantine)

    if a.drill:
        res = s.drill(a.drill)
        if a.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            for d in res:
                print("=" * 70)
                if "error" in d:
                    print(f"{d['id']}: {d['error']}")
                    continue
                print(f"{d.get('id')}  [{d.get('_tier')}]  in:{d.get('_indeg')}  "
                      f"concept={d.get('concept')}")
                print("-" * 70)
                print(d.get("content") or "(brak tresci)")
                print()
        return 0

    if a.compare:
        c = s.compare()
        if a.json:
            print(json.dumps(c, ensure_ascii=False, indent=2))
        else:
            print("== OUTLINE vs PELNA TRESC ==")
            for k, v in c.items():
                print(f"  {k:34s} {v}")
        return 0

    rows = s.outline(search=a.search, concept=a.concept, tier=a.tier,
                     budget=a.budget, limit=a.limit)
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print(f"== OUTLINE ({len(rows)} chunkow, P = zaparkowany) ==")
        print(render_outline(rows))
        print("Drill:  python cbms_outline.py --drill <ID>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
