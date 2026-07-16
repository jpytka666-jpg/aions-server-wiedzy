import re
from typing import Tuple


SAFE_UNCHANGED_PATTERNS = [
    re.compile(r"\[[^\]]+\]"),          # bracketed blocks like [Źródło: ...]
    re.compile(r"\d+[\d\s.,]*"),        # numbers
]


def _normalize_ws(text: str) -> str:
    # Normalize whitespace but preserve newlines
    text = text.replace("\r", "")
    # collapse multiple spaces
    text = re.sub(r"[ \t]+", " ", text)
    # collapse 3+ newlines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # trim trailing spaces per line
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return text.strip()


def _safe_invariants(orig: str, styled: str) -> bool:
    # Ensure bracketed blocks and numeric sequences preserved as multisets
    def grab(pat, s):
        out = []
        for m in pat.finditer(s):
            out.append(m.group(0))
        return out
    for pat in SAFE_UNCHANGED_PATTERNS:
        a = sorted(grab(pat, orig))
        b = sorted(grab(pat, styled))
        if a != b:
            return False
    return True


def style_pass(answer: str) -> Tuple[str, bool, str]:
    """Lightweight stylistic cleanup that MUST NOT change facts.

    Returns: (styled_text, applied, warning)
    """
    if not isinstance(answer, str) or not answer.strip():
        return answer, False, "empty-or-nonstring"

    orig = answer
    styled = _normalize_ws(orig)
    # if there is a '[Źródło:' ensure it's on a new paragraph
    styled = re.sub(r"\n?\s*\[Źródło:", "\n\n[Źródło:", styled)
    # Ensure first character capitalized (if letter)
    if styled and styled[0].islower():
        styled = styled[0].upper() + styled[1:]

    if not _safe_invariants(orig, styled):
        # refuse to apply style if invariants broken
        return orig, False, "invariants-broken"

    if styled == orig:
        return orig, False, "no-change"
    return styled, True, "ok"

