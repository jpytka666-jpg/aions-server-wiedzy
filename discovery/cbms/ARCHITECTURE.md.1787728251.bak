# CBMS — co to jest naprawdę

**Odczytane ze źródeł 2026-08-26.** Każda liczba pochodzi z pliku albo z `discovery/inventory.py`,
nie z pamięci. Wersja maszynowa: [`findings.json`](findings.json). Pomiar: [`measurements.json`](measurements.json).

**CBMS = Code Book Memory System.** Nazwa jest z docstringa `codebook_engine.py`, nie z domysłu.

---

## 1. Jednym obrazkiem

```
                     ZAMIERZONA ŚCIEŻKA (działa, ale prawie nieużywana)

  tekst PL/EN
      │
      ▼  esperanto_bridge.to_esperanto()          99 linii, słownik 30 haseł + regex
  esperanto — jedna forma na jedno pojęcie
      │
      ▼  codebook_engine.Codebook.encode_eo_to_cbms()    56 linii, greedy longest-first
  kody CBMS  np. ['CR2','CR3','CR4','CR1']
      │
      ▼  cbms_symbolic_index.SymbolicIndex          56 linii, budowany w locie
  symbol → zbiór bloków


                     ŚCIEŻKA, KTÓRA NIESIE RUCH

  tekst
      │
      ▼  korean_keys.build_keys()                  34 linie
  zbiór kluczy 3-znakowych  {'g:abc', 'h:1a2', ...}
      │
      ▼  przecięcie zbiorów, sortowanie po liczbie trafień
  bloki


                     ADRESOWANIE

  content ──SHA-256[:12]──► K015B0B1D5ECD  ──SHA-1──► 귀균귀겠고굠관괠굠궀궠관궠갠가겠관균가귀굠검걠
            adres bloku                                  hangul_code (52/167 bloków)
```

---

## 2. Trzy warstwy, które ludzie mylą

| Warstwa | Plik | Co robi | Ile bloków dotyczy |
|---|---|---|---|
| **Adres** | `cbms_memory.py:195` | `K` + SHA-256(treść)[:12] | 167 / 167 |
| **Adres ozdobny** | `hangul_addressing.py` | hex → prawdziwe znaki hangul | 52 / 167 |
| **Kod** | `codebook_engine.py` | treść → symbole z książki kodów | **13 / 167** |

To jest sedno całego nieporozumienia wokół CBMS.
**Blok CBMS ≠ treść zakodowana w CBMS.** Pierwsze to pojemnik, drugie to zawartość.

---

## 3. Książka kodów ma 16 symboli

`aions_core/memory/codebook/codebook.json`:

| Rodzina | Symbole | Co pokrywa |
|---|---|---|
| A1–E5 | 5 | jedno zdanie demonstracyjne: *byłem dziś w sklepie, kupiłem chleb* |
| CR1–CR5 | 5 | słownik turnieju CRLA: system, zwycięzca, wynik, latencja, determinizm |
| CB1–CB6 | 6 | CBMS o samym sobie: system, blok, fragment, odmowa, panika, fakty/klucze |

Kształt wpisu:

```json
"A1": { "sem": "byc-past-1sg", "eo": ["mi estis"], "pl": ["byłem", "byłam"] }
```

**Dlaczego esperanto stoi po drodze.** Polski odmienia: *byłem* / *byłam*. Esperanto ma jedną formę:
*mi estis*. Kanonizacja idzie **przed** przypisaniem symbolu, więc książka potrzebuje jednego wpisu
zamiast wielu. To nie jest tłumaczenie — docstring mówi wprost `This is not a translator`.

---

## 4. Co faktycznie zostało zakodowane

**13 bloków ze 167.** Wszystkie tego samego kształtu, wszystkie z jednego dnia:

| | |
|---|---|
| pojęcie | `crla_pattern` (13 / 13) |
| użyte kody | `CR1`, `CR2`, `CR3`, `CR4` |
| powstały | 2025-10-28, między 12:53 a 19:00 |

```
pl : CRLA turniej: zwycięzca C04, wynik 0.956, latencja 0.719 ms.
eo : crla turniro: gajninto c04, poentaro 0.956, latenco 0.719 ms.
cbms_codes : ['CR2', 'CR3', 'CR4', 'CR1']
```

Warstwa kodowa **działa** i jest przejechana od końca do końca — na szablonie zdania, pod który
powstała. Nigdy jej poza ten szablon nie rozszerzono. Nie dlatego, że nie działa: dlatego,
że książka ma 16 symboli.

---

## 5. Wzorce myślenia Claude — tak, są w blokach; nie, nie w kodzie

