# AIONS DEEP DIVE REPORT
**Data**: 2025-11-29 01:40
**Autor**: Claude (sesja z Marcinem)
**Status**: Kompletna analiza systemu

---

## EXECUTIVE SUMMARY

AIONS (Advanced Intelligence Operating System) to zaawansowany system AI z pamięcią CBMS, kompresją koreańską i integracją Claude thinking patterns. System ma **343,200 Q&As** w plasters, **6,819 dokumentów** w CBMS_INDEX_FULL, i **64MB** historii myślenia.

**GŁÓWNE BUGI ZIDENTYFIKOWANE:**
1. `PlastersPACK.inference()` to placeholder - nie używa wag
2. `_is_noise_content()` filtruje własne odpowiedzi CBMS
3. `_synthesize_chunks()` zwraca hardcoded template

---

## ARCHITEKTURA

```
USER QUERY
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  CBMS_DIRECT_SERVER (port 9000)                     │
│                                                      │
│  1. MATH SOLVER → deterministic calc               │
│  2. CONVERSATIONAL KB → greetings, etc             │
│  3. CBMS.cbms_think()                               │
│     ├─ Korean keys (8,042 syllables, 3.29:1)       │
│     ├─ Symbolic index (Esperanto codebook)         │
│     ├─ Concept lookup (concept_map)                │
│     └─ _synthesize_chunks() ← BUG: template        │
│  4. PANIC check (<2 chunks) → Web RAG              │
│  5. CRLA Tournament (8 candidates, F1-F6)          │
│  6. Plasters.inference() ← BUG: placeholder        │
│  7. Stylist → response formatting                  │
└─────────────────────────────────────────────────────┘
    │
    ▼
RESPONSE
```

---

## SKALA DANYCH

| Zasób | Ilość | Lokalizacja |
|-------|-------|-------------|
| CBMS_INDEX_FULL | 6,819 docs | E:\AI_WORKSPACE\MASTER_CLEAN\CBMS\ |
| Korean syllables | 8,042 | CBMS_INDEX_KOREAN |
| ContextVault facts | 7,895 | C:\Users\User\ContextVault\memory\ |
| ContextVault chunks | 505 | j.w. |
| Plasters Q&As | 343,200 | 200 PACKów × 1,716 |
| thinking_log.jsonl | 64 MB / 32,103 sesji | ContextVault |
| AIONS_SYSTEM_MAP | 1,236 nodes, 27,791 edges | ContextVault |
| Codex sessions | 40+ | C:\Users\User\.codex\ |
| CBMS_SEED artifacts | 13,889 | Mistral-7B-AIONS-REPACK |

---

## MECHANIKI SZCZEGÓŁOWO

### 1. CBMS (Chunk-Based Memory System)

**Struktura chunka:**
```json
{
  "id": "K[12-hex-chars]",
  "content": "treść wiedzy",
  "concept": "kategoria",
  "references": ["K...", "K..."],
  "created": "ISO timestamp",
  "hangul_code": "가" 
}
```

**Retrieval flow:**
1. `extract_concepts()` - wyciąga keywords
2. Korean keys - trigram → SHA1 hash → set intersection
3. Symbolic index - Esperanto codebook matching
4. Concept lookup - concept_map
5. `_synthesize_chunks()` - łączy top 5 chunków

### 2. Korean Compression

**Format CBMS_INDEX_KOREAN:**
```json
{
  "version": "korean-cbms-1.0",
  "korean_syllables_used": 8042,
  "compression_ratio": 36.0,
  "docs": [
    {
      "doc_id": "가",           // 1 znak zamiast 13
      "original_id": "F2C8B5288A83F",
      "chunk_id": "K05EFF163EF91",
      "title": "...",
      "text": "..."
    }
  ]
}
```

**Algorytm:**
- Character 3-grams z tekstu
- SHA1 hash prefix
- Prefiksy: `g:` (trigram), `h:` (hash)
- Set intersection dla semantic search

### 3. Plasters System

**Struktura PACK:**
```
PACK-0000/
├── module.json   # metadata
├── enc.npz       # encoder weights (Claude Opus)
├── dec.npz       # decoder weights
└── kb.mmap       # knowledge base (memory-mapped)
```

