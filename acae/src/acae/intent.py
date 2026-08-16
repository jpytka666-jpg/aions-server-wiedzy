"""
intent.py — M13: intencja pytania ogranicza RODZAJ rzeczy (regula czasownika z Zorka).

SKAD TO SIE BIERZE
------------------
Pomiar pomylek (`scripts/measure_confusion.py`, 2026-08-15) pokazal wzorzec powtorzony
CZTERY RAZY: odpowiedz lezala w `scripts`, a ranker szedl w `aions_core/server`.
To nie jest pomylka co do TEMATU, tylko co do RODZAJU rzeczy — pytanie dotyczy czegos,
co sie URUCHAMIA, a ranker podaje cos, co STOI I NASLUCHUJE.

W parserze Infocom/Inform ta pomylka jest NIEMOZLIWA. Czasownik nie tylko szereguje —
on wyznacza, ktore obiekty w ogole sa dopuszczalne. `Verb 'burn' * noun 'with' held`
znaczy: to co palisz musi byc widoczne, a to czym palisz musi byc TRZYMANE. Token jest
ograniczeniem typu, nie podpowiedzia.

DWIE RZECZY ZAPOZYCZONE WPROST Z INFORM
---------------------------------------
1. **Pierwsza pasujaca linia wygrywa.** Linie gramatyki sa probowane po kolei i parser
   nigdy nie oglada dalszych. Dlatego kolejnosc `GRAMATYKA` jest czescia mechanizmu:
   intencje jednoznaczne stoja wyzej, najszersza na koncu.
2. **Implicit take.** Gdy gracz pisze „zjedz banana", a banan lezy na polce zamiast byc
   trzymany, gra NIE odmawia — dobiera brakujacy krok. U nas: gdy zaden kandydat nie
   przechodzi ograniczenia, wracamy do pelnej przestrzeni zamiast zwracac pustke.
   Dokumentacja Inform nazywa odmowe w takiej sytuacji „petty" i ma racje.

DOPASOWANIE PO CALYCH SLOWACH, NIGDY PO FRAGMENCIE
--------------------------------------------------
`cbms_unified_server.py:287` robi `if pattern in user_lower` i przez to wzorzec „hi"
lapie sie w „arc-HI-tecture" — zmierzone: 25% prawdziwych zapytan przechwyconych bledem.
Ta sama wada zabila M10. Tu tokenizujemy pytanie i sprawdzamy PRZYNALEZNOSC DO ZBIORU.

UCZCIWOSC KONSTRUKCJI
---------------------
Tablica napisana wylacznie z definicji szesciu wartosci `kind` i z ogolnych angielskich
form pytan. **Zbior `acae/tests/` nie byl otwierany.** Inaczej napisalibysmy sobie
odpowiedzi do wlasnego egzaminu, tak jak przy opisach i dziedzinach.
"""

from __future__ import annotations

import re
from typing import Iterable, Mapping, Sequence

SCHEMA = "acae.intent.v1"

SLOWO = re.compile(r"[a-z0-9_]+")

# Kolejnosc MA ZNACZENIE — pierwsza pasujaca linia wygrywa (regula z Inform).
# Na gorze intencje najbardziej jednoznaczne, na dole najszersza.
#
# `serves` i `connects` stoja w jednej linii swiadomie: pytanie o punkt koncowy
# czesto trafia w klej, ktory z nim rozmawia, i odwrotnie. To jedyna para, w ktorej
# rozdzielenie byloby udawaniem precyzji, ktorej nie mamy.
GRAMATYKA: tuple[tuple[str, frozenset[str], frozenset[str]], ...] = (
    (
        "sprawdzanie",
        frozenset({
            "test", "tests", "tested", "testing", "verify", "verifies", "verified",
            "validate", "validates", "validation", "assert", "asserts", "assertion",
            "smoke", "regression", "guard", "guardrail",
        }),
        frozenset({"checks"}),
    ),
    (
        "ustawienia",
        frozenset({
            "config", "configs", "configuration", "configured", "setting", "settings",
            "constant", "constants", "schema", "schemas", "default", "defaults",
            "parameter", "parameters", "option", "options", "declared", "declaration",
        }),
        frozenset({"describes"}),
    ),
    (
        "serwer_i_polaczenia",
        frozenset({
            "server", "servers", "serve", "serves", "endpoint", "endpoints",
            "request", "requests", "http", "api", "port", "listen", "listens",
            "listening", "bridge", "bridges", "adapter", "adapters", "client",
            "protocol", "integration", "integrates", "wrapper", "mcp",
        }),
        frozenset({"serves", "connects"}),
    ),
    (
        "przechowywanie",
        frozenset({
            "store", "stores", "stored", "storing", "storage", "save", "saves",
            "saved", "persist", "persists", "persisted", "persistence",
            "database", "db", "index", "indexed", "cache", "cached",
        }),
        frozenset({"stores"}),
    ),
    (
        "uruchamianie",
        frozenset({
            "run", "runs", "running", "launch", "launches", "launched", "start",
            "starts", "started", "execute", "executes", "invoke", "invoked",
            "script", "scripts", "cli", "demo", "demos", "walkthrough", "entrypoint",
        }),
        frozenset({"runs"}),
    ),
)


def question_words(text: str) -> frozenset[str]:
    """Slowa pytania jako ZBIOR. Dopasowanie po calym slowie, nie po fragmencie."""
    return frozenset(SLOWO.findall(text.lower()))


def match_intent(question: str) -> tuple[str, frozenset[str]] | None:
    """
    Pierwsza pasujaca linia gramatyki. `None`, gdy zadna nie pasuje — wtedy
    ograniczenia nie ma i pytanie idzie do pelnej przestrzeni.
    """
    slowa = question_words(question)
    for nazwa, wyzwalacze, rodzaje in GRAMATYKA:
        if slowa & wyzwalacze:
            return nazwa, rodzaje
    return None


def allowed_files(
    assignments: Mapping[str, Mapping[str, object]],
    rodzaje: Iterable[str],
) -> frozenset[str]:
    """Pliki, ktorych `kind` mieszcza sie w dopuszczonym zbiorze."""
    dozwolone = set(rodzaje)
    return frozenset(
        sciezka for sciezka, wpis in assignments.items()
        if str(wpis.get("kind")) in dozwolone
    )


def constrain(
    question: str,
    assignments: Mapping[str, Mapping[str, object]],
) -> tuple[frozenset[str] | None, dict]:
    """
    Zbior dopuszczonych plikow plus paragon. `None` znaczy „bez ograniczenia".

    Paragon niesie nazwe linii i liczby, bo bez nich nie da sie odroznic
    „tablica milczala" od „tablica zadzialala i wycieła za duzo".
    """
    trafienie = match_intent(question)
    if trafienie is None:
        return None, {
            "rule": "intent_grammar",
            "line": None,
            "kinds": [],
            "files_in_scope": len(assignments),
            "note": "zadna linia gramatyki nie pasuje — bez ograniczenia",
        }
    nazwa, rodzaje = trafienie
    pliki = allowed_files(assignments, rodzaje)
    return pliki, {
        "rule": "intent_grammar",
        "line": nazwa,
        "kinds": sorted(rodzaje),
        "files_in_scope": len(pliki),
        "note": "pierwsza pasujaca linia wygrywa, jak w gramatyce Inform",
    }