| Co | Ile | Kiedy |
|---|---|---|
| `thinking_methodology_*` | 6 | 2025-09-09 06:07:06 — jedna partia, sekunda po sekundzie |
| `claude_meta_reasoning` (rama spinająca szóstkę) | 1 | 2025-09-09 06:07:07 |
| `session_context_save` | 9 | — |
| `consciousness_state` | 8 | pola `state_id`, `emotional_tone`, `confidence_level`, `activation_triggers` |
| `claude_behavior_rules` | 1 | 2025-11-29 |

Kształt każdego wzorca jest stały:

```
CLAUDE THINKING PATTERN: ANALYTICAL_BREAKDOWN
Core Pattern:        Break complex problems into smaller components
Methodology:         1. … 2. … 3. … 4. …
Practical Example:   …
Application Framework: …
```

Konsumuje je `cbms_think_like_claude()` i `_synthesize_chunks_with_claude_reasoning()`.

**Ale:** żaden z tych bloków nie ma pola `eo` ani `cbms_codes`. Ich treść to angielska proza.
Pojemnik jest CBMS-owy — adres `K`+hash, wpis w manifeście, krawędzie w grafie. Zawartość nie jest.

To rozróżnienie wyznacza, co zostało do zrobienia: warstwa adresowania i przechowywania jest
dla tych wzorców **gotowa**, warstwa kodowania **nigdy ich nie dotknęła** — i nie dotknie,
dopóki książka kodów nie dostanie symboli, których dziś w niej nie ma.

---

## 6. Odkurzanie: 73% bazy było echem systemu

Komentarz w `cbms_memory.py` (linie 110–130) mówi: *455 z 621 bloków to nie wiedza, tylko echo*.

**Ten pomiar da się dziś odtworzyć z dysku:**

| katalog | plików |
|---|---|
| `chunks/` | 167 |
| `chunks_quarantine/` | **455** |
| `chunks_purgatory/` | 3 |
| `blends/` | 8 |
| `gate_rejections.jsonl` | 59 linii |

455 na kwarantannie to dokładnie te 455 bloków, które policzył komentarz.

**Przyczyna zapisana w kodzie:** `_should_create_new_chunk()` decydował o zapisie na podstawie
**kształtu pytania** (`len>50` albo zawiera `new`/`how`), a nie tego, czy czegokolwiek się nauczono.
System zapisywał własne echo jako nową wiedzę:

```
"No prior knowledge found for: …"      ← zapis, że NICZEGO nie znaleziono
"Based on N knowledge chunks: …"       ← sklejka istniejących bloków
zrzuty statusów usług Windows, listy plików
```

**Bramka zapisu** (`learning_gate`) ma osiem nazwanych reguł — R1…R8 — i loguje każde odrzucenie.
Deklarowana skuteczność: łapie 457 z 621, w tym 455 realnych śmieci, **zero fałszywych alarmów**
na 164 blokach z prawdziwą wiedzą. Wyłącznik: `AIONS_WRITE_GATE=0`.

---

## 7. Graf referencji: 49 tysięcy krawędzi, przez lata nieczytany

| | |
|---|---|
| rozmiar | ~49 374 krawędzie |
| ile prowadzi do śmieci | 90,65% |
| kto po nim chodził do 2026-08-04 | **nikt** — graf był zapisywany i nigdy nieczytany |
| czytelnik dopisany | `expand_with_references(min_support=2, max_out_degree=40, max_expand=10)` |
| domyślnie | **WYŁĄCZONY** (`AIONS_GRAPH_EXPAND=1` włącza) |

Powód wyłączenia jest ciekawszy niż sam fakt. Mechanizm **działa poprawnie**: odwracalny 10/10,
zero regresji na pierwszych 15 wynikach, ~5 ms narzutu. Znajduje jednak głównie śmieci, i to nie
z winy tego kodu — graf jest **zatruty**. Bloki-syntezy cytują siebie nawzajem, tworząc klaster o:

- **niskiej** liczbie referencji → filtr `max_out_degree` ich nie łapie,
- **wysokim** współcytowaniu → podniesienie `min_support` też nie pomaga (sprawdzone: `min_support=3` klastra nie usuwa).

Kolejność zapisana w kodzie: **najpierw bramka** (zatrzymać produkcję śmieci), **potem czyszczenie**,
**dopiero potem** włączyć graf.

Skąd chain: skrypt zaszczepiający z 2025-09-09 dawał każdemu blokowi `references = poprzednie[-3:]`.
Graf zaczął życie jako **łańcuch o szerokości 3**, nie jako sieć.

---

## 8. Ścieżka pobierania, z limitami

`cbms_think()`, w kolejności — limity dopisane 2026-08-04:

