# Zmiany 2026-08: pamięć i operator

**Commit:** `53c7609`
**Data:** 2026-08-04 – 2026-08-06
**Zasada:** każda zmiana ma pomiar przed i po, wyłącznik i kopię zapasową.

---

## Spis wyłączników

Wszystko da się cofnąć bez ruszania kodu.

| Zmienna | Domyślnie | Ustaw na | Efekt |
|---|---|---|---|
| `AIONS_WRITE_GATE` | `1` (włączona) | `0` | wyłącza bramkę zapisu, wraca stan sprzed zmiany |
| `AIONS_RETRIEVAL_LIMIT` | `40` | `0` | wyłącza wszystkie limity wyników, zachowanie 1:1 jak przedtem |
| `AIONS_RETRIEVAL_KR_LIMIT` | `25` | dowolna | limit wyników z kluczy koreańskich |
| `AIONS_RETRIEVAL_CONCEPT_LIMIT` | `8` | dowolna | limit na jeden worek pojęcia |
| `AIONS_GRAPH_EXPAND` | `0` (wyłączone) | `1` | włącza rozwijanie wyników o graf `references` |
| `AIONS_GRAPH_MIN_SUPPORT` | `2` | dowolna | ile głosów musi mieć sąsiad |
| `AIONS_GRAPH_MAX_EXPAND` | `10` | dowolna | ilu sąsiadów maksymalnie |
| `AIONS_GRAPH_MAX_DEGREE` | `40` | dowolna | próg odrzucania bloków-hubów |

Wykluczenia dyskowe: plik `control_plane/operator/disk_overrides.json`. Usunięcie pliku przywraca globalny próg 90% dla wszystkich wolumenów.

**Kopie zapasowe:** `_backups/*-2026080[46]` — stan każdego pliku przed każdą pojedynczą zmianą.

---

## 1. Bramka zapisu

**Plik:** `aions_core/server/cbms_memory.py` — `learning_gate()`, `_GATE_RULES`, `_log_gate_rejection()`

### Problem

Pomiar na pełnym korpusie 621 bloków wykazał, że **455 (73,3%) to nie wiedza, tylko echo systemu**:

| Kategoria | Bloków |
|---|---:|
| META_SYNTHESIS (`"Based on N knowledge chunks: ..."`) | 420 |
| NULL_KNOWLEDGE (`"No prior knowledge found for X"`) | 17 |
| CONVERSATION_LOG | 14 |
| SYSTEM_DUMP (listy plików, statusy usług) | 4 |
| **prawdziwa wiedza** | **164** |

**90,65% z 49 374 krawędzi grafu `references` prowadzi do tych śmieci.**

### Przyczyna

`_should_create_new_chunk()` decydował o zapisie na podstawie **kształtu pytania**:

```python
return len(query) > 50 or "new" in query.lower() or "how" in query.lower()
```

Nie na podstawie tego, czy czegokolwiek się nauczono. Dowolne pytanie dłuższe niż 50 znaków tworzyło blok z własną syntezą systemu.

### Rozwiązanie

Osiem reguł odrzucania sprawdzanych **przed zapisem**, w `create_knowledge_chunk()`:

| Reguła | Co łapie |
|---|---|
| R1 | „No prior/direct knowledge found for" |
| R2 | opakowanie syntezy na początku treści |
| R3 | markery generatora |
| R4 | zrzut statusów usług Windows |
| R5 | treść to praktycznie sama lista ID bloków |
| R6 | krótsze niż 25 znaków |
| R7 | zrzut listy plików |
| R8 | log rozmowy |

### Weryfikacja

| Test | Wynik |
|---|---|
| Fałszywe alarmy na 164 blokach prawdziwej wiedzy | **0** |
| Śmieci zablokowanych z 455 | **455** |
| Wyłącznik `AIONS_WRITE_GATE=0` | działa |
| Regresja w wyszukiwaniu | brak |
| `total_chunks` po testach | 613 → 613 |

Odrzucenia trafiają do `aions_core/memory/gate_rejections.jsonl` — **widać, co bramka blokuje**.

