# CHROMA UPGRADE PLAN — AIONS / Serwer Wiedzy

- **Autor:** sesja Cursor (subagent), prototyp na D:, kanon na E:
- **Data:** 2026-07-10
- **Status:** Root cause POTWIERDZONY na izolowanej kopii D:. Fix zweryfikowany (2 warianty PASS). Promocja na prod = do zatwierdzenia przez Marcina.
- **Zasada bezpieczeństwa tej sesji:** prod Chroma `E:\server wiedzy\data\chroma` **nie był modyfikowany** — cała diagnostyka i testy szły na kopii `D:\AIONS_DEV\chroma_prototype\`.

---

## 1. Root cause (błąd "compaction") + rekomendowana naprawa

### 1.1. Objaw
Przy tier-2 ingest (`scripts/ingest_treasures_tier2.py`) leciał:

```
chromadb.errors.InternalError: Error in compaction: Error reading from metadata
segment reader: error occurred while decoding column 0: mismatched types;
Rust type `u64` (as SQL type `INTEGER`) is not compatible with SQL type `BLOB`
```

Odtworzone 1:1 na kopii D: (`python scripts/ingest_treasures_tier2.py`, system Python).

### 1.2. Przyczyna źródłowa — KONFLIKT WERSJI chromadb
Zmierzone w trzech środowiskach:

| Środowisko | Python | chromadb | Silnik |
|---|---|---|---|
| **Prod venv** `E:\server wiedzy\venv` | 3.11.9 | **0.5.3** | czysty Python (sqlite + hnswlib) |
| **System Python** `C:\Users\User\AppData\Local\Programs\Python\Python311` | 3.11.9 | **1.3.7** | **Rust bindings** (`chromadb/api/rust.py`) |
| `D:\AIONS_DEV\venv` (Windows) | — | — | nie istnieje |

- Baza `data/chroma` została utworzona i zapisana przez **chromadb 0.5.x** — potwierdzone układem na dysku: ~107 katalogów-segmentów HNSW (`<uuid>/`) + `chroma.sqlite3` (8,5 MB), tabele `embeddings_queue` (WAL), `max_seq_id`, `segments` w schemacie 0.5.x.
- W formacie 0.5.x kolumna `seq_id` (w `max_seq_id`/segment reader) jest trzymana jako **BLOB**.
- chromadb **1.3.7** ma przepisany rdzeń w **Rust**. Jego "compaction" (materializacja WAL → segment) czyta metadane segmentu i oczekuje `seq_id` jako **INTEGER (u64)**. Trafia na BLOB → `InternalError` przy pierwszym zapisie.
- tier-1 ingest zadziałał 2026-07-03, bo **wtedy poszedł przez prod venv 0.5.3**. Błąd pojawił się, gdy tier-2 uruchomiono przez **bare `python`** (system 1.3.7).

**Wniosek:** to nie jest uszkodzona baza ani zły segment/hnswlib. To niekompatybilność formatu on-disk 0.5.x (BLOB) vs silnik Rust 1.x (INTEGER). Baza prod jest zdrowa.

### 1.3. Rekomendowana naprawa (WYBRANY WARIANT: a)
**Zawsze uruchamiaj ingest/write przez prod venv 0.5.3 (nigdy przez system Python 1.3.7).**
Nie trzeba przebudowywać prod bazy — jest zdrowa i w dobrym formacie. Wystarczy powtórzyć tier-2 ingest właściwym interpreterem.

Dodatkowo (zrobione w tej sesji): **guard `chromadb.__version__`** w skryptach ingest — twardo odmawia zapisu, jeśli `!= 0.5.x`, z czytelnym komunikatem. Dzięki temu przypadkowe `python skrypt.py` już nie uszkodzi/nie wywali bazy, tylko grzecznie odmówi.

---

## 2. Wyniki prototypu D: (co przetestowano)

Katalog roboczy: `D:\AIONS_DEV\chroma_prototype\`
- `chroma_copy\` — kopia prod (robocopy, 333 pliki / 138 MB, źródło E: read-only)
- `chroma_rebuild\` — świeża baza zbudowana od zera
- `inspect_db.py`, `verify_treasures.py` — narzędzia diagnostyczne

| Test | Interpreter | Wynik |
|---|---|---|
| Odtworzenie błędu compaction | system 1.3.7 | **błąd odtworzony** (zgodnie z prod) |
| **Wariant a**: re-ingest tier-2 do istniejącej kopii | prod venv 0.5.3 | **PASS** (aions_operator 2→3, claude_marcin_main 584→598, +15 embeddingów zmaterializowanych) |
| **Wariant b**: rebuild od zera (tier-1 + tier-2, świeża baza) | prod venv 0.5.3 | **PASS** (tier-1: 2+40, tier-2: 1+14, bez błędów, baza czysta) |
| Guard blokuje system Python | system 1.3.7 | **PASS** (odmowa przed zapisem, brak crasha) |
| Recall treasures ("gdzie jest plasters_200g") | prod venv 0.5.3 | **PASS** — top hity to `plasters_200g` / `ajajaj_plasters_200g` / `plasters_unified`; `chroma_prod`, `ajajaj_root`, `catalog_index` też trafiają |

**PROTOTYP D: = PASS.** Oba warianty naprawy działają; guard skutecznie zabezpiecza przed regresją.

> Uwaga jakościowa: bezwzględne score są niskie (~0,2–0,34), bo model to `all-MiniLM-L6-v2` (angielski, 384-dim) a zapytania są PL, plus konwersja `score = 1 - distance`. **Ranking jest poprawny** (treasure na górze). Model embeddingów → punkt 3.2.

---

## 3. Docelowa architektura Chromy pod AIONS

### 3.1. Kolekcje (schemat docelowy)
Store dzisiaj mapuje sesje na kolekcje `session_<id>` (`server/store.py::VectorStore`). Docelowo świadomie utrzymywane logiczne zbiory:

| Kolekcja (nazwa store) | Zawartość | Tier | ttl_days |
|---|---|---|---|
| `aions_operator` | profil operatora + indeksy (CBMS tier-1 index, treasure index) | tier-1/2 | 365 |
| `claude_marcin_main` | pamięć główna: metadane CBMS, treasures, autolog/summaries | tier-1/2/3 | 30–365 |
| `cbms_chunks` (docelowo) | osobna kolekcja na metadane 562 chunków CBMS (dziś wrzucane do main) | tier-1 | 365 |
| `treasures_index` (docelowo) | 14 skarbów z `catalog_2026.json` jako osobna kolekcja (dziś w main+operator) | tier-2 | 365 |
| `conversations` / `autolog_*` | dumpy rozmów, auto-log | tier-3 | 30 |

Rekomendacja: **wydzielić `cbms_chunks` i `treasures_index`** z `claude_marcin_main`, żeby recall pamięci roboczej nie mieszał się z katalogiem (znany problem: "memory_recall miesza CBMS nad Chroma session docs").

### 3.2. Schema metadanych
Znormalizowana w `server/context_schema.py::normalize_metadata`:
`agent, role, source, tags (CSV), ttl_days, timestamp, expires_at` + pola extra (np. `treasure_id, path, treasure_type, status, size_gb`). Listy/obiekty są serializowane do stringów (wymóg Chromy). To jest OK — zostawić.

### 3.3. Model embeddingów
`server/store.py` **nie ustawia** `embedding_function` → chromadb 0.5.x używa **domyślnego `ONNXMiniLM_L6_V2` = all-MiniLM-L6-v2 (384-dim, ONNX)**. (`tools/ChromaFlowStudio` pinuje `chromadb==0.5.20` — ta sama linia 0.5.x.)
Rekomendacja: **zostać na all-MiniLM-L6-v2 na razie** (spójność z istniejącą bazą — zmiana modelu wymusza pełny re-embedding wszystkich kolekcji). Jeśli PL recall ma być mocniejszy → rozważyć w osobnym zadaniu model wielojęzyczny (np. `paraphrase-multilingual-MiniLM-L12-v2`) z pełnym rebuildem, nigdy w locie.

---

## 4. Wersjonowanie — jak uniknąć konfliktu system vs venv

1. **Pin już jest:** `requirements.txt` i `requirements-linux.txt` → `chromadb==0.5.3`. Utrzymać. NIE podbijać do 1.x bez świadomej migracji (punkt 6).
2. **Guard w skryptach ingest (ZROBIONE):** `ingest_tier1_chroma.py` i `ingest_treasures_tier2.py` mają `_assert_chroma_version()` — odmowa gdy `chromadb.__version__` nie zaczyna się od `0.5`.
3. **Zawsze prod venv:** uruchamiaj przez `scripts\aions_python.ps1` (rozwiązuje interpreter z `.aions\python.env` → `E:\server wiedzy\venv`, wymusza Python 3.11). **Nigdy `python skrypt.py`.**
4. **Opcjonalnie:** rozważyć odinstalowanie/izolację globalnego chromadb 1.3.7 z system Pythona, żeby nie kusił. Minimum: guard + dyscyplina wrappera.

---

## 5. Backup / restore dla `data/chroma`

- **Backup (przed każdą operacją zapisu na prod):**
  ```powershell
  $ts = Get-Date -Format "yyyyMMdd_HHmmss"
  robocopy "E:\server wiedzy\data\chroma" "E:\server wiedzy\backups\chroma_$ts" /E /R:1 /W:1
  ```
  (baza to ~138 MB / 333 pliki — tanie).
- **Restore:** zatrzymać MCP/procesy trzymające bazę → usunąć `data\chroma` → robocopy z backupu z powrotem.
- **Ważne:** przy backupie/restore **żaden proces (MCP server) nie może trzymać otwartego `chroma.sqlite3`** (blokada + WAL). Najpierw zatrzymać serwer AIONS MCP.
- `sync_dev_mirror.ps1` **celowo wyklucza `data\chroma`** — dev mirror nie kopiuje bazy (dobrze).

---

## 6. Decyzja strategiczna: zostać na 0.5.3 vs migracja do 1.3.7

**Rekomendacja: ZOSTAĆ na chromadb 0.5.x (0.5.3).**

| Kryterium | 0.5.3 (obecne) | Migracja do 1.3.7 |
|---|---|---|
| Kompatybilność z istniejącą bazą | pełna (format on-disk 0.5.x) | wymaga migracji formatu (BLOB→INTEGER); brak gwarantowanego bezstratnego migratora dla tej bazy |
| Ryzyko | niskie (znane, działa, tier-1+tier-2 PASS) | wysokie — 123 kolekcje, 741 embeddingów, ryzyko utraty/uszkodzenia |
| Koszt | zerowy | pełny re-embedding + walidacja wszystkich kolekcji |
| Zysk | — | nowszy silnik Rust (szybszy przy dużej skali), ale AIONS jest mały (0,14 GB) |

Uzasadnienie: skala jest mała, 0.5.3 działa i jest zapinowany. Migracja do 1.x to duże ryzyko dla zerowego realnego zysku **teraz**. Jeśli kiedyś skala urośnie i 1.x będzie potrzebny → migracja przez **rebuild od zera** (wariant b, sprawdzony) do nowej bazy 1.x, z re-ingest z odtwarzalnych źródeł (manifest CBMS + `catalog_2026.json`), a nie in-place upgrade.

---

## 7. Jak Chroma wspiera rozwój projektu

- **Memory-first recall:** `session_bootstrap` / `memory_recall` na starcie sesji — protokół AIONS. Chroma = warstwa pamięci długoterminowej agenta.
- **Treasure lookup:** tier-2 (`treasures_index`) odpowiada "gdzie jest X" (plasters_200g, AJAJAJ backup, CBMS_INDEX_FULL) bez skanowania dysku — metadane, nie binaria.
- **Tiery ingest:**
  - tier-1 = profil operatora + indeks CBMS (kanon operacyjny),
  - tier-2 = katalog skarbów (lokalizacje danych),
  - tier-3 = rozmowy/autolog (krótki ttl).
- **Scheduler:** okresowy `prune_expired` (jest w store) + odświeżanie tier-2 po zmianie `catalog_2026.json` (re-run `ingest_treasures_tier2.py` przez prod venv).
- **Przyszłe zmysły:** nowe źródła (pliki, web, desktop) ingestują metadane do dedykowanych kolekcji tym samym, bezpiecznym torem 0.5.x + guard.

---

## 8. Bezpieczna promocja prototyp D: → prod E:

Prod baza jest zdrowa, więc promocja = **wykonać brakujący tier-2 ingest na prod właściwym interpreterem**, nie kopiować bazy z D:.

1. Zatrzymać AIONS MCP server (zwolnić blokadę `chroma.sqlite3`).
2. **Backup prod** (punkt 5).
3. Uruchomić na prod przez prod venv:
   ```powershell
   cd "E:\server wiedzy"
   .\scripts\aions_python.ps1 scripts\ingest_treasures_tier2.py
   ```
   (guard przepuści tylko 0.5.x; CHROMA_PATH domyślnie = `data/chroma`).
4. Zweryfikować recall na prod (analogicznie do `verify_treasures.py`, prod venv).
5. Wystartować MCP server; sanity `memory_recall("claude_marcin_main","gdzie jest plasters_200g")`.
6. Gdyby coś poszło źle → restore z backupu (punkt 5).

Rebuild całości (wariant b) tylko jako plan awaryjny, gdyby prod baza była uszkodzona.

---

## 9. Konkretne następne kroki (ponumerowane)

1. **[zrobione]** Guard `chromadb.__version__` w obu skryptach ingest.
2. **[do zatwierdzenia przez Marcina]** Promocja tier-2 na prod wg punktu 8 (backup → `aions_python.ps1 ingest_treasures_tier2.py` → weryfikacja). **Nie zrobione w tej sesji — prod nietknięty zgodnie z zasadami.**
3. Sprawdzić, czym MCP server (v6) odpala Pythona — upewnić się, że używa prod venv 0.5.3, nie system 1.3.7.
4. (Higiena) Rozważyć usunięcie/izolację globalnego `chromadb 1.3.7` z system Pythona.
5. (Architektura) Wydzielić `cbms_chunks` i `treasures_index` jako osobne kolekcje (mniej szumu w `claude_marcin_main`).
6. (Ops) Dodać do schedulera: backup `data/chroma` + `prune_expired` + odświeżanie tier-2 po zmianie katalogu.
7. (Opcjonalnie, osobne zadanie) Ewaluacja modelu wielojęzycznego dla PL recall — tylko z pełnym rebuildem.

---

## Załącznik: artefakty prototypu (D:, do usunięcia po akceptacji)
- `D:\AIONS_DEV\chroma_prototype\chroma_copy\` — kopia prod po testach wariantu a
- `D:\AIONS_DEV\chroma_prototype\chroma_rebuild\` — świeży rebuild (wariant b)
- `D:\AIONS_DEV\chroma_prototype\inspect_db.py`, `verify_treasures.py`
