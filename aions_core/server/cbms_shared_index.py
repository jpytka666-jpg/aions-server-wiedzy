#!/usr/bin/env python3
# ==========================================
# AUTHOR: M. SZUL
# AI MODEL: Claude Opus 5
# TIMESTAMP: 2026-08-27 00:45:12
# REASON FOR CREATION: The symbolic layer was pointed at a 16-symbol code book written in
#   October 2025 around one example sentence about buying bread. Measured on the live
#   store: 86 of 167 blocks contained not a single one of its symbols, so no query could
#   ever reach them - and those 86 turned out to be the thinking patterns, the
#   meta-cognitive strategies and the reasoning methodologies. The idea was sound; the
#   dictionary saw an eighth of the memory.
# MECHANICS: Reads the symbols already stored in each block's `cbms_codes` rather than
#   re-encoding every block at startup, so the index loads instead of being rebuilt and
#   survives a restart. Scores by rarity: a symbol in three blocks says far more about a
#   query than one in ninety, which the previous count-the-hits scoring could not express.
#   Queries are split by the same rule the CBMS encoder applies - punctuation peeled off
#   both ends, case folded only where a case mark could put it back.
# SYSTEM PART: AIONS memory - symbolic retrieval.
# ARCHITECTURE FUNCTION: The layer that makes stored blocks findable by meaning without a
#   model, an embedding, or a network call. It shares one code book with Noworodek, so a
#   block written here is material the learner can read directly.
# DEPENDENCIES/LINKS: reads the shared code book produced by cbms-writing (`grow`), and
#   the `cbms_codes` / `cbms_book` fields on stored chunks. Consumed by cbms_memory.
# TECH STACK: Python 3, standard library. Python because this plugs into the existing
#   memory server, which is Python; nothing here is hot enough to need otherwise.
# LOCAL WORKSPACE: E:\server wiedzy\aions_core\server\cbms_shared_index.py
# GIT COMMIT: PENDING
# GITHUB METADATA: local to the AIONS knowledge server
# ==========================================
"""Wyszukiwanie po znakach CBMS, na wspolnej ksiazce kodow."""

from __future__ import annotations

import json
import math
import os
import re
import string
from collections import Counter
from pathlib import Path
from typing import Dict, List, Set, Tuple

# One book, shared with Noworodek. An id or a symbol only means anything relative to it.
DEFAULT_BOOK = Path.home() / "Desktop" / "AIONS-CBMS" / "ksiazka-wspolna.txt"

_UPLUS = re.compile(r"^U\+([0-9A-Fa-f]{4,6})$")
_PUNCT = set(string.punctuation)


def _decode_symbol(sym: str) -> str:
    """The book writes some symbols as glyphs and some as `U+25CB`. Both are the same
    thing, and reading the notation literally makes a six-character 'symbol' that matches
    nothing."""
    m = _UPLUS.match(sym)
    return chr(int(m.group(1), 16)) if m else sym


def load_book(path: Path) -> Dict[str, str]:
    """root -> symbol, exactly as the encoder sees it."""
    book: Dict[str, str] = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#") or "=" not in line:
                continue
            root, sym = line.rstrip("\n").rsplit("=", 1)
            if root and sym:
                book[root] = _decode_symbol(sym)
    return book


def _core(token: str) -> str:
    """Punctuation peeled off both ends - the encoder's definition of a word. Leaving it
    attached is what once made `status:` miss the entry minted for `status`."""
    i, j = 0, len(token)
    while i < j and token[i] in _PUNCT:
        i += 1
    while j > i and token[j - 1] in _PUNCT:
        j -= 1
    return token[i:j]


def _folded(word: str) -> str:
    """Folded only where a case mark could put the capitals back. A mixed shape like
    `AarSvc_6e9d9` is left alone, because the book must hold it verbatim or not at all."""
    if word.islower() or word.isupper() or (word[:1].isupper() and word[1:].islower()):
        return word.lower()
    return word


def located_symbols(text: str, book: Dict[str, str]) -> List[Tuple[str, int]]:
    """Every symbol the text yields, with the offset of the token that produced it.

    Offsets come from walking the tokens, never from searching for the word afterwards.
    `content.find(word)` returns the FIRST occurrence, which is rarely the one that made
    the block rank, and it matches inside longer words - `memory` found inside
    `memorywise`. A token walk cannot do either.
    """
    out: List[Tuple[str, int]] = []
    i, n = 0, len(text)
    while i < n:
        while i < n and text[i].isspace():
            i += 1
        start = i
        while i < n and not text[i].isspace():
            i += 1
        token = text[start:i]
        if not token:
            continue
        core = _core(token)
        if not core:
            continue
        at = start + token.find(core)
        for candidate in (core, _folded(core)):
            if candidate in book:
                out.append((book[candidate], at))
                break
    return out


