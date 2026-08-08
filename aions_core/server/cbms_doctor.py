"""
cbms_doctor.py — diagnostyka spójności magazynu chunków CBMS.

Leaf node, TYLKO ODCZYT. Nic nie zapisuje, nic nie kasuje, nie dotyka
cbms_memory.py ani serwera. Tylko stdlib.

Wzorzec zapożyczony z Sereny (`get_diagnostics_for_file`) — tam LSP raportuje
niespójności w kodzie. Tutaj raportujemy niespójności w pamięci.

Powód istnienia: `_should_create_new_chunk()` dopisuje chunki automatycznie, a chunk
zapisany ze słabej odpowiedzi staje się evidence dla przyszłych odpowiedzi. Przy 167
chunkach to niewidoczne, przy 5000 zacznie dryfować. To narzędzie zamienia
"trzeba uważać" na "mam liczbę".

Użycie:
    python cbms_doctor.py
    python cbms_doctor.py --chunks "E:/server wiedzy/aions_core/memory/chunks"
    python cbms_doctor.py --json
    python cbms_doctor.py --fail-on-critical      # kod wyjscia 1 gdy sa bledy krytyczne

Kody wyjscia: 0 = czysto lub tylko ostrzezenia, 1 = bledy krytyczne (z --fail-on-critical),
2 = zly katalog.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

DEFAULT_CHUNKS = r"E:\server wiedzy\aions_core\memory\chunks"

# Pola, ktore chunk powinien miec zawsze. Ustalone z pomiaru na zywym store,
# nie wymyslone: id/concept/content/created wystepuja w 167/167.
CORE_FIELDS = ("id", "concept", "content", "created")
EXPECTED_FIELDS = CORE_FIELDS + ("size", "references", "access_count", "last_accessed")

SEV_CRITICAL = "CRITICAL"
SEV_WARN = "WARN"
SEV_INFO = "INFO"


class Finding:
    __slots__ = ("severity", "code", "message", "items")

    def __init__(self, severity: str, code: str, message: str, items: list | None = None):
        self.severity = severity
        self.code = code
        self.message = message
        self.items = items or []

    def as_dict(self) -> dict:
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "count": len(self.items),
            "items": self.items[:50],
            "truncated": max(0, len(self.items) - 50),
        }


def load_chunks(chunks_dir: str) -> tuple[dict[str, dict], list[tuple[str, str]]]:
    """Zwraca (chunki wg id, lista (sciezka, blad))."""
    chunks: dict[str, dict] = {}
    broken: list[tuple[str, str]] = []
    for path in sorted(glob.glob(os.path.join(chunks_dir, "*.json"))):
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except json.JSONDecodeError as exc:
            broken.append((path, f"niepoprawny JSON: {exc}"))
            continue
        except OSError as exc:
            broken.append((path, f"blad odczytu: {exc}"))
            continue
        if not isinstance(data, dict):
            broken.append((path, "korzen nie jest obiektem JSON"))
            continue
        stem = os.path.splitext(os.path.basename(path))[0]
        cid = str(data.get("id") or stem)
        if cid in chunks:
            broken.append((path, f"zduplikowane id: {cid}"))
            continue
        data["_path"] = path
        data["_stem"] = stem
        chunks[cid] = data
    return chunks, broken


def looks_like_chunk_id(value: str) -> bool:
    v = value.strip()
    if not v or "/" in v or "\\" in v or v.lower().endswith((".py", ".md", ".json", ".jsonl")):
        return False
    return v.upper().startswith("K") and len(v) >= 4


def diagnose(chunks_dir: str, root_hint: str | None = None) -> tuple[list[Finding], dict]:
    chunks, broken = load_chunks(chunks_dir)
    findings: list[Finding] = []
    total = len(chunks)

    if total == 0:
        findings.append(Finding(SEV_CRITICAL, "EMPTY_STORE",
                                f"Brak chunkow w {chunks_dir}"))
        return findings, {"chunks": 0}

    # --- 1. Pliki nieczytelne ---
    if broken:
        findings.append(Finding(SEV_CRITICAL, "UNREADABLE",
                                "Pliki nieczytelne lub zduplikowane id",
                                [f"{os.path.basename(p)} :: {e}" for p, e in broken]))

    # --- 2. Brakujace pola rdzeniowe ---
    missing_core: list[str] = []
    for cid, d in chunks.items():
        gaps = [f for f in CORE_FIELDS if f not in d]
        if gaps:
            missing_core.append(f"{cid}: brak {', '.join(gaps)}")
    if missing_core:
        findings.append(Finding(SEV_CRITICAL, "MISSING_CORE_FIELDS",
                                "Chunki bez pol rdzeniowych", missing_core))

    # --- 3. id != nazwa pliku ---
    mismatched = [f"{cid} w pliku {d['_stem']}.json"
                  for cid, d in chunks.items() if cid != d["_stem"]]
    if mismatched:
        findings.append(Finding(SEV_WARN, "ID_FILENAME_MISMATCH",
                                "Pole id nie zgadza sie z nazwa pliku", mismatched))

    # --- 4. Pusta lub podejrzanie krotka tresc ---
    empty, tiny = [], []
    for cid, d in chunks.items():
        content = d.get("content")
        if not isinstance(content, str) or not content.strip():
            empty.append(cid)
        elif len(content.strip()) < 80:
            tiny.append(f"{cid} ({len(content.strip())} zn.)")
    if empty:
        findings.append(Finding(SEV_CRITICAL, "EMPTY_CONTENT",
                                "Chunki z pusta trescia — beda cytowane jako evidence bez tresci", empty))
    if tiny:
        findings.append(Finding(SEV_WARN, "TINY_CONTENT",
                                "Chunki ponizej 80 znakow — sprawdz czy niosa wiedze", tiny))

    # --- 5. Deklarowany size vs rzeczywistosc ---
    size_drift = []
    for cid, d in chunks.items():
        declared = d.get("size")
        content = d.get("content")
        if isinstance(declared, int) and isinstance(content, str):
            actual = len(content)
            if declared and abs(declared - actual) > max(50, 0.2 * actual):
                size_drift.append(f"{cid}: deklarowane {declared}, rzeczywiste {actual}")
    if size_drift:
        findings.append(Finding(SEV_WARN, "SIZE_DRIFT",
                                "Pole size rozjechalo sie z dlugoscia content", size_drift))

    # --- 6. Martwe krawedzie: referencje do nieistniejacych chunkow ---
    dangling: list[str] = []
    file_refs: dict[str, set[str]] = defaultdict(set)
    reverse: dict[str, set[str]] = defaultdict(set)
    for cid, d in chunks.items():
        refs = d.get("references")
        if not isinstance(refs, list):
            continue
        for raw in refs:
            if not isinstance(raw, str) or not raw.strip():
                continue
            ref = raw.strip()
            if looks_like_chunk_id(ref):
                reverse[ref].add(cid)
                if ref not in chunks:
                    dangling.append(f"{cid} -> {ref}")
            else:
                file_refs[cid].add(ref)
    if dangling:
        findings.append(Finding(SEV_CRITICAL, "DANGLING_REFS",
                                "Referencje do chunkow, ktore nie istnieja", dangling))

    # --- 7. Referencje do plikow, ktorych nie ma na dysku ---
    if root_hint and os.path.isdir(root_hint):
        missing_files: list[str] = []
        for cid, refs in file_refs.items():
            for ref in refs:
                if "${" in ref or ref.startswith(("http://", "https://")):
                    continue  # placeholder albo URL — nie sprawdzamy
                cand = os.path.join(root_hint, ref.replace("/", os.sep))
                if not os.path.exists(cand):
                    missing_files.append(f"{cid} -> {ref}")
        if missing_files:
            findings.append(Finding(SEV_WARN, "MISSING_FILE_REFS",
                                    f"Referencje do plikow nieobecnych w {root_hint}", missing_files))

    # --- 8. Sieroty: nikt na nie nie wskazuje ---
    orphans = sorted(cid for cid in chunks if cid not in reverse)
    if orphans:
        sev = SEV_WARN if len(orphans) < 0.8 * total else SEV_INFO
        findings.append(Finding(sev, "ORPHANS",
                                "Chunki bez cytowan przychodzacych — do przegladu, NIE do kasowania",
                                orphans))

    # --- 9. Zdrowie licznikow dostepu ---
    zero_access = [cid for cid, d in chunks.items() if not d.get("access_count")]
    if len(zero_access) == total:
        findings.append(Finding(SEV_CRITICAL, "ACCESS_TRACKING_DEAD",
                                "ZADEN chunk nie ma access_count > 0. Sygnal 'co jest uzywane' "
                                "nie dziala — albo ten katalog nie jest zywym store, albo licznik "
                                "nie jest persystowany."))
    elif zero_access:
        findings.append(Finding(SEV_INFO, "NEVER_ACCESSED",
                                "Chunki nigdy nieodczytane", zero_access))

    # --- 10. Duplikaty konceptu ---
    by_concept = Counter(str(d.get("concept")) for d in chunks.values())
    dupes = [f"{c}: {n} chunkow" for c, n in by_concept.most_common() if n > 3]
    if dupes:
        findings.append(Finding(SEV_INFO, "CONCEPT_CLUSTERS",
                                "Koncepty z wieloma chunkami — kandydaci do konsolidacji", dupes))

    # --- 11. Dryf schematu ---
    field_counts = Counter()
    for d in chunks.values():
        for k in d:
            if not k.startswith("_"):
                field_counts[k] += 1
    rare = [f"{k} (w {n}/{total})" for k, n in field_counts.items()
            if n <= max(2, 0.05 * total) and k not in EXPECTED_FIELDS]
    if rare:
        findings.append(Finding(SEV_INFO, "SCHEMA_DRIFT",
                                "Pola wystepujace w pojedynczych chunkach — eksperymenty w produkcji",
                                rare))

    # --- 12. Brak proweniencji ---
    no_prov = [cid for cid, d in chunks.items()
               if not any(k in d for k in ("source", "provenance", "derived_from", "author"))]
    if no_prov:
        findings.append(Finding(SEV_WARN, "NO_PROVENANCE",
                                "Chunki bez informacji o pochodzeniu. Przy kaskadzie do chmury "
                                "nie odroznisz odpowiedzi modelu od wiedzy zweryfikowanej.",
                                no_prov))

    summary = {
        "chunks_dir": chunks_dir,
        "scanned_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "chunks": total,
        "unreadable": len(broken),
        "chunk_to_chunk_edges": sum(len(v) for v in reverse.values()),
        "chunk_to_file_edges": sum(len(v) for v in file_refs.values()),
        "orphans": len(orphans),
        "dangling": len(dangling),
        "distinct_concepts": len(by_concept),
        "critical": sum(1 for f in findings if f.severity == SEV_CRITICAL),
        "warnings": sum(1 for f in findings if f.severity == SEV_WARN),
        "info": sum(1 for f in findings if f.severity == SEV_INFO),
    }
    return findings, summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Diagnostyka magazynu chunkow CBMS (tylko odczyt)")
    ap.add_argument("--chunks", default=DEFAULT_CHUNKS)
    ap.add_argument("--root", default=None,
                    help="korzen projektu do weryfikacji referencji plikowych")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fail-on-critical", action="store_true")
    ap.add_argument("--max-items", type=int, default=15)
    args = ap.parse_args(argv)

    if not os.path.isdir(args.chunks):
        print(f"BLAD: katalog nie istnieje: {args.chunks}", file=sys.stderr)
        return 2

    root = args.root
    if root is None:
        # memory/chunks -> korzen projektu dwa poziomy wyzej
        root = os.path.dirname(os.path.dirname(os.path.abspath(args.chunks)))

    findings, summary = diagnose(args.chunks, root)

    if args.json:
        print(json.dumps({"summary": summary,
                          "findings": [f.as_dict() for f in findings]},
                         ensure_ascii=False, indent=2))
    else:
        print("=" * 72)
        print("CBMS DOCTOR")
        print("=" * 72)
        for k, v in summary.items():
            print(f"  {k:24s} {v}")
        print()
        order = {SEV_CRITICAL: 0, SEV_WARN: 1, SEV_INFO: 2}
        for f in sorted(findings, key=lambda x: order[x.severity]):
            print(f"[{f.severity}] {f.code} ({len(f.items)})")
            print(f"    {f.message}")
            for item in f.items[:args.max_items]:
                print(f"      - {item}")
            if len(f.items) > args.max_items:
                print(f"      ... i {len(f.items) - args.max_items} wiecej")
            print()
        if not findings:
            print("Czysto. Brak zastrzezen.\n")

    if args.fail_on_critical and summary.get("critical"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
