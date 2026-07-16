import re
import hashlib
from typing import Set

_TOKEN_RE = re.compile(r"[A-Za-z0-9]{2,}")


def _trigrams(s: str):
    for i in range(len(s) - 2):
        yield s[i : i + 3]


def build_keys(text: str) -> Set[str]:
    """Build syllable-like fixed-length keys inspired by Hangul blocks.

    - Normalize tokens (alnum, lower)
    - Derive short 3-char 'syllables' via:
      * character 3-grams from token
      * 3-char groups from SHA1(token) hex
    - Return a set of keys for matching.
    """
    if not text:
        return set()
    tokens = [t.lower() for t in _TOKEN_RE.findall(text)]
    keys: Set[str] = set()
    for tok in tokens:
        # direct 3-grams (prefix 'g:')
        for g in _trigrams(tok[:12]):  # limit to first 12 chars
            keys.add("g:" + g)
        # hashed groups (stable, prefix 'h:')
        h = hashlib.sha1(tok.encode("utf-8")).hexdigest()[:12]
        keys.add("h:" + h[0:3])
        keys.add("h:" + h[3:6])
    return keys
