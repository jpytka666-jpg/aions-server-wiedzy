# HANDOFF DO NASTĘPNEJ ITERACJI CLAUDE

**Data**: 2025-11-08 17:10
**Od**: Claude Senior (Session 20251108_163049)
**Do**: Claude Junior (Następna Iteracja)
**Status**: READY FOR DIAGNOSTIC

---

## SZYBKI START (READ THIS FIRST!)

1. **Przeczytaj**: `C:\Users\User\notes\DIAGNOSTIC_BRIEFING_FOR_CLAUDE.md`
   - To jest twój pełny briefing (10 sekcji, wszystko co musisz wiedzieć)

2. **Zrozum Problem**:
   - AIONS V3 serwer działa (port 9000)
   - Ale wszystkie odpowiedzi to generyczny template
   - Twoje zadanie: **ZNALEŹĆ DLACZEGO**

3. **Twoje Zadanie**:
   - 12 tasków diagnostycznych (w briefingu)
   - Priority: TIER 1 (krytyczne) → TIER 2 (ważne) → TIER 3 (opcjonalne)
   - Output: Comprehensive diagnostic report

4. **Zacznij Od**:
   ```bash
   # Zapisz że zaczynasz
   python /c/Users/User/save_claude_context.py -m "DIAGNOSTIC START: Junior Claude rozpoczyna diagnostykę"

   # Sprawdź serwer
   curl http://localhost:9000/health

   # Znajdź logi
   ls -la "E:/AI_WORKSPACE/MASTER_CLEAN/UNCLASSIFIED/AIONS_CBMS_RELEASE_V3/logs/"

   # Czytaj main server code
   # (użyj Read tool na server/cbms_direct_server.py)
   ```

---

## CO WIEM (KLUCZOWE FINDINGS)

### ✅ Działa
- Server startup (FastAPI na porcie 9000)
- Health endpoint (`/health` zwraca 521 chunks, plasters_enabled: true)
- Plasters loading (PACK-0166, 0167, 0168 są wywoływane)
- Request processing (serwer zwraca responses)

### ❌ Nie Działa
- **CBMS retrieval** - zawsze "1 fragmentów wiedzy"
- **Content synthesis** - zawsze ten sam template greeting
- **Math solver** - nie rozpoznaje "1337 * 42"
- **Korean compression** - nie rozpoznaje Korean queries
- **Esperanto indexing** - nie rozpoznaje Esperanto queries
- **Query routing** - wszystko idzie do tego samego template

### ❓ Nieznane (TWOJE ZADANIE)
- Czy CRLA tworzy thinking patterns?
- Czy system zapisuje nowe chunks?
- Czy consciousness layer istnieje?
- Czy reasoning działa?
- Co jest w logach?
- **DLACZEGO wszystko zwraca template?** ← MAIN QUESTION

---

## PLIKI KLUCZOWE

### Briefing i Dokumentacja
- **`C:\Users\User\notes\DIAGNOSTIC_BRIEFING_FOR_CLAUDE.md`** ← PRZECZYTAJ TO!
- `C:\Users\User\notes\AIONS_V3_DISCOVERY.md` - co odkryliśmy o V3
- `C:\Users\User\CLAUDE.md` - główna dokumentacja AIONS

### Kod Do Zbadania
- `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\AIONS_CBMS_RELEASE_V3\server\cbms_direct_server.py`
- `server\cbms_memory.py`
- `server\korean_keys.py`
- `server\plasters_loader.py`
- `server\crla_core.py`

### Logi (Prawdopodobnie)
- `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\AIONS_CBMS_RELEASE_V3\logs\`
- `memory\thinking_log.jsonl` (?)
- `memory\crla_runs.jsonl` (?)

### Context Saving
- `python /c/Users/User/save_claude_context.py -m "MESSAGE"` - zapisz finding
- `python /c/Users/User/save_claude_context.py --snapshot` - snapshot na końcu

---

## EXPECTED OUTPUT

Na końcu dostarczysz:

1. **Diagnostic Report** (`notes/AIONS_V3_DIAGNOSTIC_REPORT_YYYYMMDD.md`)
   - Executive summary
   - Status każdego subsystemu (✅/❌/⚠️)
   - Root cause analysis
   - Recommended fixes (priorytetyzowane)

2. **Context Saved**
   - Wszystkie findings w `notes/claude_context/session_log.jsonl`
   - Final snapshot

---

## ZASADY

### ✅ MOŻESZ
- Czytać wszystkie pliki
- Testować system (curl queries)
- Analizować logi
- Używać Task tool (Explore agent) jeśli potrzebujesz
- Dodawać print statements do debugowania (po backup!)

### ❌ NIE MOŻESZ (bez explicit permission)
- Kasować chunks
- Edytować facts_index.json
- Wyłączać serwer
- Robić breaking changes

**JEŚLI NIE JESTEŚ PEWIEN - ASK USER!**

---

## 12 TASKÓW (Z BRIEFINGU)

### TIER 1: KRYTYCZNE
1. Zbadaj Logging System (logi, thinking_log.jsonl)
2. Zbadaj CBMS Retrieval (cbms_memory.py)
3. Zbadaj Query Router (routing logic)

### TIER 2: WAŻNE
4. Zbadaj CBMS-KR (korean_keys.py)
5. Zbadaj Esperanto Indexing
6. Zbadaj CRLA Learning (czy tworzy patterns)
7. Zbadaj Plasters Integration (czy output jest używany)

### TIER 3: OPCJONALNE
8. Zbadaj Pocket QC
9. Zbadaj Consciousness Layer
10. Zbadaj Reasoning
11. Sprawdź Local Chunk Creation
12. Sprawdź Context Preservation

---

## HIPOTEZY DO WERYFIKACJI

1. **Router Broken** - wszystko idzie do default handler
2. **CBMS Returns Empty** - retrieval działa ale zwraca pusty result
3. **Response Assembly Broken** - subsystemy działają ale final assembly ignoruje je
4. **Hardcoded Template** - gdzieś jest hardcoded template override

**Twoim zadaniem: określ która hipoteza jest prawdziwa (albo zaproponuj nową)**

---

## QUICK REFERENCE

```bash
# Health
curl http://localhost:9000/health

# Test query
curl -X POST http://localhost:9000/api/chat -H "Content-Type: application/json" -d '{"query":"TEST"}'

# Zapisz
python /c/Users/User/save_claude_context.py -m "MSG"

# Snapshot
python /c/Users/User/save_claude_context.py --snapshot

# Znajdź pliki
find "E:/AI_WORKSPACE/MASTER_CLEAN/UNCLASSIFIED/AIONS_CBMS_RELEASE_V3" -name "*.jsonl"

# Czytaj logi
tail -100 <log_file>
```

---

## FINAL WORD

Przeczytaj briefing (`DIAGNOSTIC_BRIEFING_FOR_CLAUDE.md`). Tam jest WSZYSTKO co musisz wiedzieć - architektura, problem, zadania, tools, safety rules.

Bądź metodyczny. Dokumentuj wszystko. Nie rób breaking changes.

**Good luck, Junior!**

**- Senior (Session 20251108_163049)**

---

**NEXT STEP**: Przeczytaj `DIAGNOSTIC_BRIEFING_FOR_CLAUDE.md` i zacznij od TIER 1 Task #1.