### Obejście dla świadomych wywołujących

```python
create_knowledge_chunk(content, concept, bypass_gate=True)
```

Dla przypadków, w których wywołujący wie, co robi (ingest zatwierdzonych blendów, import z zewnątrz). Zwraca `None`, gdy bramka odrzuci.

---

## 2. Limity wyników wyszukiwania

**Plik:** `aions_core/server/cbms_memory.py` — `cbms_think()`

### Problem

Trzy źródła wyników, jedno bez ogranicznika:

| Źródło | Limit przed zmianą |
|---|---|
| klucze koreańskie | 50 |
| indeks symboliczny | 7 |
| **worki pojęć** | **brak** |

`find_chunks_by_concept()` zwracał **cały worek**. Efekt: średnio **295 z 613 bloków na zapytanie** — 48% całej bazy. Do syntezy odpowiedzi trafiało tylko 15. Reszta była szumem.

Gorzej: `create_knowledge_chunk()` zapisywał **całą tę listę** jako `references` nowego bloku. Stąd bloki z 300–446 referencjami. **To jest źródło zatrucia grafu.**

### Rozwiązanie i weryfikacja

| Miara | Przed | Po |
|---|---:|---:|
| Wyników na zapytanie | 295 | **33** |
| Udział bazy | 48% | 5% |
| **Pierwsze 15 ID (z nich powstaje odpowiedź)** | — | **identyczne w 10/10 zapytaniach** |
| Referencji dla nowego bloku | 295 | 33 |
| Czas | 10,3 ms | 11,2 ms |

Wycięty został wyłącznie ogon listy, który nigdy nie docierał do odpowiedzi. `AIONS_RETRIEVAL_LIMIT=0` daje **identyczne listy** co przed zmianą — sprawdzone na 10/10 zapytaniach.

---

## 3. Deduplikacja

`chunk_id` to hash treści, więc identyczna treść nadpisywała ten sam plik — ale `total_chunks` i `concept_map` rosły **bezwarunkowo**. Stąd rozjazd manifestu (613) z liczbą plików na dysku (621).

Po zmianie: licznik rośnie tylko przy naprawdę nowym bloku, `concept_map` nie dostaje duplikatów.

---

## 4. Rozwijanie grafu — zbudowane, WYŁĄCZONE

**Plik:** `aions_core/server/cbms_memory.py` — `expand_with_references()`

Bloki mają pole `references` tworzące graf ~49 tys. krawędzi. **Do 2026-08-04 żaden kod retrievalu po nim nie chodził.**

Mechanizm zbudowano: rozwijanie przez **co-cytowanie** (sąsiad musi być wskazany przez ≥2 bloki z wyników), z pomijaniem bloków-hubów.

### Dlaczego jest wyłączone

| Test | Wynik |
|---|---|
| Odwracalność | 10/10 |
| Regresja na pierwszych 15 | zero |
| Błędy | zero |
| Narzut czasu | ~5 ms |
| **Trafność znalezionych sąsiadów** | **zła** |

