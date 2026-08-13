"""
verify.py — M10: warunek DOPUSZCZENIA zamiast kolejnej zmiany punktacji.

PO CO
-----
Czternascie mechanizmow zmienialo sposob liczenia punktow. Zaden nie ruszyl sciany,
o ktora rozbil sie najlepszy wariant: `embed_desc` porzadkuje najlepiej w calym projekcie
(`MRR` 0,243) i ma kontrole negatywna 97,7% — czyli na pytanie o rzecz, ktorej w repo
NIE MA, odpowiada niemal tak samo pewnie jak na prawdziwe. Podobienstwo wektorow zawsze
zwroci jakas liczbe, wiec zawsze cos wygra.

M10 nie dotyka punktacji ani o promil. Dokłada pytanie zadawane PO uszeregowaniu:
czy ten symbol w ogole ma prawo byc odpowiedzia?

ZASADA: LICZYMY SWIADECTWA, NIE PROGUJEMY PODOBIENSTWA
------------------------------------------------------
Wzorzec wziety z dzialajacego AIONS, gdzie „nie wiem" zapada w trzech niezaleznych
miejscach i za kazdym razem jest LICZNIKIEM, nigdy progiem na podobienstwie:
  `cbms_unified_server.py:186`  — `if len(refs) < 2` (PANIC)
  `crla_core.py:104`            — `if len(chunks) < cand.min_hits` (odmowa)
  `pocket_qc.py:45`             — `cbms_count > 0` (czy tekst koduje sie na pojecie)

Prog na podobienstwie musialby byc dobrany na danych — czyli bylby pokretlem strojonym
na szesciu negatywach. Licznik nie musi: „zero trafien" nie wymaga kalibracji.

INNA REPREZENTACJA — to jest sedno, nie szczegol
------------------------------------------------
Weryfikator NIE jest tym, co szeregowalo. Ranking liczy podobienstwo gestych wektorow,
weryfikator sprawdza DOSLOWNA obecnosc tokenu. Gdyby sprawdzal ta sama miara, ktora
wybrala odpowiedz, sprawdzalby sam siebie i zawsze wychodzilo by „zgadza sie".

Wzorzec z `pocket_qc.py`: odpowiedz idzie przez codebook, a nie przez baze wektorowa,
ktora ja znalazla. ACAE nie robilo tego nigdzie — ranker byl sedzia wlasnej pracy.
"""

from __future__ import annotations

from typing import Mapping, Sequence

# `_haystack` swiadomie z retrieve: jedno zrodlo prawdy o tym, jaki tekst symbolu
# widzi warstwa leksykalna. Odtworzenie go tutaj rozjechaloby sie przy pierwszej
# zmianie pola w retrieve.py.
from .retrieve import _haystack

SCHEMA = "acae.verify.v1"


def terms_covered(
    path: str,
    row: Mapping[str, object],
    terms: Sequence[str],
    description: str = "",
) -> int:
    """
    Ile ROZNYCH terminow zapytania wystepuje doslownie w tekscie symbolu.

    Liczymy terminy, nie wystapienia. Opis powtarzajacy slowo dziesiec razy ma dac
    tyle samo co opis wspominajacy je raz — inaczej dlugosc opisu stalaby sie
    pokretlem, a generator mozna by naklonic do powtarzania slow kluczowych.
    """
    hay = f"{_haystack(path, row)} {description.lower()}"
    return sum(1 for term in terms if term in hay)


def admit(
    ranked: Sequence[Mapping[str, object]],
    terms: Sequence[str],
    descriptions: Mapping[str, str],
    min_terms: int,
) -> list[dict]:
    """
    Przepuszcza wylacznie symbole z co najmniej `min_terms` swiadectwami.

    Kolejnosc pozostaje DOKLADNIE ta, ktora nadal ranker. Filtr moze tylko USUWAC —
    niczego nie promuje, nie dodaje terminow, nie wprowadza nowej wagi. Dzieki temu
    roznica wobec `embed_desc` pochodzi wylacznie z odsiewu, a nie z przestawiania.

    Pusta lista jest POPRAWNYM wynikiem i znaczy „nie wiem". To jedyna sciezka,
    ktora ACAE ma do powiedzenia tego wprost.
    """
    if not terms:
        return []
    return [
        dict(item)
        for item in ranked
        if terms_covered(
            str(item["path"]), item["row"], terms, descriptions.get(str(item["path"]), "")
        ) >= min_terms
    ]
