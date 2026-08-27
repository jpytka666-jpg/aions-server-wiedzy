#!/usr/bin/env python3
# ==========================================
# AUTHOR: M. SZUL
# AI MODEL: Claude Opus 5
# TIMESTAMP: 2026-08-27 03:35:20
# REASON FOR CREATION: The observer records what Claude DOES - which command ran, what it
#   returned. It records nothing of what was WORKED OUT: the correction, the reason a
#   direction was abandoned, the number that settled an argument. That knowledge existed
#   only in a conversation and was gone when the conversation ended. This writes it into
#   the same store, in the same alphabet, addressed the same way as everything else.
# MECHANICS: Text in, one block out. The block carries four things and each has a job.
#   The Hangul address says WHICH block, and is on the surface so a scan never opens the
#   file. `cbms_codes` says WHAT IT IS ABOUT, rarest symbol first, and is what the
#   symbolic index searches. `cbms_packed` is the text through the shared code book -
#   measured 0.65x of the source on a block of this size, 0.49x across the whole store,
#   which is worse than gzip and not the point: it is the form Noworodek reads, so a
#   block written here is material the learner can take without conversion. `content`
#   stays plain, because a memory that can only be read by the thing that wrote it is not
#   a memory.
# SYSTEM PART: AIONS memory - writing side.
# ARCHITECTURE FUNCTION: Closes the loop that made the store one-directional. Until now
#   the store was read by retrieval and written only by AIONS itself; conversation with
#   Claude produced nothing that survived.
# DEPENDENCIES/LINKS: hangul_addressing.make_hangul_code for the address; the shared code
#   book via cbms_shared_index; the cbms binary for packing; writes into memory/chunks.
# TECH STACK: Python 3, standard library. The store is Python and its blocks are JSON;
#   anything else would need a second definition of what a block is.
# LOCAL WORKSPACE: E:\server wiedzy\aions_core\server\write_knowledge_block.py
# GIT COMMIT: PENDING
# GITHUB METADATA: jpytka666-jpg/aions-server-wiedzy, branch main
# ==========================================
"""Zapisuje ustalenie z rozmowy jako blok pamieci - adres KR, znaki CBMS, tresc."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cbms_shared_index import DEFAULT_BOOK, load_book, symbols_of  # noqa: E402

MEMORY = Path(os.environ.get("AIONS_MEMORY") or Path(__file__).resolve().parent.parent / "memory")
CHUNKS = MEMORY / "chunks"
CBMS_BIN = Path(os.environ.get("AIONS_CBMS_BIN") or
                r"C:/temp/aions-cbms-2026-08-26/target/release/cbms.exe")

# Below this there is no knowledge, only a note. The lesson gate one level down refuses
# for the same reason: a store that accepts everything fills with its own echo, which is
# how 455 blocks ended up quarantined once already.
MIN_CHARS = 120


def hangul_address(data: str) -> str:
    """The same addressing AIONS already uses, imported rather than reimplemented so the
    two can never drift into disagreeing about what a block is called."""
    try:
        from hangul_addressing import make_hangul_code  # type: ignore
        return make_hangul_code(data)
    except Exception:
        base = ord("가")
        h = hashlib.sha1(data.encode("utf-8")).hexdigest()[:23]
        return "".join(chr(base + int(c, 16) * 32) for c in h)


def store_frequency() -> dict:
    """How many blocks each symbol appears in, across the whole store.

    Read from what the blocks already carry rather than re-encoding them, so this costs
    one pass over small JSON files. A block written before this existed simply does not
    contribute, which understates a symbol's spread and can only make it look rarer -
    the safe direction, since the worst outcome is an unremarkable word leading the list.
    """
    seen: Counter = Counter()
    try:
        for f in CHUNKS.glob("*.json"):
            try:
                codes = json.loads(f.read_text(encoding="utf-8")).get("cbms_codes")
            except Exception:
                continue
            if isinstance(codes, list):
                for c in set(codes):
                    seen[c] += 1
    except Exception:
        pass
    return seen


def grow_book(text: str, book_path: Path, max_new: int = 400) -> int:
    """Add this text's unknown words to the shared book. Returns how many were added.

    Capped: one block should not be able to mint hundreds of entries from a typo storm,
    and the words that matter are the ones that repeat. Failure is not fatal - the block
    is still written, just in the vocabulary the book already had.
    """
    if not CBMS_BIN.exists() or not book_path.exists():
        return 0
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "corpus.txt"
        src.write_text(text, encoding="utf-8")
        r = subprocess.run(
            [str(CBMS_BIN), str(book_path), "grow", str(src), str(max_new), "1"],
            capture_output=True, text=True, encoding="utf-8", timeout=300)
        if r.returncode != 0:
            return 0
        for line in (r.stdout or "").splitlines():
            if line.startswith("dopisano"):
                try:
                    return int(line.split(":")[1].split()[0])
                except Exception:
                    return 0
    return 0


def pack(text: str, book_path: Path) -> str | None:
    """Text through the shared code book. Returns None rather than a broken block if the
    binary is absent or refuses - a block claiming to hold CBMS that does not is worse
    than one that says it holds none."""
    if not CBMS_BIN.exists():
        return None
    with tempfile.TemporaryDirectory() as tmp:
        src, out = Path(tmp) / "b.txt", Path(tmp) / "b.cbms"
        src.write_text(text, encoding="utf-8")
        r = subprocess.run([str(CBMS_BIN), str(book_path), "write", str(src), str(out)],
                           capture_output=True, text=True, encoding="utf-8", timeout=120)
        if r.returncode != 0 or not out.exists():
            return None
        return base64.b64encode(out.read_bytes()).decode("ascii")


def write_block(text: str, concept: str, source: str = "rozmowa",
                book_path: Path | None = None) -> dict:
    text = text.strip()
    if len(text) < MIN_CHARS:
        raise ValueError(f"za krotkie: {len(text)} znakow, minimum {MIN_CHARS}")

    book_path = Path(book_path or os.environ.get("AIONS_CBMS_BOOK") or DEFAULT_BOOK)

    # Teach the book this block's words BEFORE encoding it.
    #
    # Without this a block is written in whatever vocabulary the book happens to hold, and
    # everything else is spelled out letter by letter. Measured on a 273-character note:
    # the book knew 15 of its 42 words - the glue (`za`, `jest`, `w`) and none of the
    # content - and the packed form came out at 312 bytes, LARGER than the source. A block
    # from the store, whose words the book already had, encodes 37 characters into 6
    # symbols.
    #
    # `grow` only ever appends and refuses anything that would renumber or break the round
    # trip, so this cannot invalidate a block already written or a checkpoint already
    # trained. The store and the book learn the same words at the same time, which is the
    # whole reason they share one.
    grow_book(text, book_path)
    book = load_book(book_path)

    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()
    chunk_id = "K" + digest[:12].upper()

    CHUNKS.mkdir(parents=True, exist_ok=True)
    target = CHUNKS / f"{chunk_id}.json"
    if target.exists():
        # Same text, same id. Saying so is more useful than writing it twice.
        return {"id": chunk_id, "nowy": False, "plik": str(target)}

    syms = symbols_of(text, book)
    # Rarest ACROSS THE STORE first, so reading the opening codes tells you what the block
    # is about.
    #
    # Ordering by count within the block does not work and the reason is worth keeping:
    # inside one block almost every word occurs exactly once, so the sort collapses to
    # alphabetical and the glue leads. Asked what a block said, it answered
    # "i ma a jak model dostaje bok" - the four commonest words in Polish first, and
    # nothing about its subject. A word in three blocks of a hundred says where to look;
    # a word in ninety says nothing, however often it repeats here.
    across = store_frequency()
    codes = sorted(set(syms), key=lambda s: (across.get(s, 0), s))

    block = {
        "id": chunk_id,
        "concept": concept,
        "content": text,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "size": len(text),
        "references": [],
        "access_count": 0,
        "last_accessed": None,
        "pattern_type": "ustalenie",
        "zrodlo": source,
        "hangul_code": hangul_address(chunk_id),
        "cbms_codes": codes,
        "cbms_book": None,
        "cbms_packed": pack(text, book_path),
    }

    mark = subprocess.run([str(CBMS_BIN), str(book_path), "mark"],
                          capture_output=True, text=True, encoding="utf-8", timeout=120)
    if mark.returncode == 0:
        got = {}
        for line in mark.stdout.splitlines():
            if line.startswith("wpisow"):
                got["wpisow"] = int(line.split(":")[1])
            elif line.startswith("znak"):
                got["znak"] = line.split(":")[1].strip()
        block["cbms_book"] = got or None

    tmp = target.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(block, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(target)
    return {"id": chunk_id, "nowy": True, "plik": str(target),
            "znakow": len(text), "kodow": len(codes),
            "spakowane": len(block["cbms_packed"] or "")}


def main() -> int:
    if len(sys.argv) < 2:
        print("write_knowledge_block.py <pojecie> [plik]   (bez pliku czyta wejscie)")
        return 2
    concept = sys.argv[1]
    text = Path(sys.argv[2]).read_text(encoding="utf-8") if len(sys.argv) > 2 else sys.stdin.read()
    try:
        out = write_block(text, concept)
    except ValueError as exc:
        print(f"nie zapisano: {exc}")
        return 1
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