| krok | limit | zmienna |
|---|---|---|
| wstrzyknięty kontekst | — | — |
| klucze koreańskie | 25 | `AIONS_RETRIEVAL_KR_LIMIT` |
| trafienia symboliczne | 7 | — |
| worki pojęć | 8 na pojęcie | `AIONS_RETRIEVAL_CONCEPT_LIMIT` |
| **suma** | **40** | `AIONS_RETRIEVAL_LIMIT` (0 = stare zachowanie) |
| rozwinięcie po grafie | 10 | `AIONS_GRAPH_EXPAND` (domyślnie off) |
| podbicie terminów krytycznych | pierwsze 100 kandydatów | — |

Przed poprawką worki pojęć **nie miały limitu**: średnio 295 z 613 bloków na zapytanie (48% bazy),
a do syntezy szło i tak tylko 15. Reszta była szumem — i trafiała do `references` nowego bloku,
stąd bloki z 300–446 referencjami. Tak dokładnie zatruwał się graf.

---

## 9. Warstwy pól = warstwy pisarzy

Pola opcjonalne w blokach, zmierzone:

| pole | ile bloków |
|---|---|
| `hangul_code` | 52 |
| `pattern_type` | 32 |
| `source` | 21 |
| `success_rate`, `domain`, `usage_count` | 16 |
| `eo`, `cbms_codes` | 13 |
| `strategy_id`, `metaphor_id`, `state_id`, `template_id`, `url` | 8 |

Grupy po 8 i 16 to nie przypadek. **Każda grupa to jeden pisarz, który przejechał raz
i zostawił swój kształt.** Historia systemu jest czytelna z rozkładu pól.

---

## 10. „Zastrzyk koreański" w Phi-3 — obalony, z dowodem

`aions_core/AIONS_KOREAN_INJECTION_RESULTS.json` deklaruje: Phi-3 Mini 4K, 8 bloków CBMS,
kompresja 3,31, **redukcja pamięci 75%**, 48 mapowań.

Co jest w środku naprawdę:

| deklaracja | pomiar |
|---|---|
| 48 mapowań | 16 sylab × 3 tensory (`q_proj`, `k_proj`, `mlp.gate_proj`), tylko warstwy 0–15 |
| „modyfikacje neuronowe" | 48 × 100 = 4800 wartości; **średnia −0,000491, odchylenie 0,100013**, zakres −0,369…0,383 → rozkład normalny N(0; 0,1), czyli **szum losowy** |
| 8 bloków CBMS, każdy z własnym wzorcem | wszystkie 8 `neural_pattern` są **bajt w bajt identyczne** (sha256 `fbfb16c4dc276df7`) — ten sam słownik 16×768 podpięty pod każdy blok |
| kompresja 3,19 / 2,85 / 4,2 / … | **stałe wpisane ręcznie**, nie policzone z niczego w pliku |

Zgadza się to z niezależnym pomiarem na wagach: różnica wstrzykniętego Phi-3 wobec bazowego
to szum nieskorelowany — odchylenie 0,000995, obcięcie ±2⁻⁸, korelacja między warstwami 0,00016.
**Ten plik jest źródłem tamtego szumu.**

Gdzie leży prawdziwe 3,19: w `korean_cbms_tokenizer.json`, 4016 wpisów. To własność **tokenizera**,
nie wag. Do modelu nic się nie nauczyło.

---

## 11. Rozjazd, który został otwarty

| | |
|---|---|
| manifest `total_chunks` | 159 |
| wpisy w `chunk_index` | 159 |
| pliki na dysku | **167** |
| różnica | **+8** |

Stary błąd był odwrotny: licznik rósł bezwarunkowo przy każdym zapisie, choć hash treści nadpisywał
ten sam plik — naprawione 2026-08-04 sprawdzeniem obecności w `chunk_index`. Te 8 to pliki **bez**
wpisu w manifeście. Kto je zapisał — nie wiadomo. Zapisane jako pytanie otwarte, nie zgadywane.

---

## 12. Trop niezweryfikowany: rodzina CBMS_KR

Blok `KTHINKSTACK001` (2025-11-08) twierdzi, że istnieje `cbms_kr_configs/` z wariantami silnika:
`CBMS_KR` (rdzeń), `cbms_kr_v1`, `cbms_kr_v1_blend`, `cbms_kr_v1_broadcast` oraz `CBMS_KR_PURE.py`,
każdy z manifestem `ARCH_CBMS_KR.md`. Używane rzekomo do przebudowy Korean Keys albo naprawy
uszkodzonego `kb.mmap`. Wzorzec `ITERATIVE_REFINEMENT` ma wymagać `cbms_kr_v1_blend`.

**Nic z tego nie zostało otwarte i sprawdzone.** To deklaracja wcześniejszej sesji, nie pomiar.
Traktować jak trop.

---

## Jak to odtworzyć

```bash
python discovery/inventory.py --memory-dir <ścieżka do aions_core/memory>
python discovery/ingest.py                     # buduje bazę wektorową z tego zapisu
```

`inventory.py` otwiera pliki wyłącznie do odczytu. Żywej bazy nie dotyka nic w tym katalogu.
