# 🗺️ AIONS ECOSYSTEM DEPENDENCY MAP
## Complete Project Inventory & Dependency Graph
### Generated: 2025-11-28

---

## 📊 OVERVIEW STATISTICS

| Metric | Count |
|--------|-------|
| CLAUDE.md files | 31 |
| POLIP folders/files | 44 |
| CBMS folders/files | 50+ |
| MAIPA folders/files | 18 |
| CRLA folders/files | 46 |
| Pocket_QC folders/files | 50+ |
| GPT-US folders/files | 23 |
| MAPA_LASU docs | 24 |
| **TOTAL DUPLICATES** | **200+** |

---

## 🏗️ CORE PROJECTS

### 1. AIONS (AI Optimization Neural System)
**Status:** OPERATIONAL (with issues)
**Primary Location:** `C:\Users\User\OneDrive - Global Banking School\Desktop\AIONS_CBMS_RELEASE_V3\`

```
AIONS
├── CBMS (Chunk-Based Memory System) - Core knowledge storage
├── CRLA (Chain Reaction Learning Algorithm) - Tournament selection
├── Korean Keys - 3.29:1 compression using Korean syllables
├── Plasters - Extended knowledge packs (343,091 Q&As)
├── Pocket QC - Quantum Computing Emulator
├── Math Solver - Deterministic calculations
├── OOD Detection - Out-of-domain safety
└── Conversation Enhancer - Response formatting
```

**Known Issues:**
- All responses return generic template (DIAGNOSTIC NEEDED)
- CBMS retrieval always returns "1 fragment"
- Query routing broken

### 2. CBMS (Chunk-Based Memory System)
**Dependency:** Core component of AIONS
**Chunks:** 521 active (V3), 2,233 historical

```
CBMS Dependencies:
├── korean_keys.py - Compression algorithm
├── cbms_memory.py - Memory management
├── knowledge_manifest.json - Chunk index (~10MB, 33,945+ facts)
├── facts_index.json - Core knowledge database
└── chunks/ folder - 521 JSON chunk files
```

### 3. CRLA (Chain Reaction Learning Algorithm)
**Dependency:** Learning component of AIONS

```
CRLA Dependencies:
├── crla_core.py - Tournament algorithm
├── crla_policies/ - Policy definitions
├── crla_runs.jsonl - Learning history
├── thinking_log.jsonl - Thinking patterns
└── baseline__crla_ask.json - Configuration
```

### 4. POLIP (Brain Probe System)
**Status:** Multiple versions exist
**Primary:** `E:\AJAJAJ\CBMS_EXTRACT\POLIP_GOOD_20250823_220346\`

```
POLIP Versions:
├── POLIP_20250823_193350
├── POLIP_DOSSIER_20250822_* (4 versions)
├── POLIP_FIX_v2_20250823_161945
├── POLIP_GOOD_20250823_220346 ← BEST VERSION
├── POLIP_INVENTORY_20250823_200855
└── POLIPEK V1 (with rollback system)
```

### 5. MAIPA (AI Assistant)
**Status:** Development
**Primary:** `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\MAIPA\`

```
MAIPA Components:
├── maipa.py - Main script
├── maipa_pro.py - Pro version
├── maipa_v2/ - Version 2 folder
└── tests/ - Test suite
```

### 6. Pocket QC (Quantum Computing Emulator)
**Dependency:** Optional component of AIONS
**Primary:** `E:\CBMS_Pocket_QC_Lab\`

```
Pocket_QC Components:
├── pocket_qc.py - Main module
├── crla_policies/ - CRLA integration
├── Statevector simulator
├── QUBO optimizer
└── Deterministic trace (JSONL + checksums)
```

### 7. GPT-US (Custom GPT)
**Status:** ChatGPT Custom GPT integrated with AIONS
**Location:** `E:\AI_WORKSPACE\...\GPT-US\`

```
GPT-US Components:
├── GPT-US_UNIFIED_AI_OS_CRLA/ - CRLA integration
├── GPT-US_DIAGNOSTIC_REPORT.md
├── README_GPT-US.md
└── gptus_data/CBMS_SECRET_UNDERSTANDING.jsonl ← IMPORTANT!
```

---

## 🔄 DEPENDENCY GRAPH

```
                    ┌─────────────────────────────────────┐
                    │           AIONS SYSTEM              │
                    │    (AIONS_CBMS_RELEASE_V3)          │
                    └─────────────────────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
          ▼                         ▼                         ▼
    ┌───────────┐           ┌───────────┐           ┌───────────┐
    │   CBMS    │           │   CRLA    │           │ Plasters  │
    │ (Memory)  │◄─────────►│(Learning) │           │(Knowledge)│
    └───────────┘           └───────────┘           └───────────┘
          │                         │                         │
          │                         │                         │
          ▼                         ▼                         │
    ┌───────────┐           ┌───────────┐                     │
    │  Korean   │           │ Pocket QC │                     │
    │   Keys    │           │(Quantum)  │                     │
    └───────────┘           └───────────┘                     │
          │                                                   │
          │     ┌───────────────────────────────────────────┘
          │     │
          ▼     ▼
    ┌───────────────────────────────────────────────────────┐
    │                    OUTPUT LAYER                        │
    │  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
    │  │   Math   │  │   OOD    │  │  Convo   │            │
    │  │  Solver  │  │Detection │  │ Enhancer │            │
    │  └──────────┘  └──────────┘  └──────────┘            │
    └───────────────────────────────────────────────────────┘
                              │
                              ▼
                       API Server (port 9000)
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
     ┌─────────┐        ┌─────────┐        ┌─────────┐
     │ GPT-US  │        │  POLIP  │        │  MAIPA  │
     │ (Chat)  │        │ (Probe) │        │ (Asst)  │
     └─────────┘        └─────────┘        └─────────┘
