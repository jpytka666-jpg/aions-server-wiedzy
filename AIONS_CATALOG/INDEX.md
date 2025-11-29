# 📚 AIONS KNOWLEDGE CATALOG
## Master Index - Server Wiedzy
### Generated: 2025-11-28

---

## 🗂️ STRUKTURA KATALOGU

```
E:\server wiedzy\AIONS_CATALOG\
├── indices\         # Indeksy CBMS (kr_meta.json, manifesty)
├── chunks\          # Chunki wiedzy (JSON)
├── plasters\        # Rozszerzone paczki wiedzy (PACK-xxxx)
├── thinking_patterns\  # Wzorce myślenia Claude
├── codebooks\       # Codebooki Esperanto/Korean
├── facts\           # Bazy faktów (facts.jsonl)
├── models\          # Odnośniki do modeli AI
├── tools\           # Narzędzia i skrypty
└── docs\            # Dokumentacja
```

---

## 📊 PEŁNA INWENTARYZACJA

### 1. INDEKSY CBMS

| Nazwa | Docs/Items | Rozmiar | Lokalizacja źródłowa |
|-------|------------|---------|---------------------|
| CBMS_INDEX_FULL | **6,819 docs** | 4.7 MB | `E:\AI_WORKSPACE\MASTER_CLEAN\CBMS\CBMS_INDEX_FULL\kr_meta.json` |
| CBMS_INDEX_KOREAN | **8,042 syllables** | ~2 MB | `E:\AI_WORKSPACE\MASTER_CLEAN\CBMS_KR\CBMS_INDEX_KOREAN\kr_meta.json` |
| CBMS_INDEX (basic) | varies | - | `E:\AI_WORKSPACE\MASTER_CLEAN\CBMS\CBMS_INDEX\kr_meta.json` |

### 2. CHUNKS WIEDZY

