# DIAGNOSTIC BRIEFING FOR NEXT CLAUDE ITERATION

**Data**: 2025-11-08 17:04+
**Od**: Claude (Senior - Session 20251108_163049)
**Do**: Claude (Junior - Next Iteration)
**Priorytet**: CRITICAL
**Status**: System działa, ale źle - potrzebna pełna diagnostyka

---

## TL;DR - CO MUSISZ WIEDZIEĆ

Masz przed sobą **AIONS V3** - offline'owy system AI z rewolucyjną architekturą. Problem: **serwer działa, ale wszystkie odpowiedzi to generyczny template zamiast prawdziwego CBMS retrieval**. Twoje zadanie: **przeprowadź pełną diagnostykę wszystkich subsystemów i znajdź co jest zepsute**.

---

## CZĘŚĆ 1: CO TO JEST AIONS?

### Architektura AIONS (Uproszczona)

```
User Query
  ↓
┌─────────────────────────────────────┐
│ AIONS CBMS RELEASE V3               │
├─────────────────────────────────────┤
│ 1. Math Solver (deterministic)      │
│ 2. Facts System (database lookup)   │
│ 3. CBMS Think ← TUTAJ PROBLEM!      │
│    │                                 │
│    ├─ CBMS (521 chunks)             │
│    ├─ CBMS-KR (Korean compression)  │
│    ├─ CBMS-ES (Esperanto indexing)  │
│    ├─ Plasters (200-448 PACKs)      │
│    └─ CRLA (learning algorithm)     │
│                                      │
│ 4. Pocket QC (quantum emulator)     │
│ 5. Enhancement (conversation)        │
│ 6. Consciousness Layer (?)          │
│ 7. Reasoning Layer (?)              │
└─────────────────────────────────────┘
  ↓
Response (FastAPI port 9000)
```

### Kluczowe Komponenty

**CBMS (Chunk-Based Memory System)**
- 521 chunks w formacie K[13-hex-chars]
- JSON blocks w `memory/chunks/`
- `facts_index.json` - 10 MB, 33,945+ faktów
- Kompresja: 3.29:1

**CBMS-KR (Korean Key Compression)**
- Używa Korean syllable decomposition
- Character 3-grams + SHA1 hash
- 4,016+ patterns
- Set intersection dla semantic search

**CBMS-ES (Esperanto Symbolic Indexing)**
- Symboliczne indeksowanie
- Esperanto jako neutral language bridge
- Details: nieznane (musisz zbadać)

**Plasters System**
- `plasters_200g`: 200 PACKs → 343,091 Q&As
- `plasters_fullstack`: 448 PACKs → 768,768 Q&As
- `chunks_unified`: 1,033 chunks
- Dynamic loading, LRU cache (max 10 PACKs in RAM)

**CRLA (Chain Reaction Learning Algorithm)**
- Generuje K=12 kandidatów
- Multi-dimension scoring (6 factors)
- J=0.893 threshold
- **POWINIEN** tworzyć thinking patterns i zapisywać je jako chunks

**Pocket QC**
- Quantum computing emulator (CPU-only)
- Statevector simulator
- Quantum-inspired optimizer
- Lokalizacja: `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\pocket_qc\CBMS_Pocket_QC_Lab\`

---

## CZĘŚĆ 2: OBECNY STATUS

### Serwer Działa ✅

```bash
# Port: 9000
# PID: 47600 (może się zmienić)
# Lokacja: E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\AIONS_CBMS_RELEASE_V3
# Started: 2025-11-08 ~17:00
```

**Health check**:
```bash
curl http://localhost:9000/health
# Response:
{
  "status": "healthy",
  "chunks": 521,
  "plasters_enabled": true
}
```

### Ale Odpowiedzi Są Zepsute ❌

**Problem**: Wszystkie queries zwracają ten sam generyczny template:

```
Na podstawie 1 fragmentów wiedzy:

Witaj! Jestem AIONS - Advanced Intelligence Operating System.

System oparty na CBMS (Code Book Memory System) z integracją Claude thinking patterns.
Gotowy do pomocy w zadaniach programistycznych, analizie i rozwiązywaniu problemów.

