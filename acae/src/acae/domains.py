"""
domains.py — M11: warstwa dziedzin. Najpierw polka, potem ksiazka.

PO CO
-----
Pomiar z 2026-08-15 (`scripts/measure_confusion.py`) pokazal, ze pomylki rankera nie sa
szumem, tylko sa UPORZADKOWANE: przy porazce osiem z dziesieciu odpowiedzi pochodzi
z jednego katalogu, a wlasciwy katalog nie pojawia sie w czolowce w 14 z 21 przypadkow.
Ranker nie bladzi — pewnym krokiem idzie na zla polke i wygarnia ja cala.

Bledu uporzadkowanego da sie bronic kierowaniem. Szumu nie. Dlatego M11 najpierw pyta
„o czym w ogole jest to pytanie", a dopiero potem szuka wsrod plikow wybranych dziedzin.

CZYM TO ROZNI SIE OD M6, KTORY PRZEGRAL
---------------------------------------
M6 wyprowadzal „zakresy" ze STRUKTURY — wspolzmiennosci commitow i grafu wywolan —
i zlepil 139 ze 169 plikow w jeden worek. Bramka nie bramkowala. M9c powtorzyl to
na opisach i bylo GORZEJ (mediana 157 ze 169).

Tu dziedziny sa PISANE po ludzku, jak opisy plikow w M8 — jedyny mechanizm, ktory
w tym projekcie zadzialal. Dziedzina moze przecinac katalogi i nie ma obowiazku
pokrywac sie z drzewem plikow.

PULAPKA, KTORA LATWO PRZEOCZYC: `not_about` NIE WCHODZI DO WEKTORA
------------------------------------------------------------------
Kazda dziedzina ma pole `not_about` — zdanie „czym to NIE jest", ktore oddziela ja
od najblizszego sasiada. Jest bezcenne przy PRZYPISYWANIU plikow i dla czlowieka.

Ale do tekstu, z ktorym porownujemy PYTANIE, wchodzic NIE MOZE. Gdyby weszlo, dziedzina
„gotowanie" z dopiskiem „to nie dotyczy silnikow samochodowych" mialaby slowo „silnik"
w swoim tekscie — i przyciagalaby wlasnie te pytania, przed ktorymi mial chronic.
Zaprzeczenie nie istnieje w przestrzeni wektorow; zostaje samo slowo.

Dlatego `domain_text()` sklada WYLACZNIE nazwe i opis. To nie jest optymalizacja,
tylko warunek poprawnosci.

DETERMINIZM
-----------
Ta sama arytmetyka calkowita co w M7: wektory z przypietego artefaktu, podobienstwo
w promilach przez `similarity_permille`, remisy rozstrzygane po `id` dziedziny.
Zadnych floatow w porzadkowaniu.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .embed import similarity_permille

SCHEMA = "acae.domains.v1"

# Dopuszczalne wartosci pola `kind`. Warstwa „rodzaj rzeczy" NIE jest czescia M11 —
# zbieramy ja przy okazji przypisywania, bo model i tak ma opis przed oczami, ale
# do mechanizmu wchodzi dopiero po osobnej prerejestracji. Zbieranie etykiet naraz
# to co innego niz mierzenie ich naraz.
KINDS = frozenset({"runs", "serves", "stores", "checks", "connects", "describes"})


class DomainsError(RuntimeError):
    """Artefakt dziedzin nie nadaje sie do pomiaru."""


def domain_text(domain: Mapping[str, object]) -> str:
    """
    Tekst dziedziny do porownania z pytaniem: nazwa + opis. BEZ `not_about`.

    Powod w naglowku modulu — zaprzeczenie w wektorze zamienia sie w przyciaganie.
    """
    return f"{domain.get('name') or ''} {domain.get('description') or ''}".strip()


def load_domains(path: Path) -> tuple[list[dict], dict]:
    dane = json.loads(Path(path).read_text(encoding="utf-8"))
    domeny = dane.get("domains")
    if not isinstance(domeny, list) or not domeny:
        raise DomainsError(f"{path}: brak listy `domains`")
    ids = [str(d.get("id") or "") for d in domeny]
    if "" in ids:
        raise DomainsError(f"{path}: dziedzina bez `id`")
    if len(set(ids)) != len(ids):
        raise DomainsError(f"{path}: powtorzone `id` dziedzin")
    for d in domeny:
        if not str(d.get("description") or "").strip():
            raise DomainsError(f"{path}: dziedzina {d.get('id')} bez opisu")
    return domeny, dane.get("provenance", {})


def load_assignments(paths: Iterable[Path], znane_id: Sequence[str]) -> dict[str, dict]:
    """
    Scalenie czesciowych przypisan. Odmawia przy sprzecznosci lub nieznanej dziedzinie —
    cichy blad tutaj przesunalby pliki na zle polki i pomiar nie mialby jak tego pokazac.
    """
    dozwolone = set(znane_id)
    scalone: dict[str, dict] = {}
    for p in paths:
        czesc = json.loads(Path(p).read_text(encoding="utf-8"))
        for sciezka, wpis in czesc.items():
            if sciezka in scalone and scalone[sciezka] != wpis:
                raise DomainsError(f"{sciezka}: dwa rozne przypisania w {p}")
            prim = str(wpis.get("primary") or "")
            sec = wpis.get("secondary")
            if prim not in dozwolone:
                raise DomainsError(f"{sciezka}: nieznana dziedzina `{prim}` ({p})")
            if sec is not None and str(sec) not in dozwolone:
                raise DomainsError(f"{sciezka}: nieznana dziedzina wtorna `{sec}` ({p})")
            if str(wpis.get("kind") or "") not in KINDS:
                raise DomainsError(f"{sciezka}: nieznany rodzaj `{wpis.get('kind')}` ({p})")
            scalone[sciezka] = dict(wpis)
    return scalone


class DomainIndex:
    """
    Kieruje pytanie do dziedzin i zwraca pliki tych dziedzin.

    Pytanie porownywane jest WYLACZNIE z opisami dziedzin. Kod nie jest na tym etapie
    dotykany w ogole — to jest ta sama zasada, ktora w M6 nazywalismy „pytanie nie dotyka
    kodu przy routowaniu", tyle ze tam proza byla wyliczana, a tu jest napisana.
    """

    def __init__(self, embedder, domeny: Sequence[Mapping[str, object]],
                 przypisania: Mapping[str, Mapping[str, object]]) -> None:
        self.embedder = embedder
        self.ids = [str(d["id"]) for d in domeny]
        self.wektory = [embedder.vector(domain_text(d)) for d in domeny]

        pliki: dict[str, set[str]] = {i: set() for i in self.ids}
        for sciezka, wpis in przypisania.items():
            pliki[str(wpis["primary"])].add(sciezka)
            wtorna = wpis.get("secondary")
            if wtorna:
                pliki[str(wtorna)].add(sciezka)
        self.pliki_dziedziny = {i: frozenset(sorted(s)) for i, s in pliki.items()}

    def route(self, pytanie: str, top: int) -> list[tuple[str, int]]:
        """Najlepsze `top` dziedzin. Remis rozstrzyga `id`, zeby wynik byl powtarzalny."""
        qv = self.embedder.vector(pytanie)
        wyniki = [
            (self.ids[i], similarity_permille(qv, self.wektory[i]))
            for i in range(len(self.ids))
        ]
        wyniki.sort(key=lambda kv: (-kv[1], kv[0]))
        return wyniki[:top]

    def files(self, pytanie: str, top: int) -> tuple[frozenset[str], list[tuple[str, int]]]:
        """
        Pliki do przeszukania plus paragon (ktore dziedziny i z jakim wynikiem).

        Zwrocenie PUSTEGO zbioru jest poprawnym wynikiem i znaczy „nie wiem" — miernik
        ma wtedy zastosowac fallback na pelna przestrzen i odnotowac to w diagnostyce,
        zamiast po cichu udawac, ze bramka nic nie zrobila.
        """
        wybrane = self.route(pytanie, top)
        zbior: set[str] = set()
        for did, wynik in wybrane:
            if wynik > 0:
                zbior |= self.pliki_dziedziny.get(did, frozenset())
        return frozenset(zbior), wybrane
