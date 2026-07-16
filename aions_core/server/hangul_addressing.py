#!/usr/bin/env python3
from __future__ import annotations

import hashlib

_HANGUL_BASE = ord("가")


def _hex_to_hangul(s: str) -> str:
    out = []
    for ch in s:
        n = int(ch, 16)
        out.append(chr(_HANGUL_BASE + n * 32))
    return "".join(out)


def make_hangul_code(data: str, length: int = 23) -> str:
    h = hashlib.sha1(data.encode("utf-8")).hexdigest()
    return _hex_to_hangul(h[:length])