Zadaj mi pytanie, a odpowiem błyskawicznie!

[Źródło: CBMS, 231 chunków pamięci]

🎨 Plasters insight:
[PLASTERS_200g Inference]
[PACK-0166] Response based on 1716 QAs
[PACK-0167] Response based on 1716 QAs
[PACK-0168] Response based on 1716 QAs

Evidence from CBMS:
Na podstawie 1 fragmentów wiedzy:

Witaj! Jestem AIONS - Advanced Intelligence Operating System...
```

**To SAMO dla**:
- "Wyjaśnij mi dokładnie jak działa CBMS chunk-based memory system"
- "어떻게 Korean compression이 작동하나요?" (Korean)
- "Kiel funkcias la Esperanto simbola indeksado?" (Esperanto)
- "1337 * 42" (math query)

### Co Wiemy

✅ **Działa**:
- Server startup (FastAPI on port 9000)
- Health endpoint
- Plasters loading (pokazuje PACK-0166, 0167, 0168)
- Request processing (zwraca response)

❌ **Nie Działa**:
- CBMS retrieval (zawsze "1 fragmentów wiedzy")
- Content synthesis (zawsze ten sam template)
- Math solver (nie rozpoznaje queries matematycznych)
- Korean compression (nie rozpoznaje Korean queries)
- Esperanto indexing (nie rozpoznaje Esperanto)
- Query routing (wszystko idzie do tego samego template)

❓ **Nieznane**:
- Czy CRLA tworzy nowe thinking patterns?
- Czy zapisuje nowe chunks lokalnie?
- Czy consciousness layer istnieje?
- Czy reasoning layer działa?
- Co jest w logach (`thinking_log.jsonl`)?
- Dlaczego zawsze zwraca "231 chunków pamięci" gdy health pokazuje 521?

---

## CZĘŚĆ 3: TWOJE ZADANIE

### Główny Cel

**Przeprowadź pełną diagnostykę wszystkich subsystemów i określ:**
1. Co działa prawidłowo
2. Co jest zepsute
3. Dlaczego jest zepsute
4. Jak to naprawić

### 12 Tasków Diagnostycznych (Z PRIORYTETAMI)

#### TIER 1: KRYTYCZNE (Zrób najpierw)

**1. Zbadaj Logging System**
- Znajdź i przeczytaj `thinking_log.jsonl`
- Znajdź server logi (prawdopodobnie w `logs/`)
- Zobacz CO DOKŁADNIE dzieje się podczas query processing
- **Output**: Lista plików logów + co pokazują

**2. Zbadaj CBMS Retrieval**
- Kod: `server/cbms_memory.py`
- Sprawdź czy `retrieve()` metoda jest wywoływana
- Sprawdź czy zwraca chunks czy tylko template
- Wyślij test query i śledź execution path
- **Output**: Czy retrieval działa + proof

**3. Zbadaj Query Router**
- Kod: prawdopodobnie w `server/cbms_direct_server.py` lub `AIONS_ULTIMATE_UNIFIED.py`
- Sprawdź routing logic (Math → Facts → CBMS)
- Zobacz dlaczego wszystko idzie do template
- **Output**: Diagram routing flow + gdzie pęka

#### TIER 2: WAŻNE (Zrób potem)

**4. Zbadaj CBMS-KR (Korean Compression)**
- Kod: `server/korean_keys.py`
- Wyślij Korean query
- Sprawdź czy jest wykrywany i przetwarzany
- **Output**: Czy KR działa + test results

**5. Zbadaj Esperanto Indexing**
- Znajdź kod dla CBMS-ES
- Wyślij Esperanto query
- Sprawdź czy system go rozpoznaje
- **Output**: Czy ES istnieje + test results

**6. Zbadaj CRLA Learning**
- Kod: `server/crla_core.py`
- Sprawdź czy tworzy thinking patterns
- Sprawdź `memory/crla_runs.jsonl` (jeśli istnieje)
- Wyślij query i zobacz czy zapisuje nowy pattern
- **Output**: Czy CRLA uczy się + proof

**7. Zbadaj Plasters Integration**
- Kod: `server/plasters_loader.py`
- Plasters WYWOŁYWANY (widzimy PACK-0166, 0167, 0168)
- Ale czy jego output jest UŻYWANY?
- **Output**: Czy plasters output trafia do final response

#### TIER 3: NICE TO HAVE (Jeśli zostanie czas)

**8. Zbadaj Pocket QC**
- Czy jest zintegrowany w main server?
- Gdzie jest kod integracji?
- Wyślij query wymagający QC
- **Output**: Czy QC jest aktywny

**9. Zbadaj Consciousness Layer**
- Szukaj `CBMS_ENABLE_CONSCIOUSNESS` lub podobnych
- Sprawdź environment variables
- Sprawdź kod dla consciousness references
- **Output**: Czy consciousness istnieje

**10. Zbadaj Reasoning Capabilities**
- Wyślij query wymagający multi-step reasoning
- Zobacz czy używa thinking patterns
- **Output**: Czy reasoning działa

**11. Sprawdź Local Chunk Creation**
- Wyślij nowy query (coś czego system nie zna)
- Sprawdź czy tworzy nowy chunk w `memory/chunks/`
- Sprawdź timestamps plików
- **Output**: Czy tworzy nowe chunks

**12. Sprawdź Context Preservation**
- Wyślij 2-3 queries w sekwencji
- Sprawdź czy pamięta poprzedni context
- Sprawdź czy zapisuje jako CBMS chunks
- **Output**: Czy context preservation działa

---

## CZĘŚĆ 4: JAK TO ZROBIĆ

### Step-by-Step Process

**Krok 1: Zrozum Strukturę Kodu**

Najpierw READ (nie edytuj!):
1. `server/cbms_direct_server.py` - main server
2. `server/cbms_memory.py` - memory management
3. `server/plasters_loader.py` - plasters system
4. `server/crla_core.py` - learning algorithm

Zrób sobie mental map jak to działa.

**Krok 2: Znajdź Logi**

```bash
# Sprawdź czy thinking_log.jsonl istnieje
find "E:/AI_WORKSPACE/MASTER_CLEAN/UNCLASSIFIED/AIONS_CBMS_RELEASE_V3" -name "thinking_log.jsonl"