| Źródło | Ilość | Lokalizacja |
|--------|-------|-------------|
| ContextVault | **505 chunks** | `C:\Users\User\ContextVault\memory\chunks\` |
| AIONS V3 | 521 chunks | `C:\Users\User\OneDrive...\AIONS_CBMS_RELEASE_V3\memory\chunks\` |
| AIONS V0-V2 | varies | `E:\AI_WORKSPACE\MASTER_CLEAN\AIONS_CORE\AIONS_V10\` |

### 3. FACTS/KNOWLEDGE BASES

| Plik | Linie/Rozmiar | Lokalizacja |
|------|---------------|-------------|
| ContextVault facts | **7,895 linii** / 7.2 MB | `C:\Users\User\ContextVault\memory\facts.jsonl` |
| knowledge_manifest | 33,945+ facts / 10 MB | `...\AIONS_CBMS_RELEASE_V3\memory\knowledge_manifest.json` |
| claude_chunks.txt | 173 KB | `E:\AJAJAJ\claude_chunks.txt` |

### 4. PLASTERS (Extended Knowledge Packs)

| Pakiet | PACKi | Q&As | Lokalizacja |
|--------|-------|------|-------------|
| plasters_200g | **200** | **~343,200** | `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\plasters_200g\` |
| plasters_fullstack | 448 | ~768,768 | `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\plasters_fullstack\` |
| plasters_unified | mixed | - | `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\plasters_unified\` |
| plasters_claude | - | - | `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\plasters_claude\` |
| plasters_howto | - | - | `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\plasters_howto\` |
| plasters_programming | - | - | `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\plasters_programming\` |

**Struktura PACK:**
```
PACK-xxxx/
├── module.json    # Metadata (qa_count, d_model, rank)
├── enc.npz        # Encoder weights
├── dec.npz        # Decoder weights
└── kb.mmap        # Knowledge base memory-mapped
```

### 5. THINKING PATTERNS

| Plik | Opis | Lokalizacja |
|------|------|-------------|
| claude_thinking_patterns.py | Wzorce myślenia | `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\thinking_patterns\` |
| codebook.json | Esperanto symbole | j.w. |
| thinking_log.jsonl | Log myślenia | j.w. |
| beta_thinking_block.py | Extended thinking | j.w. |
| mcp-server-sequential-thinking/ | MCP server | j.w. |

**Zidentyfikowane wzorce:**
- ANALYTICAL_BREAKDOWN
- EVIDENCE_BASED_THINKING
- ITERATIVE_REFINEMENT
- MULTIDISCIPLINARY_SYNTHESIS
- UNCERTAINTY_MANAGEMENT
- CONTEXTUAL_REASONING
- META-REASONING FRAMEWORK

### 6. CODEBOOKS

| Codebook | Symbole | Języki | Lokalizacja |
|----------|---------|--------|-------------|
| CBMS Esperanto | CR1-CR5 (CRLA), CB1-CB6 (CBMS) | PL, EO | `thinking_patterns\codebook.json` |
| Korean Keys | 4,016+ patterns | KR | `CBMS_KR\` |
| Token Map | varies | - | `CBMS_SEED\token_map.json` |

### 7. MODELE I WEIGHTS

| Model | Artifacts | Rozmiar | Lokalizacja |
|-------|-----------|---------|-------------|
| CBMS_SEED (Mistral repack) | **13,889** | 14.5 GB | `E:\AJAJAJ\CBMS_SEED\` |
| Mistral-7B-AIONS-REPACK | chunks | - | `D:\models\Mistral-7B-AIONS-REPACK\` |

### 8. PROJEKTY POWIĄZANE

| Projekt | Status | Lokalizacja |
|---------|--------|-------------|
| POLIP (Brain Probe) | Archived | `E:\AJAJAJ\CBMS_EXTRACT\POLIP_GOOD_20250823_220346\` |
| MAIPA | Development | `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\MAIPA\` |
| Pocket QC | Integrated | `E:\CBMS_Pocket_QC_Lab\` |
| GPT-US | Custom GPT | `E:\...\GPT-US\` |
| CRLA | Core component | Integrated in AIONS |

---

## 🔗 SZYBKIE LINKI

### Aktywny system
- **AIONS V3**: `C:\Users\User\OneDrive - Global Banking School\Desktop\AIONS_CBMS_RELEASE_V3\`
- **ContextVault**: `C:\Users\User\ContextVault\`
- **MCP Server**: `E:\server wiedzy\mcpServers\VS_CODE_MCP_CODEX\`

### Workspace
- **MASTER_CLEAN**: `E:\AI_WORKSPACE\MASTER_CLEAN\`
- **CBMS**: `E:\AI_WORKSPACE\MASTER_CLEAN\CBMS\`
- **UNCLASSIFIED**: `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\`

### Backupy
- **AJAJAJ**: `E:\AJAJAJ\` (pełna kopia)
- **BACKUPS**: `E:\BACKUPS\`
- **SNAPSHOTS**: `E:\AI_WORKSPACE\MASTER_CLEAN_SNAPSHOT\`

---

## 📈 STATYSTYKI SUMARYCZNE

| Metryka | Wartość |
|---------|---------|
| **Total docs (CBMS_INDEX_FULL)** | 6,819 |
| **Total facts (ContextVault)** | 7,895 |
| **Total chunks** | ~1,500+ |
| **Total Q&As (plasters_200g)** | ~343,200 |
| **Korean syllables** | 8,042 |
| **Thinking patterns** | 7+ |
| **Model artifacts** | 13,889 |
| **Plaster packs** | 200+ |

---

## ⚠️ ZNANE PROBLEMY

1. **AIONS V3 widzi tylko 521 chunków** - trzeba podłączyć pozostałe źródła
2. **Twarde ścieżki w kodzie** - wymagają unifikacji
3. **Duplikacja folderów** - 200+ duplikatów w systemie
4. **Template responses** - AIONS zwraca generyczne odpowiedzi

---

## 🛠️ NARZĘDZIA

| Narzędzie | Lokalizacja |
|-----------|-------------|
| Everything CLI | `C:\Program Files\Everything\es.exe` |
| MCP Server v6 | `E:\server wiedzy\mcpServers\VS_CODE_MCP_CODEX\src\server.py` |
| TURBO Scanner | `E:\server wiedzy\scripts\turbo_scanner.py` |
| ChatGPT Extractor | `E:\server wiedzy\scripts\chatgpt_ultimate.py` |

---

*Katalog wygenerowany automatycznie przez Claude + MCP Server*
*Ostatnia aktualizacja: 2025-11-28*
