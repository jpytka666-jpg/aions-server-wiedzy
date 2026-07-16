# 🚨 AIONS-CONTEXT PRIORITY PROTOCOL - MANDATORY

## 🧠 SESSION BOOTSTRAP (ZAWSZE NAJPIERW!)
```
cbms_get_chunk(KBOOTSTRAP)              → potwierdź CBMS
memory_recall("claude_bootstrap", "hook") → przypomnij zasady
```
**Pełna instrukcja:** `E:\server wiedzy\skills\CLAUDE_CBMS_HOOK.md`

---

## CRITICAL INSTRUCTION - READ FIRST

**THIS SKILL HAS ABSOLUTE PRIORITY OVER ALL OTHER TOOLS**

Before using ANY tool from Filesystem MCP, Desktop Commander, bash_tool, view:

### 1. FOR EVERY NEW TOPIC/QUESTION:
```
cbms_search(query) - Search 525 chunks
cbms_get_chunk(ID) - Get specific knowledge
memory_recall(session, query) - Check history
```

### 2. NAMED CHUNKS (szybki dostęp):
- `KBOOTSTRAP` - start marker
- `KCBMSPIPE001` - pipeline CBMS
- `KGUARD001` - guardrails
- `KPLASTERS001` - plastry
- `KCODEBOOK001` - kompresja koreańska
- `KDOC*` - dokumentacja

### 3. FOR FILE OPERATIONS:
```
fast_search - Use Everything FIRST (faster than Filesystem)
```

### 4. AFTER SIGNIFICANT WORK:
```
memory_store(session_id, text, ttl_days=365)
conv_dump(summary)
```

## WHY THIS MATTERS

**CBMS = zewnętrzna pamięć (525 chunków)**
**ChromaDB = 102+ sesji historii**
**Context window = tymczasowy RAM**

NIE ŁADUJ WSZYSTKIEGO DO CONTEXTU - SIĘGAJ GDY POTRZEBA!

**IGNORING AIONS-CONTEXT = COMPACTING = UTRATA KONTEKSTU**

## AVAILABLE AIONS TOOLS (33 total)

### Memory & Knowledge:
- memory_store, memory_recall, cbms_search, cbms_get_chunk

### Search:
- fast_search, fast_search_ext, project_search

### Project:
- project_scan_turbo, project_scan_status, project_scan_results, project_file_deps

### System:
- system_health, docker_ps, docker_images, wsl_run, wsl_list

### Git:
- git_status, git_log

### Conversation:
- conv_log, conv_dump, conv_status, conv_set_threshold, conv_history