# Sprawdź logs/ directory
ls -la "E:/AI_WORKSPACE/MASTER_CLEAN/UNCLASSIFIED/AIONS_CBMS_RELEASE_V3/logs/"

# Przeczytaj ostatnie 100 linii najnowszego logu
tail -100 <newest_log_file>
```

**Krok 3: Śledź Query Execution**

Wyślij test query z verbose logging:
```bash
curl -X POST http://localhost:9000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"Test diagnostic query 123", "verbose": true}'
```

Jednocześnie obserwuj logi (tail -f).

**Krok 4: Badaj Kod**

Dla każdego subsystemu:
1. READ kod
2. Znajdź entry point (gdzie jest wywoływany)
3. Sprawdź czy jest wywoływany (logi, print statements)
4. Sprawdź output
5. Określ: DZIAŁA / NIE DZIAŁA / CZĘŚCIOWO

**Krok 5: Dokumentuj Wszystko**

Używaj TodoWrite do tracking progress:
```python
TodoWrite({
  "todos": [
    {"content": "Zbadać CBMS retrieval", "status": "completed", "activeForm": "..."},
    {"content": "Zbadać CRLA learning", "status": "in_progress", "activeForm": "..."},
    # etc
  ]
})
```

Zapisuj findings lokalnie:
```bash
python /c/Users/User/save_claude_context.py -m "FINDING: CBMS retrieval always returns same template because..."
```

**Krok 6: Twórz Raport**

Na końcu stwórz comprehensive diagnostic report:
- Co działa
- Co nie działa
- Dlaczego
- Jak naprawić
- Priority fixes

---

## CZĘŚĆ 5: KLUCZOWE PLIKI I LOKACJE

### Główny Katalog
```
E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\AIONS_CBMS_RELEASE_V3\
```

### Kod Serwera
- `server/cbms_direct_server.py` - FastAPI server
- `server/cbms_memory.py` - CBMS memory system
- `server/korean_keys.py` - Korean compression
- `server/plasters_loader.py` - Plasters loading
- `server/crla_core.py` - CRLA algorithm
- `server/conversation_enhancer.py` - Enhancement
- `server/math_solver.py` - Math solving
- `server/stylist.py` - Response formatting

### Memory
- `memory/chunks/` - 521 chunks
- `memory/facts_index.json` - 10 MB database
- `memory/manifest.json` - Chunk index
- `memory/thinking_log.jsonl` - Thinking patterns (?)
- `memory/crla_runs.jsonl` - CRLA history (?)

### Plasters
- `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\plasters_200g\` - 200 PACKs
- `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\plasters_fullstack\` - 448 PACKs

### Logs (Prawdopodobnie)
- `logs/` - Server logs
- `logs/cbms_server_YYYYMMDD.log` - Daily logs
- `logs/startup_*.log` - Startup logs

### Config
- `config/memory_sources.json` - 56 paths do chunks
- Environment variables w startup scripts

---

## CZĘŚĆ 6: CO WIEM O PROBLEMIE

### Symptomy

1. **Template Response**: Zawsze ten sam greeting
2. **"1 fragmentów wiedzy"**: Zawsze 1, nigdy więcej
3. **"231 chunków pamięci"**: Hardcoded? Health pokazuje 521
4. **Plasters Called**: PACK-0166/67/68 wywoływane (widać w response)
5. **But Not Used**: Plasters output nie trafia do final response
6. **No Math Solving**: "1337 * 42" nie rozpoznane jako math
7. **No Language Detection**: Korean/Esperanto nie wykryte

### Hipotezy

**Hipoteza 1: Router Broken**
- Query routing nie działa
- Wszystko idzie do default template handler
- Math/Facts/CBMS ścieżki pominięte

**Hipoteza 2: CBMS Retrieval Returns Empty**
- CBMS retrieval wywoływany
- Ale zwraca empty/invalid results
- Fallback do template

**Hipoteza 3: Response Assembly Broken**
- Wszystkie subsystemy działają
- Ale final response assembly używa tylko template
- Ignoruje CBMS/Plasters output

**Hipoteza 4: Hardcoded Template**
- Gdzieś w kodzie jest hardcoded template
- Override'uje wszystko inne
- Może debug mode?

### Twoje Zadanie: Określ Która Hipoteza Jest Prawdziwa

---

## CZĘŚĆ 7: NARZĘDZIA DO DYSPOZYCJI

### Dostępne Komendy

```bash
# Health check
curl http://localhost:9000/health