Graf jest zatruty **samoreferencyjnym klastrem bloków-syntez** („Based on N knowledge chunks: … No prior knowledge found for …"), które cytują się nawzajem. Mają **niską** liczbę referencji, więc filtr hubów ich nie łapie, a **wysokie** co-cytowanie, więc podniesienie progu głosów też nie pomaga (sprawdzone przy `min_support=3`).

**Włączyć dopiero po wyczyszczeniu bazy.** Bramka zapisu zatrzymuje przyrost śmieci; czyszczenie starych to osobne zadanie.

---

## 5. Wyciszenie fałszywego alarmu `disk_full`

**Pliki:** `control_plane/operator/loop.py`, `control_plane/operator/disk_overrides.json`

### Ustalenie

Dysk **F: jest hostem dla Dev Drive D:**

| | |
|---|---:|
| `F:\workspace.vhdx` (kontener dysku D:) | 220,00 GB |
| D: rozmiar całkowity | 219,94 GB |
| `pagefile.sys` | 15,5 GB |
| **razem** | **235,5 z 238 GB** |

Zgodność rozmiaru pliku z rozmiarem dysku D: oznacza kontener o **stałym rozmiarze** — nie rośnie. Wolne 47,7 GB na D: znajduje się **wewnątrz** kontenera i nie zajmuje ani bajta więcej na F:.

**Zapełnienie F: na poziomie 98–99% jest stanem poprawnym i stałym.**

### Skala błędu

Od **2026-07-31 09:04** do **2026-08-06**:

- **1812** fałszywych zgłoszeń `disk_full` dla `/mnt/f`
- **1746** z nich dodatkowo uruchomiło lokalny model językowy, żeby skomentować nieistniejący problem — **co 5 minut, przez tydzień**
- **żadne nie dotarło do człowieka** — pętla operatora nie ma kanału wyjściowego

Dla porównania: przez 16 dni przed pojawieniem się błędu log urósł o **14 wpisów**.

### Rozwiązanie

Wykluczenia i progi per-wolumen w `control_plane/operator/disk_overrides.json`:

```json
{
  "/mnt/f": { "ignore": true, "reason": "..." },
  "/mnt/x": { "threshold_pct": 95.0 }
}
```

Odczyt przy każdym cyklu — **zmiana nie wymaga restartu**.

**Zachowanie awaryjne:** brak pliku, zły JSON albo brak wpisu dla wolumenu → globalny próg 90%. Czyli **fail-open** — przy problemie z konfiguracją operator dalej alarmuje, nie milczy. Zweryfikowane testem.

### Dlaczego plik leży przy kodzie

`runtime/` jest w `.gitignore`. Konfiguracja w `runtime/state/` byłaby tracona przy każdym świeżym klonie i **fałszywy alarm by wracał**. To konfiguracja człowieka, nie stan systemu — należy do repozytorium.

### Archiwizacja

`runtime/state/operator_incidents.jsonl` (1828 wpisów, 1,92 MB, ponad 96% szumu) → `operator_incidents_archive_2026-07-15_2026-08-06.jsonl`. Nowy log startuje pusty.

---

## 6. Pierwszy prawdziwy wpis wiedzy

**Blok `KE2969827A76F`**, koncept `infrastruktura_dyskowa`.

Treść: ustalenie o F:/Dev Drive D: — z pomiarem, interpretacją, skutkiem operacyjnym i prowenancją.

| Pole | Wartość |
|---|---|
| `kind` | `learned_fact` |
| `status` | `verified` |
| `confidence` | 0.98 |
| `derived_from` | `audyt_systemu_2026-08-06` |
| `evidence` | rozmiary plików + log incydentów |

Przeszedł przez bramkę zapisu. Licznik 613 → 614.

**To pierwszy wpis w tej bazie, który nie jest echem systemu, tylko faktem wyciągniętym z wykonanego zadania.**

---

## 7. Czyszczenie bloków-śmieci

**Wykonane 2026-08-06, trzy etapy, wszystko odwracalne.**

Pliki **przeniesione, nie skasowane** — `aions_core/memory/chunks_quarantine/`.

### Przebieg

| Etap | Bloków | Kryterium |
|---|---:|---|
| 1 | 3 | zero referencji przychodzących |
| 2 | 399 | wskazywane wyłącznie przez inne śmieci |
| 1 (ponownie) | 2 | osierocone po etapie 2 |
| 3 | 51 | wskazywane też przez prawdziwą wiedzę |
| **razem** | **455** | |

### Stan

| | Przed | Po |
|---|---:|---:|
| Plików bloków | 622 | 167 |
| `total_chunks` | 614 | 159 |
| W kwarantannie | 0 | 455 |

Dwa pojęcia straciły wszystkich członków i zniknęły z `concept_map`: `conversation_summary`, `desktop_files_analysis`. Oba były w całości śmieciowe.

### Efekt — pomiar na 10 zapytaniach

| | Przed czyszczeniem | Po czyszczeniu |
|---|---:|---:|
| **Śmieci w pierwszych 15** | **44,0%** | **0,0%** |
| **Prawdziwa wiedza w pierwszych 15** | ~53% | **96,7%** (145/150) |
| Mediana czasu | 10,3 ms | **7,6 ms** |
| Wyników na zapytanie | ~33 | 29 |

Zapytanie „chunki wiedzy" — przed czyszczeniem **15/15 śmieci, zero prawdziwej wiedzy** — po czyszczeniu **15/15 prawdziwej wiedzy**.

### Dlaczego etap 3 mimo ryzyka

Etap 3 oznaczał, że 14 bloków prawdziwej wiedzy straci referencje. Decyzja: **wykonać**, bo:

1. **Referencja z prawdziwej wiedzy do śmiecia sama jest śmieciem.** Blok nie traci treści, tylko wskaźnik na coś, co nie powinno było powstać.
2. System już tolerował zwisające referencje (463 sztuki po etapie 2) bez żadnych błędów — `retrieve_chunk()` zwraca `None`, wywołujący to obsługują.
3. W etapie 3 był blok **`K5BFE2E3E256C`** — zawierający otwartym tekstem klucz API OpenAI, hasło i parę e-mail+hasło, **aktywnie zwracany przez wyszukiwanie** przy zwykłych pytaniach. To był argument rozstrzygający.

Po etapie 3 ten blok **nie jest już w żywej pamięci**. Leży w kwarantannie — nadal wymaga unieważnienia poświadczeń, ale przestał wychodzić w odpowiedziach.

### Efekt uboczny — graf się rozpadł

| | Przed | Po |
|---|---:|---:|
| Składowych spójnych | 45 | 87 |
| Największa składowa | 92,9% węzłów | 60,9% |
| Węzłów izolowanych | 44 | 86 |

Usunięcie bloków-hubów (jeden miał 446 referencji) zerwało spoiwo, które sztucznie łączyło bazę w jedną całość. **To spoiwo było śmieciem** — ale oznacza, że rozwijanie po grafie ma teraz mniejszy zasięg. Bez znaczenia dopóki `AIONS_GRAPH_EXPAND=0`; do ponownej oceny przed włączeniem.

### Jak cofnąć

```
python _measure/restore_quarantine.py --list
python _measure/restore_quarantine.py --run-id <id> --execute
python _measure/restore_quarantine.py --all --execute
```

Pełna kopia sprzed czyszczenia: `backups/cbms_20260806_pre_quarantine/` (622 pliki + manifest).
Kopie per-etap: `_measure/quarantine_backups/<znacznik>/`.

---

## Znane, nienaprawione

| # | Rzecz | Skutek |
|---|---|---|
| 1 | **Haki gita zepsute** — `cd: too many arguments`, spacja w „server wiedzy" rozbija ścieżkę w `pre-commit`, `prepare-commit-msg`, `commit-msg`, `post-commit` | haki nie działają; ta sama klasa błędu co naprawiona w `8000ad9` dla zadań harmonogramu |
| 2 | **455 bloków-śmieci nadal w bazie** | 61% wyników wyszukiwania i 44% pierwszych 15 to śmieć. Skrypty kwarantanny gotowe w `_measure/`, nieuruchomione |
| 3 | **Operator nie ma kanału wyjściowego** | wie o problemach i nie ma jak powiedzieć. Gotowy skill `sys.notify` istnieje i działa, nie jest podłączony |
| 4 | **Operator nie czyta pamięci** | opiera się wyłącznie na twardych progach. Gdyby sprawdzał pamięć, sam wykryłby, że alarm o F: jest fałszywy |
| 5 | **266 plików „zmodyfikowanych" to szum końców linii** | `git status` jest nieczytelny. Brak `.gitattributes` z normalizacją |
| 6 | **`aions_execute_step` zna 4 narzędzia z 87** | plan powstaje i nie da się go wykonać przez MCP |

---

## Jak cofnąć wszystko

```
# 1. Wyłączniki (bez ruszania kodu):
AIONS_WRITE_GATE=0
AIONS_RETRIEVAL_LIMIT=0
AIONS_GRAPH_EXPAND=0        # już domyślnie

# 2. Wykluczenia dyskowe:
usuń control_plane/operator/disk_overrides.json

# 3. Pełne cofnięcie kodu:
git revert 53c7609
# albo z kopii zapasowych:
_backups/aions_core_server__cbms_memory.py.bak-pre-write-gate-20260804
_backups/control_plane_operator__loop.py.bak-pre-disk-overrides-20260806
```

**Uwaga:** cofnięcie kodu nie usunie bloku `KE2969827A76F` ani nie odtworzy zarchiwizowanego logu incydentów. To dane, nie kod.

---

## Pomiary

Wszystkie liczby w tym dokumencie pochodzą z plików w `_measure/` (nieśledzone w git, zawierają podglądy treści bloków):

| Plik | Zawiera |
|---|---|
| `baseline_2026-08-04.json` | stan przed zmianami, 10 zapytań |
| `after_OFF_/after_ON_2026-08-04.json` | test odwracalności limitów |
| `graph_OFF_/graph_ON_/graph_SUP3_2026-08-04.json` | test rozwijania grafu |
| `chunk_classification.json` | klasyfikacja wszystkich 621 bloków |
| `gate_test_report.txt` | testy bramki zapisu |
| `risk_analysis.json`, `search_simulation.json` | analiza czyszczenia |

---

## 8. Haki gita — usunięcie martwego husky po edytorze Kiro

**Objaw:** każda operacja gita wypisywała `cd: too many arguments`.

**Przyczyna.** W `.git/hooks/` leżało 18 haków wygenerowanych przez **husky 0.13.4**, wszystkie datowane 17.12.2025, każdy z linią:

```sh
cd tu huje/.kiro/Kiro/resources/app
```

Ścieżka zawiera spację i nie jest w cudzysłowach, więc `cd` dostaje dwa argumenty i przerywa.

**Po co powstały (sprawdzone przed usunięciem).** Nie powstały dla AIONS. To produkt uboczny instalacji edytora **Kiro** — husky przy instalacji wpisał własny katalog roboczy do haków tego repozytorium. Haki husky uruchamiają `npm run <skrypt>` z `package.json`. W `E:\server wiedzy` **nie ma `package.json`** i nigdy nie było — to repozytorium jest pythonowe. Wskazywany katalog `tu huje/.kiro/Kiro/resources/app` również tu nie istnieje.

**Czy blokowały commity — nie.** Zmierzone bezpośrednio:

```
sh .git/hooks/pre-commit  →  kod wyjścia 0
```

`cd` zawodzi, ale powłoka idzie dalej; `has_hook_script precommit` sprawdza `[ -f package.json ]`, dostaje fałsz i hak kończy się przez `exit 0`. Były wyłącznie hałasem na wyjściu błędów, nie przeszkodą. Wcześniejsze commity robione z `--no-verify` były zabezpieczone nadmiarowo.

**Dlaczego mimo to usunięte.** To mina: gdyby w repozytorium kiedykolwiek pojawił się `package.json` ze skryptem `precommit`, 18 haków zaczęłoby próbować uruchamiać `npm` z katalogu, którego nie ma.

**Działanie.** Przeniesione (nie skasowane) do `.git/hooks_disabled_husky_kiro_20260807/`. Pozostały wyłącznie pliki `.sample` — domyślne wzorce gita, bezczynne z definicji.

| | przed | po |
|---|---:|---:|
| aktywne haki | 18 | 0 |
| pliki `.sample` | 14 | 14 |

**Cofnięcie:**
```bash
mv "E:/server wiedzy/.git/hooks_disabled_husky_kiro_20260807/"* "E:/server wiedzy/.git/hooks/"
```

**Uwaga:** `.git/` nie jest śledzony przez gita, więc ta zmiana nie ma commita — istnieje tylko lokalnie i ten wpis jest jej jedynym śladem.

**Niezałatwione, powiązane:** `docs/CBMS_HUMAN_GUIDE.md` pokazuje 132 wstawienia i 132 usunięcia bez zmiany treści — to różnica w znakach końca linii (CRLF/LF). Wymaga `.gitattributes`. Ujęte w zaległych drobnych naprawach.