**module.json:**
```json
{
  "name": "PACK-0000",
  "d_model": 1024,
  "rank": 512,
  "stats": {"qa_count": 1716},
  "router": {"idf": "idf.npz", "minhash": "mhash.npz"}
}
```

**LRU Cache:** max 10 PACKów w RAM (~10-20GB)

### 4. CRLA Tournament

**6 czynników scoringowych:**
- F1: facts coverage (ilość chunków)
- F2: determinism (1.0 dla current pipeline)
- F3: latency (normalizacja ~150ms)
- F4: policies (refusal jeśli poniżej min_hits)
- F5: trace compactness
- F6: hygiene (UTF-8/printable)

**Threshold:** J=0.893

### 5. Thinking Patterns

**7 wzorców Claude:**
1. ANALYTICAL_BREAKDOWN
2. EVIDENCE_BASED_THINKING
3. ITERATIVE_REFINEMENT
4. MULTIDISCIPLINARY_SYNTHESIS
5. UNCERTAINTY_MANAGEMENT
6. CONTEXTUAL_REASONING
7. META-REASONING FRAMEWORK

**Codebook Esperanto:**
- CR1-CR5: CRLA (turniro, gajninto, poentaro, latenco, determinismo)
- CB1-CB6: CBMS (memorsistemo, memorbloko, fragmento, refuzo, paniko, faktoj)

---

## ZIDENTYFIKOWANE BUGI

### BUG #1: PlastersPACK.inference() PLACEHOLDER

**Lokalizacja:** `plasters_loader.py:79-85`

```python
def inference(self, query_embedding):
    """Run inference: enc → kb → dec"""
    if not self.loaded:
        self.load()
    # Simple inference (placeholder - actual implementation depends on architecture)
    return f"[{self.pack_id}] Response based on {self.qa_count} QAs"
```

**Problem:** Zwraca mock string zamiast prawdziwego inference.
**Impact:** 343,200 Q&As NIE są używane.

### BUG #2: _is_noise_content() ZA AGRESYWNY

**Lokalizacja:** `cbms_memory.py`

```python
noise_prefixes = (
    "no prior knowledge found",
    "na podstawie 5 fragmentów wiedzy",  # ← CBMS FORMAT!
    "based on ",
    "desktop files analysis -",
)
```

**Problem:** Filtruje własne odpowiedzi CBMS jako "noise".
**Impact:** Prawdziwa wiedza jest odrzucana.

### BUG #3: _synthesize_chunks() TEMPLATE FALLBACK

**Lokalizacja:** `cbms_memory.py`

```python
if not relevant_knowledge:
    return f"Witaj! Jestem AIONS - Advanced Intelligence Operating System..."
```

**Problem:** Hardcoded greeting gdy brak wiedzy.
**Impact:** Kombinacja z BUG #2 = zawsze template.

---

## LOKALIZACJE KANONICZNE

| Projekt | Ścieżka | Notatki |
|---------|---------|---------|
| **AIONS_V3 (aktywna)** | C:\Users\User\OneDrive - Global Banking School\Desktop\AIONS_CBMS_RELEASE_V3\ | Serwer port 9000 |
| **MASTER_CLEAN** | E:\AI_WORKSPACE\MASTER_CLEAN\ | Główny workspace |
| **ContextVault** | C:\Users\User\ContextVault\ | Pamięć, facts, chunks |
| **Plasters** | E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\plasters_200g\ | 200 PACKów |
| **Server wiedzy** | E:\server wiedzy\ | MCP Server v6 |
| **CBMS_INDEX_FULL** | E:\AI_WORKSPACE\MASTER_CLEAN\CBMS\CBMS_INDEX_FULL\ | 6,819 docs |
| **CBMS_INDEX_KOREAN** | E:\AI_WORKSPACE\MASTER_CLEAN\CBMS_KR\CBMS_INDEX_KOREAN\ | 8,042 syllables |
| **CBMS_SEED** | E:\AJAJAJ\CBMS_SEED\ | 13,889 artifacts |
| **Thinking patterns** | E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\thinking_patterns\ | 7 wzorców |

---

## DUPLIKATY (8 baz)