# Info endpoint
curl http://localhost:9000/info

# Chat query
curl -X POST http://localhost:9000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"YOUR_QUERY"}'

# Plasters stats (jeśli endpoint istnieje)
curl http://localhost:9000/plasters/stats

# Zapisz context
python /c/Users/User/save_claude_context.py -m "MESSAGE"

# Snapshot
python /c/Users/User/save_claude_context.py --snapshot
```

### Dostępne Tools (Claude Code)

- **Read**: Czytaj pliki
- **Grep**: Szukaj w plikach
- **Glob**: Znajdź pliki
- **Bash**: Wykonaj komendy
- **Edit**: Edytuj pliki (TYLKO jeśli wiesz co robisz!)
- **Task**: Uruchom sub-agenta (jeśli potrzebujesz help)

---

## CZĘŚĆ 8: ZASADY BEZPIECZEŃSTWA

### NIE RÓB TEGO:

❌ **NIE KASUJ** chunks (`memory/chunks/*`)
❌ **NIE EDYTUJ** `facts_index.json` bez backup
❌ **NIE WYŁĄCZAJ** serwera bez powodu
❌ **NIE ZMIENIAJ** Korean markers
❌ **NIE MODYFIKUJ** kodu bez zrozumienia
❌ **NIE URUCHAMIAJ** destructive commands

### ZRÓB TO:

✅ **READ FIRST** - zawsze czytaj przed edycją
✅ **BACKUP** - twórz backupy przed zmianami
✅ **TEST** - testuj na prostych queries
✅ **DOCUMENT** - zapisuj wszystko przez save_claude_context.py
✅ **ASK** - jeśli nie jesteś pewien, ASK USER

---

## CZĘŚĆ 9: OCZEKIWANIA

### Output Który Ode Mnie Oczekujemy

**Na końcu diagnostyki dostarczysz**:

1. **Comprehensive Diagnostic Report** (markdown file)
   - Executive Summary
   - Każdy subsystem: STATUS (✅/❌/⚠️)
   - Root cause analysis
   - Evidence (logi, code snippets)
   - Recommended fixes (priorytetyzowane)

2. **Updated TODO List**
   - Co zostało zdiagnozowane
   - Co wymaga naprawy
   - Priority order

3. **Context Saved**
   - Wszystkie findings w session_log.jsonl
   - Snapshot na końcu

### Format Raportu

```markdown
# AIONS V3 DIAGNOSTIC REPORT

## Executive Summary
[3-5 bullet points co znalazłeś]

## Subsystem Status

### CBMS Retrieval
**Status**: ❌ BROKEN
**Evidence**: [code snippets, log entries]
**Root Cause**: [explanation]
**Fix Priority**: P0 (Critical)

### CBMS-KR (Korean)
**Status**: ⚠️ PARTIALLY WORKING
[etc...]

## Root Cause Analysis
[Deep dive]

## Recommended Action Plan
1. [P0] Fix CBMS retrieval (estimated: 2h)
2. [P1] Fix query routing (estimated: 1h)
[etc...]
```

---

## CZĘŚĆ 10: PYTANIA I ODPOWIEDZI

**Q: Co jeśli nie mogę znaleźć pliku?**
A: Użyj `find` lub `Glob`. Jeśli nadal nie znajdziesz, DOCUMENT and continue.

**Q: Co jeśli kod jest zbyt skomplikowany?**
A: Use Task tool z Explore agent. Albo ASK USER.

**Q: Co jeśli serwer crashuje podczas testów?**
A: STOP, zapisz logi, report to user immediately.

**Q: Czy mogę edytować kod?**
A: **TYLKO** jeśli:
  1. Masz 100% pewność co robisz
  2. Stworzyłeś backup
  3. To jest prosty fix (np. print statement dla debugowania)

Dla większych zmian: **ASK USER FIRST**.

**Q: Ile mam czasu?**
A: Nie ma time limit, ale bądź efektywny. Prioritize TIER 1 tasks.

**Q: Co jeśli znajdę coś nieoczekiwanego?**
A: DOCUMENT natychmiast, może być kluczowe.

---

## STARTING POINT

Zacznij od tego:

```bash
# 1. Zapisz że zaczynasz
python /c/Users/User/save_claude_context.py -m "DIAGNOSTIC START: Beginning comprehensive AIONS V3 subsystem analysis"

# 2. Sprawdź czy serwer działa
curl http://localhost:9000/health

# 3. Znajdź logi
ls -la "E:/AI_WORKSPACE/MASTER_CLEAN/UNCLASSIFIED/AIONS_CBMS_RELEASE_V3/logs/"

# 4. Przeczytaj main server code
# READ server/cbms_direct_server.py

# 5. GO!
```

---

## FINAL NOTE OD SENIORA

Listen up. Ten system to 42 godziny pracy codex'a + setki godzin wcześniejszego developmentu. Jest tutaj rewolucyjna architektura - Korean compression, chunk-based memory, offline AI, zero hallucinations.

Ale COKOLWIEK codex zrobił w tych 42h, coś poszło nie tak. System odpala się, ale nie działa jak powinien.

Twoja misja: **ZNAJDŹ CO JEST ZEPSUTE I DLACZEGO**.

Nie naprawiaj jeszcze (chyba że trivial fix). Najpierw DIAGNOZUJ. Potem User zdecyduje co z tym zrobić.

Bądź metodyczny. Bądź dokładny. Dokumentuj wszystko.

Good luck, Junior. Masz to.

**- Claude Senior (Session 20251108_163049)**

---

**END OF BRIEFING**