```

---

## 📁 CANONICAL LOCATIONS (USE THESE!)

| Project | Canonical Location | Status |
|---------|-------------------|--------|
| AIONS V3 | `C:\Users\User\OneDrive - Global Banking School\Desktop\AIONS_CBMS_RELEASE_V3\` | PRIMARY |
| CBMS Core | Same as AIONS V3 | INTEGRATED |
| CRLA | Same as AIONS V3 + `E:\...\crla\` | SPLIT |
| POLIP | `E:\AJAJAJ\CBMS_EXTRACT\POLIP_GOOD_20250823_220346\` | BEST |
| MAIPA | `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\MAIPA\` | DEV |
| Pocket QC | `E:\CBMS_Pocket_QC_Lab\` | ISOLATED |
| GPT-US | `E:\AI_WORKSPACE\MASTER_CLEAN\CBMS\CBMS_EXTRACT\...\GPT-US\` | ARCHIVE |
| ContextVault | `C:\Users\User\ContextVault\` | ACTIVE |
| MCP Server | `E:\server wiedzy\` | ACTIVE |

---

## 🔴 DUPLICATE HELL - LOCATIONS TO CLEAN

### Pattern: Every project exists in 4-8 places:

```
1. C:\Users\User\Desktop\                     # Desktop (current work)
2. C:\Users\User\OneDrive...\Desktop\         # OneDrive sync (CANONICAL)
3. E:\AI_WORKSPACE\MASTER_CLEAN\              # Master workspace
4. E:\AI_WORKSPACE\MASTER_CLEAN_SNAPSHOT\     # Snapshot copy
5. E:\AI_WORKSPACE\TRASH_BACKUP_MASTER_CLEAN\ # Trash backup
6. E:\AI_WORKSPACE\UNCLASSIFIED_SNAPSHOT...\  # Another snapshot
7. E:\AJAJAJ\                                  # Another full copy
8. E:\BACKUPS\                                 # Backup folder
```

### RECOMMENDED CLEANUP:

**KEEP:**
- `C:\Users\User\OneDrive...\Desktop\AIONS_CBMS_RELEASE_V3\` - PRIMARY
- `E:\AI_WORKSPACE\MASTER_CLEAN\` - WORKSPACE
- `E:\BACKUPS\` - SINGLE BACKUP

**DELETE (after verification):**
- `E:\AI_WORKSPACE\MASTER_CLEAN_SNAPSHOT\` - redundant
- `E:\AI_WORKSPACE\TRASH_BACKUP_MASTER_CLEAN\` - redundant
- `E:\AI_WORKSPACE\UNCLASSIFIED_SNAPSHOT_MASTER_CLEAN\` - redundant
- `E:\AJAJAJ\` - full duplicate

**Estimated space savings:** 50-100GB

---

## 📋 FILE DEPENDENCIES (Cross-References)

### cbms_direct_server.py depends on:
```python
from cbms_memory import CBMSMemory
from korean_keys import KoreanKeyCompressor
from crla_core import CRLATournament
from plasters_loader import PlastersLoader
from conversation_enhancer import ConversationEnhancer
from math_solver import MathSolver
from stylist import Stylist
```

### AIONS_ULTIMATE_UNIFIED.py depends on:
```python
# All of the above plus:
from pocket_qc import PocketQC
from ood_detector import OODDetector
```

### Key Data Files:
```
memory/
├── knowledge_manifest.json  ← CRITICAL (10MB, 33,945 facts)
├── facts_index.json         ← CRITICAL
├── chunks/                  ← CRITICAL (521 files)
├── thinking_log.jsonl       ← Important (learning history)
└── crla_runs.jsonl          ← Important (CRLA history)
```

---

## 🚨 CRITICAL ACTIONS NEEDED

### 1. FIX AIONS DIAGNOSTIC ISSUE
**Problem:** All responses return generic template
**Location:** `server/cbms_direct_server.py`
**Task:** Follow DIAGNOSTIC_BRIEFING_FOR_CLAUDE.md

### 2. DEDUPLICATE FOLDERS
**Current:** 200+ duplicate folders
**Target:** Single canonical location per project
**Savings:** 50-100GB disk space

### 3. CONSOLIDATE DOCUMENTATION
**Current:** 31 CLAUDE.md files scattered
**Target:** Single master CLAUDE.md per project

### 4. FIX BROKEN IMPORTS
**Symptom:** Multiple `__pycache__` across locations
**Solution:** Single Python path, clean bytecode

---

## 🛠️ RECOMMENDED TOOLS

### For Deduplication:
- `E:\server wiedzy\scripts\turbo_scanner.py` - Hash-based duplicate finder
- `Everything CLI (es.exe)` - Fast file search

### For Dependency Mapping:
- Python `ast` module - Parse imports
- `pipdeptree` - Python package dependencies
- `grep -r "from .* import"` - Find cross-references

### For Cleanup:
- `robocopy /MIR` - Mirror single canonical folder
- `rdfind` - Find and link duplicates
- Git - Version control canonical locations

---

## 📝 NEXT STEPS

1. **READ:** `C:\Users\User\notes\DIAGNOSTIC_BRIEFING_FOR_CLAUDE.md`
2. **FIX:** AIONS diagnostic issue (template responses)
3. **SCAN:** Run TURBO scanner for complete file inventory
4. **DEDUPE:** Identify and remove duplicate folders
5. **CONSOLIDATE:** Single canonical location per project
6. **DOCUMENT:** Update this map with fixes

---

## 📚 KEY DOCUMENTATION FILES

| File | Location | Purpose |
|------|----------|---------|
| CLAUDE.md | C:\Users\User\ | Master documentation |
| HANDOFF_TO_NEXT_CLAUDE.md | C:\Users\User\notes\ | Session handoff |
| DIAGNOSTIC_BRIEFING_FOR_CLAUDE.md | C:\Users\User\notes\ | Diagnostic tasks |
| MAPA_LASU.txt | MAPA_LASU_SOLO_CBMS\ | Full system map |
| MAPA_LASU_TECHNICAL_FACTS.txt | Same | Technical details |

---

**Generated by:** Claude + AIONS MCP Server v6
**Last updated:** 2025-11-28T03:40:00Z