1. C:\Users\User\Desktop\
2. C:\Users\User\OneDrive - Global Banking School\Desktop\ ← CANONICAL
3. E:\AI_WORKSPACE\MASTER_CLEAN\ ← WORKSPACE
4. E:\AI_WORKSPACE\MASTER_CLEAN_SNAPSHOT\
5. E:\AI_WORKSPACE\TRASH_BACKUP_MASTER_CLEAN\
6. E:\AI_WORKSPACE\UNCLASSIFIED_SNAPSHOT_MASTER_CLEAN\
7. E:\AJAJAJ\
8. E:\BACKUPS\

**Szacowane oszczędności po cleanup:** 50-100 GB

---

## AIONS_SYSTEM_MAP

**Gotowy graf zależności (12.11.2025):**

| Plik | Rozmiar |
|------|---------|
| system_graph.json | 2.8 MB |
| system_graph.graphml | 2.3 MB |
| graph.dot | 1.2 MB |
| edges.csv | 715 KB (27,791 edges) |
| nodes.csv | 150 KB (1,236 nodes) |

**Typy relacji:**
- `references_chunk` - plik referencuje chunk K[hex]
- `imports` - Python import

**Skrypty:**
- `scan_system.ps1` - skanuje C:\D:\E:\
- `analyze_knowledge.ps1` - analiza grafu
- `import_knowledge.ps1` - import do bazy

---

## KLUCZOWE DATY

| Data | Wydarzenie |
|------|------------|
| 2025-09-13 | KOREAN BREAKTHROUGH (3 wersje w 30 min) |
| 2025-09-18 | Start sesji Codex |
| 2025-09-20 | Pierwszy wpis thinking_log.jsonl |
| 2025-10-28 | Backup server_backup_20251028 |
| 2025-11-03 | thinking_log.jsonl created |
| 2025-11-07 | AIONS_SNAPSHOT backup |
| 2025-11-08 | Handoff docs (DIAGNOSTIC_BRIEFING) |
| 2025-11-09 | thinking_log.jsonl last modified |
| 2025-11-12 | AIONS_SYSTEM_MAP utworzony |
| 2025-11-28 | Full system scan (280MB) |
| 2025-11-29 | Ten raport |

---

## REKOMENDACJE

### NATYCHMIASTOWE (P0)

1. **Napraw PlastersPACK.inference()**
   - Zaimplementuj prawdziwy enc→kb→dec pipeline
   - Użyj numpy do matmul z załadowanymi wagami

2. **Napraw _is_noise_content()**
   - Usuń `"na podstawie"` i `"based on"` z noise_prefixes
   - To są VALIDE odpowiedzi CBMS

3. **Napraw _synthesize_chunks()**
   - Lepszy fallback niż generic greeting
   - Użyj CRLA do generowania odpowiedzi

### ŚREDNIOTERMINOWE (P1)

4. **Połącz odłączone źródła**
   - V3 widzi tylko 521 chunków
   - CBMS_INDEX_FULL ma 6,819
   - Plasters ma 343,200 Q&As

5. **Cleanup duplikatów**
   - 200+ duplikatów w 8 lokalizacjach
   - 50-100 GB do odzyskania

### DŁUGOTERMINOWE (P2)

6. **IDF + MinHash routing dla Plasters**
   - router.idf i router.minhash są w module.json
   - Aktualnie hash-based routing

7. **Distributed Plasters**
   - 200 PACKów to dużo
   - Multi-machine setup

---

## PLIKI REFERENCYJNE

- `C:\Users\User\notes\DIAGNOSTIC_BRIEFING_FOR_CLAUDE.md` (17KB)
- `C:\Users\User\notes\HANDOFF_TO_NEXT_CLAUDE.md` (5.6KB)
- `C:\Users\User\notes\AIONS_V3_DISCOVERY.md` (10.5KB)
- `E:\server wiedzy\AIONS_CATALOG\INDEX.md`
- `E:\server wiedzy\ANALYSIS_CHECKPOINT_20251128.md`

---

## KONIEC RAPORTU

**Wygenerowano:** 2025-11-29 01:40 UTC
**Przez:** Claude Opus 4.5 + MCP Server v6 DEBILOODPORNE
