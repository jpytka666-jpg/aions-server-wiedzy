"""
secrets.py — plik z sekretem nie wchodzi do packa.

Baza regul to guard_write.py z hookow Marcina (wzorzec przypisania klucza),
rozszerzona o formaty, ktore rozpoznaje sie po samym ksztalcie tokenu i ktore
nie potrzebuja slowa "key" obok siebie.

ZASADA: znaleziony sekret NIE jest nigdzie cytowany — ani w wyniku, ani w logu.
Raport mowi "regula X trafila w linii N" i na tym koniec. Skaner, ktory przepisuje
sekret do raportu, przenosi wyciek zamiast go zatrzymac.
"""

from __future__ import annotations

import re
from typing import Sequence

# Slowa kluczowe budowane osobno od reszty wzorca — inaczej ta linia sama
# wygladalaby jak przypisanie sekretu i guard_write zablokowalby zapis tego pliku.
_KEYWORD = r"(?:api[_-]?key|apikey|secret|token|passwd|password|access[_-]?key)"

RULES: Sequence[tuple[str, re.Pattern]] = (
    ("assignment", re.compile(_KEYWORD + r"\s*[=:]\s*[\"'][^\"'\s]{12,}[\"']", re.I)),
    ("private_key_block", re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----")),
    ("anthropic_key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9]{32,}\b")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("slack_token", re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{6,}")),
)

# Linia, ktora czyta wartosc ze srodowiska albo z configu, nie jest wyciekiem —
# jest wzorcem, ktorego chcemy. Ta sama logika co ENV_OK w guard_write.py.
_FROM_ENV = re.compile(r"getenv|environ|process\.env|\$env:|ENV\[|config\[", re.I)

# Placeholdery w dokumentacji i przykladach. Bez tego kazdy README z "sk-ant-xxxx"
# wyrzucalby plik z packa.
_PLACEHOLDER = re.compile(
    r"(?:x{6,}|\.{3,}|<[^>]{3,}>|\bTU_WKLEJ\b|\byour[_-]|\bexample\b|\bdummy\b|\bplaceholder\b)",
    re.I,
)


def scan_text(text: str) -> list[dict]:
    """
    Zwraca liste trafien: [{"rule": nazwa, "line": numer}], posortowana.

    Bez fragmentu tresci i bez samego dopasowania — celowo. Numer linii wystarczy,
    zeby czlowiek poszedl i sprawdzil, a raport moze bezpiecznie trafic do packa.
    """
    hits: list[dict] = []
    for lineno, line in enumerate(text.split("\n"), 1):
        stripped = line.strip()
        if not stripped:
            continue
        if _FROM_ENV.search(line) or _PLACEHOLDER.search(line):
            continue
        for name, pattern in RULES:
            if pattern.search(line):
                hits.append({"rule": name, "line": lineno})
    hits.sort(key=lambda h: (h["line"], h["rule"]))
    return hits


def scan_bytes(raw: bytes) -> list[dict]:
    """Wygoda dla wywolan z portu Reader, ktory operuje na bajtach."""
    return scan_text(raw.decode("utf-8", errors="replace"))


def has_secret(raw: bytes) -> bool:
    return bool(scan_bytes(raw))