def symbols_of(text: str, book: Dict[str, str]) -> List[str]:
    return [s for s, _ in located_symbols(text, book)]


class SharedBookIndex:
    """Symbol -> blocks, built from what the blocks already carry."""

    def __init__(self, memory_dir: Path, book_path: Path | None = None):
        self.chunks_dir = Path(memory_dir) / "chunks"
        self.book_path = Path(book_path or os.environ.get("AIONS_CBMS_BOOK") or DEFAULT_BOOK)
        self.book: Dict[str, str] = {}
        self.sym2word: Dict[str, str] = {}
        self.sym2chunks: Dict[str, Set[str]] = {}
        self.where: Dict[str, Path] = {}
        self.total = 0
        self.book_mark: Dict | None = None

    def build(self, limit: int | None = None) -> int:
        """Load, do not re-encode. The previous index walked every block and ran the whole
        codec at every server start, then lost the result on shutdown."""
        self.book = load_book(self.book_path)
        # Symbol back to the word it stands for. This is what turns a hit into a place:
        # the symbol says the block is relevant, the word says WHERE in it to look.
        # First root wins, so the reverse map is stable as the book grows.
        for root, sym in self.book.items():
            self.sym2word.setdefault(sym, root)
        count = 0
        for i, f in enumerate(sorted(self.chunks_dir.glob("*.json"))):
            if limit and i >= limit:
                break
            try:
                obj = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            codes = obj.get("cbms_codes")
            # Only the list form. The old field held codes from the 16-symbol book under
            # the same name; treating those as if they were ours would quietly mix two
            # alphabets in one index.
            if not isinstance(codes, list) or not codes:
                continue
            cid = obj.get("id") or f.stem
            for c in codes:
                self.sym2chunks.setdefault(c, set()).add(cid)
            self.where[cid] = f
            if self.book_mark is None:
                self.book_mark = obj.get("cbms_book")
            count += 1
        self.total = count
        return count

    def _weight(self, symbol: str) -> float:
        """A symbol in 3 blocks of 167 tells you where to look; one in 90 does not. The
        previous scoring added 1 per hit and so could not tell them apart."""
        seen = len(self.sym2chunks.get(symbol, ()))
        if seen == 0:
            return 0.0
        return math.log((self.total + 1) / seen)

    def search(self, query: str, top_k: int = 12) -> List[Tuple[str, float]]:
        scores: Counter = Counter()
        for sym in set(symbols_of(query, self.book)):
            w = self._weight(sym)
            if w <= 0:
                continue
            for cid in self.sym2chunks.get(sym, ()):
                scores[cid] += w
        return sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))[:top_k]

    def content_of(self, chunk_id: str) -> str:
        f = self.where.get(chunk_id)
        if f is None:
            return ""
        try:
            return json.loads(f.read_text(encoding="utf-8")).get("content") or ""
        except Exception:
            return ""

    def snippet(self, chunk_id: str, chars: int = 200) -> str:
        """QUICK: the opening of the block. Costs one file read, because the store keeps
        its text readable instead of compressed - the whole reason for not using an
        archive format here."""
        return " ".join(self.content_of(chunk_id).split())[:chars]

    def deep(self, chunk_id: str, query: str, chars: int = 240) -> Tuple[str, int]:
        """DEEP: the passage that actually made this block rank, and where it begins.

        A symbol says the block is relevant; on its own that still means reading the
        block. The offsets say where, and QUICK may be approximate but this must not be.

        Which occurrence matters is decided by the query, not by position: the window
        chosen is the one where the most query weight gathers - several distinct rare
        symbols close together. A word that repeats twenty times therefore does not drag
        the answer to its first appearance, and a common symbol cannot outvote a rare one
        because the weights are the same ones that produced the ranking.
        """
        content = self.content_of(chunk_id)
        if not content:
            return "", -1

        weights = {s: self._weight(s) for s in set(symbols_of(query, self.book))}
        weights = {s: w for s, w in weights.items() if w > 0}
        if not weights:
            return self.snippet(chunk_id, chars), 0

        hits = [(s, at) for s, at in located_symbols(content, self.book) if s in weights]
        if not hits:
            return self.snippet(chunk_id, chars), 0

        # Every hit is a candidate anchor; the best window is the one that gathers the
        # most weight. Distinct symbols only - the same word repeated inside one window
        # says no more than it did the first time.
        best_start, best_at, best_score = 0, hits[0][1], -1.0
        for _, anchor in hits:
            start = max(0, anchor - chars // 3)
            inside = {s for s, at in hits if start <= at < start + chars}
            score = sum(weights[s] for s in inside)
            if score > best_score:
                best_score, best_start, best_at = score, start, anchor

        window = content[best_start:best_start + chars]
        return " ".join(window.split()), best_at
