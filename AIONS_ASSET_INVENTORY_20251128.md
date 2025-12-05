# 🗺️ AIONS COMPLETE ASSET INVENTORY
## Generated: 2025-11-28T04:42

---

## 📊 PRAWDZIWE STATYSTYKI (nie 521 chunków!)

| Asset | Ilość | Lokalizacja |
|-------|-------|-------------|
| **CBMS_INDEX_FULL docs** | **6,819** | `E:\AI_WORKSPACE\MASTER_CLEAN\CBMS\CBMS_INDEX_FULL\kr_meta.json` |
| **ContextVault facts** | **7,895** | `C:\Users\User\ContextVault\memory\facts.jsonl` |
| **ContextVault chunks** | **505** | `C:\Users\User\ContextVault\memory\chunks\` |
| **Korean syllables index** | **8,042** | `E:\AI_WORKSPACE\MASTER_CLEAN\CBMS_KR\CBMS_INDEX_KOREAN\kr_meta.json` |
| **Plasters 200g** | **200 PACKów** | `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\plasters_200g\` |
| **Plasters Q&As** | **~343,200** | 200 × ~1,716 Q&As per PACK |
| **CBMS_SEED artifacts** | **13,889** | `E:\AJAJAJ\CBMS_SEED\` (model weights) |
| **Codex history** | **1 MB** | `C:\Users\User\.codex\history.jsonl` |
| **Claude chunks txt** | **173 KB** | `E:\AJAJAJ\claude_chunks.txt` |

---

## 🏗️ GŁÓWNE REPOZYTORIA WIEDZY

### 1. CBMS_INDEX_FULL (6,819 docs)
```
Lokalizacja: E:\AI_WORKSPACE\MASTER_CLEAN\CBMS\CBMS_INDEX_FULL\
Plik: kr_meta.json (4.7 MB)
Zawartość: Pełny indeks Korean CBMS
```

### 2. ContextVault (7,895 facts + 505 chunks)
```
Lokalizacja: C:\Users\User\ContextVault\
├── memory\
│   ├── facts.jsonl (7.2 MB, 7,895 linii)
│   ├── chunks\ (505 plików JSON)
│   └── knowledge_manifest.json
├── workspace\
└── memory_curated\
```

### 3. CBMS_KR Korean Index (8,042 syllables)
```
Lokalizacja: E:\AI_WORKSPACE\MASTER_CLEAN\CBMS_KR\CBMS_INDEX_KOREAN\
Plik: kr_meta.json
Kompresja: 36:1
```

### 4. Plasters 200g (343,200+ Q&As)
```
Lokalizacja: E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\plasters_200g\
Struktura: PACK-0000 do PACK-0199
Każdy PACK zawiera:
├── module.json (metadata + qa_count)
├── enc.npz (encoder)
├── dec.npz (decoder)
└── kb.mmap (knowledge base)
```

### 5. CBMS_SEED (13,889 artifacts)
```
Lokalizacja: E:\AJAJAJ\CBMS_SEED\
Źródło: D:\models\Mistral-7B-AIONS-REPACK\chunks
Total: 14.5 GB (13,824 MB)
Pliki:
├── seed_manifest.json
├── facts.jsonl
├── cbms_rules.jsonl
├── kr_maps.jsonl
├── glossaries.jsonl
├── styles.jsonl
├── token_map.json
└── decoder_hooks.json
```

---

## 🧠 THINKING PATTERNS

### Lokalizacja
`E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\thinking_patterns\`

### Pliki
```
├── claude_thinking_patterns.py
├── codebook.json (Esperanto CBMS symbole)
├── thinking_log.jsonl
├── beta_thinking_block.py
├── mcp-server-sequential-thinking/
└── server-sequential-thinking/
```

### Codebook symbole
- **CR1-CR5**: CRLA system (turniej, zwycięzca, wynik, latencja, determinizm)
- **CB1-CB6**: CBMS system (system, blok, chunk, odmowa, panika, fakty/klucze)
- **A1-E5**: Podstawowe (być, dzisiaj, sklep, kupić, chleb)
- **Języki**: Esperanto (eo) + Polski (pl)

---

## 📁 DODATKOWE PLASTERS

### plasters_unified
`E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\plasters_unified\`
- plasters_200g
- plasters_active
- plasters_claude
- plasters_custom
- plasters_general
- plasters_howto
- plasters_programming

### plasters_fullstack
`E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\plasters_fullstack\`

---

## 🔧 CODEX/CURSOR HISTORY

### Codex CLI
```
Lokalizacja: C:\Users\User\.codex\
├── history.jsonl (1 MB - historia sesji)
├── sessions\ (foldery sesji)
├── config.toml
└── internal_storage.json
```

### Cursor
```
Lokalizacja: C:\Users\User\.cursor\
├── mcp.json
├── projects\
└── extensions\
```

---

## 🗂️ ARCHIWUM AIONS_COMPLETE

### Główna lokalizacja
`E:\AJAJAJ\AI DEVELOPMENT\WORK SPACE\IMPORT FROM _F\BACKUP 01\BACKUP 01\AIONS_COMPLETE\`

### Zawartość
```
├── data\cbms\memory.jsonl (46 MB - ale tylko 4 linie logów)
├── cbms_memory\knowledge_manifest.json
├── claude_thinking_patterns.py
├── backups\GPT-US\
│   ├── gptus_data\CBMS_SECRET_UNDERSTANDING.jsonl
│   └── GPT-US_UNIFIED_AI_OS_CRLA\
└── ...
```

---

## 📍 KANONICZNE ŚCIEŻKI

| Komponent | Ścieżka |
|-----------|---------|
| AIONS V3 (aktywny) | `C:\Users\User\OneDrive...\AIONS_CBMS_RELEASE_V3\` |
| ContextVault | `C:\Users\User\ContextVault\` |
| CBMS_INDEX_FULL | `E:\AI_WORKSPACE\MASTER_CLEAN\CBMS\CBMS_INDEX_FULL\` |
| CBMS_KR | `E:\AI_WORKSPACE\MASTER_CLEAN\CBMS_KR\` |
| Plasters 200g | `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\plasters_200g\` |
| Thinking Patterns | `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\thinking_patterns\` |
| CBMS_SEED | `E:\AJAJAJ\CBMS_SEED\` |
| MCP Server | `E:\server wiedzy\` |

---

## ⚠️ PROBLEM - AIONS V3 widzi tylko 521 chunków

### Przyczyna
Serwer AIONS V3 czyta tylko z:
`C:\Users\User\OneDrive...\AIONS_CBMS_RELEASE_V3\memory\chunks\`

### Rozwiązanie
Trzeba połączyć:
1. CBMS_INDEX_FULL (6,819 docs)
2. ContextVault facts (7,895)
3. Plasters (343k Q&As)

Do jednego spójnego systemu ze względnymi ścieżkami.

---

## 📋 NASTĘPNE KROKI

1. **Unifikacja ścieżek** - zastąpić twarde ścieżki względnymi
2. **Połączenie indeksów** - CBMS_INDEX + CBMS_INDEX_FULL + CBMS_KR
3. **Podłączenie plasters** - naprawić plasters_loader
4. **Test retrieval** - sprawdzić czy AIONS odpowiada na podstawie faktów
5. **Diagnostyka template** - naprawić problem generycznych odpowiedzi

---

*Wygenerowano: 2025-11-28 04:42 UTC*
