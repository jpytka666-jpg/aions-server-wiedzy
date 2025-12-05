# AIONS FULL ANALYSIS - 2025-12-04

## EXECUTIVE SUMMARY

**Status:** CHAOS - Repozytorium wymaga natychmiastowej konsolidacji

**Top 5 Problemów:**
1. **Duplikacja kodu** - Wiele wersji tego samego pliku w różnych lokalizacjach
2. **Brak CBMS** - Główny komponent AIONS (CBMS) nie jest w tym repozytorium
3. **Gigantyczny venv** - 1.27GB niepotrzebnych plików w repozytorium
4. **Rozproszenie** - Kod rozrzucony po E:\AIONS_V10\, E:\AJAJAJ\, Linux partycji
5. **Brak dokumentacji** - Brak README.md, niekompletna dokumentacja

**Top 3 Pilne Akcje:**
1. Wykonać AIONS_MASTER_EXECUTE.ps1 aby skonsolidować wszystko
2. Dodać venv/ do .gitignore i usunąć z repo
3. Zintegrować CBMS z E:\AIONS_V10\AIONS_CBMS_RELEASE_V3\

---

## 1. STRUKTURA REPOZYTORIUM

### Główne Foldery

| Folder | Cel | Status | Plików | Rozmiar | Uwagi |
|--------|-----|--------|--------|---------|-------|
| **venv/** | Python virtual env | ❌ PROBLEM | 41,271 | 1.27GB | NIE POWINNO BYĆ W REPO! |
| **tu huje/** | Testy/benchmarki | ⚠️ Chaos | 4,734 | 764MB | Dziwna nazwa, niejasny cel |
| **FULL_SCAN_*/** | Wyniki skanów | 📊 Archiwum | 25 | 472MB | 3 foldery skanów - można zarchiwizować |
| **index/** | Indeksy (IDF, mhash) | ✅ Aktywny | 10 | 179MB | Korean Keys / MART indices |
| **data/chroma/** | ChromaDB | ✅ Aktywny | 102 | 38.6MB | 25 sesji, 162 embeddingi |
| **server/** | Core AIONS backend | ✅ Aktywny | 13 | 60KB | store.py, context_schema.py, models.py, app.py |
| **mcpServers/** | MCP server | ✅ Aktywny | 21 | 250KB | VS_CODE_MCP_CODEX - główny MCP |
| **scripts/** | Utility scripts | ✅ Aktywny | 23 | 90KB | Skrypty instalacyjne, skanery |
| **logs/** | Conversation dumps | ✅ Aktywny | 9 | 120KB | Auto-logging JSONL |
| **AIOrchestrator/** | Legacy system | ⚠️ Martwy? | 71 | 310KB | Stary system, prawdopodobnie nieużywany |
| **chatgpt_extracted/** | Ekstrakty ChatGPT | 📊 Archiwum | 16 | 340KB | Dane z ChatGPT |
| **AIONS_CATALOG/** | Katalog wiedzy | ✅ Aktywny | 10 | 20KB | chunks, facts, plasters, thinking_patterns |
| **docs/** | Dokumentacja | ⚠️ Niekompletna | 2 | 10KB | MCP_SETUP.md, NONICATAB_MCP_ARCHITECTURE.md |
| **skills/** | Skills | ⚠️ Pusty | 1 | <1KB | aions-priority-SKILL.md |
| **files_extracted/** | Ekstrakty | ⚠️ Duplikat | 12 | 110KB | marcin_memory_mcp - DUPLIKAT! |
| **marcin_memory_mcp/** | MCP memory | ⚠️ Duplikat | 1 | <1KB | DUPLIKAT files_extracted/ |
| **ustawienia_md/** | Ustawienia Claude | 📊 Archiwum | 27 | 140KB | Stare ustawienia |
| **.kiro/** | Kiro IDE config | ✅ Aktywny | 5 | 10KB | settings, specs, steering |
| **.claude/** | Claude config | ✅ Aktywny | 10 | 50KB | agents, specs, system-prompts |

### Pliki Główne

| Plik | Rozmiar | Status | Uwagi |
|------|---------|--------|-------|
| requirements.txt | <1KB | ✅ | Zależności Python |
| context_admin.py | <10KB | ✅ | Admin tool dla ChromaDB |
| show_chroma.py | <1KB | ✅ | Narzędzie diagnostyczne |
| aions_scan.db | ? | ⚠️ | SQLite DB - cel niejasny |
| AIONS_MASTER_*.md | ~50KB | ✅ | Plany konsolidacji |
| AIONS_MASTER_EXECUTE.ps1 | ~20KB | ✅ | Skrypt konsolidacji - GOTOWY DO URUCHOMIENIA |

---

## 2. KLUCZOWE KOMPONENTY AIONS

### 2.1 ChromaDB (Semantic Search)

**Lokalizacja:** `data/chroma/`  
**Rozmiar:** 38.6MB  
**Status:** ✅ DZIAŁA

**Statystyki:**
- **25 kolekcji** (sesji)
- **162 embeddingi** (dokumenty)
- **1,557 metadanych**
- Główne sesje:
  - `session_claude_session_20251113`
  - `session_claude_auto_20251113`
  - `session_claude_auto_20251115`
  - `session_claude_auto_20251114`
  - `session_codex_check`

**Integracja:**
- `server/store.py` - VectorStore class
- `server/context_schema.py` - Metadata normalization
- MCP server używa przez `get_vector_store()`

### 2.2 CBMS (Chunk-Based Memory System)

**Lokalizacja:** ❌ **BRAK W TYM REPO!**  
**Prawdopodobna lokalizacja:** `E:\AIONS_V10\AIONS_CBMS_RELEASE_V3\`

**Problem:** MCP server próbuje załadować CBMS z:
```python
AIONS_V10 = Path("E:/AIONS_V10/AIONS_CBMS_RELEASE_V3")
from cbms_memory import CBMSMemory
```

**Status:** ⚠️ CBMS nie jest częścią tego repozytorium!

**Akcja:** Trzeba skopiować/zlinkować CBMS z E:\AIONS_V10\

### 2.3 Korean Keys (Fast Matching)

**Lokalizacja:** `index/` + wbudowane w MCP server  
**Status:** ✅ DZIAŁA

**Implementacja:**
```python
def korean_build_keys(text: str) -> set:
    tokens = re.findall(r"[A-Za-z0-9]{2,}", text.lower())
    keys = set()
    for tok in tokens[:30]:
        for i in range(len(tok) - 2):
            keys.add(f"g:{tok[i:i+3]}")  # 3-gram
        h = hashlib.sha1(tok.encode()).hexdigest()[:12]
        keys.add(f"h:{h[0:3]}")  # Hash prefix
    return keys
```

**Pliki indeksów:**
- `index/claude.idf.npz` - IDF weights
- `index/claude.mhash.npz` - MinHash signatures
- `index/global_200g.idf.npz`
- `index/global_full.idf.npz`

### 2.4 Auto-Logging System

**Lokalizacja:** `logs/conversation_dumps/`  
**Status:** ✅ DZIAŁA

**Mechanizm:** DEBILOODPORNE AUTO-LOGGING
- Każde wywołanie narzędzia MCP = automatyczny log
- Buffer 5 wpisów → auto-dump do JSONL + ChromaDB
- Decorator `@auto_logged` na wszystkich toolach

**Pliki logów:**
```
autolog_2025-12-03.jsonl  21.75KB  (DZISIAJ)
autolog_2025-12-02.jsonl   2.03KB
autolog_2025-12-01.jsonl   9.72KB
autolog_2025-11-29.jsonl  45.96KB
autolog_2025-11-28.jsonl  34.51KB
```

**Format:**
```json
{
  "id": "abc123",
  "timestamp": "2025-12-04T00:00:00Z",
  "tool": "fast_search",
  "args": "query='*.py', max_results=50",
  "result": "status: ok, files: 127"
}
```

### 2.5 MCP Server (aions-context)

**Lokalizacja:** `mcpServers/VS_CODE_MCP_CODEX/src/server.py`  
**Status:** ✅ DZIAŁA  
**Wersja:** v6 DEBILOODPORNE + PLAYWRIGHT + MCP CATALOG

**Narzędzia (32 total):**

#### Wyszukiwanie plików (Everything)
- `fast_search` - Błyskawiczne wyszukiwanie plików
- `fast_search_ext` - Wyszukiwanie po rozszerzeniu

#### Docker
- `docker_ps` - Lista kontenerów
- `docker_images` - Lista obrazów

#### WSL/Linux
- `wsl_run` - Uruchom komendę w WSL
- `wsl_list` - Lista dystrybucji WSL

#### Git
- `git_status` - Status repozytorium
- `git_log` - Historia commitów

#### Network
- `network_ping` - Ping hosta

#### Project Scanner
- `project_scan_turbo` - TURBO skan (Everything)
- `project_scan_status` - Status skanu
- `project_scan_results` - Wyniki skanu
- `project_search` - Szukanie w wynikach
- `project_file_deps` - Zależności pliku

#### Conversation Logging
- `conv_log` - Manualny log
- `conv_dump` - Wymuś dump bufora
- `conv_status` - Status bufora
- `conv_set_threshold` - Ustaw próg auto-dump
- `conv_history` - Historia logów

#### Memory (ChromaDB + CBMS + Korean)
- `memory_store` - Zapisz do pamięci
- `memory_recall` - Wyszukaj w pamięci (3 źródła!)
- `session_list` - Lista sesji
- `cbms_search` - Bezpośrednie CBMS

#### System
- `system_health` - Health check

#### Browser (Playwright)
- `browser_navigate` - Nawiguj do URL
- `browser_snapshot` - Accessibility snapshot
- `browser_click` - Kliknij element
- `browser_type` - Wpisz tekst
- `browser_screenshot` - Screenshot
- `browser_get_text` - Pobierz tekst
- `browser_close` - Zamknij przeglądarkę
- `browser_evaluate` - Wykonaj JavaScript

#### MCP Catalog
- `mcp_find` - Szukaj serwerów MCP
- `mcp_list` - Lista serwerów
- `mcp_info` - Info o serwerze

#### Web
- `web_fetch` - Pobierz URL

**Konfiguracja:** `.kiro/settings/mcp.json`
```json
{
  "mcpServers": {
    "aions-context": {
      "command": "E:/server wiedzy/venv/Scripts/python.exe",
      "args": ["-m", "mcp.server.stdio", "--server-script", 
               "E:/server wiedzy/mcpServers/VS_CODE_MCP_CODEX/src/server.py"],
      "env": {
        "CHROMA_PATH": "E:/server wiedzy/data/chroma",
        "PYTHONPATH": "E:/server wiedzy;E:/server wiedzy/server"
      }
    }
  }
}
```

---

## 3. MAPA PLIKÓW PYTHON

| Plik | Lokalizacja | Cel | Importuje | Importowany przez | Status |
|------|-------------|-----|-----------|-------------------|--------|
| **server/store.py** | server/ | ChromaDB wrapper | chromadb, context_schema | app.py, MCP server | ✅ AKTYWNY |
| **server/context_schema.py** | server/ | Metadata normalization | - | store.py | ✅ AKTYWNY |
| **server/models.py** | server/ | Pydantic models | pydantic | app.py | ✅ AKTYWNY |
| **server/app.py** | server/ | FastAPI server | fastapi, store, models | - | ✅ AKTYWNY |
| **mcpServers/.../server.py** | mcpServers/VS_CODE_MCP_CODEX/src/ | MCP server | mcp, chromadb, playwright | - | ✅ AKTYWNY |
| **context_admin.py** | ./ | Admin CLI | server.store | - | ✅ AKTYWNY |
| **show_chroma.py** | ./ | Diagnostic tool | sqlite3 | - | ✅ AKTYWNY |
| **scripts/project_scanner.py** | scripts/ | Project scanner | - | MCP server | ✅ AKTYWNY |
| **scripts/turbo_scanner.py** | scripts/ | TURBO scanner (Everything) | - | MCP server | ✅ AKTYWNY |
| **scripts/chatgpt_*.py** | scripts/ | ChatGPT extractors | - | - | 📊 ARCHIWUM |
| **scripts/aions_tray.py** | scripts/ | System tray app | - | - | ⚠️ NIEZNANY |
| **files_extracted/.../server.py** | files_extracted/marcin_memory_mcp/ | MCP memory server | mcp | - | ⚠️ DUPLIKAT |
| **marcin_memory_mcp/server.py** | marcin_memory_mcp/ | MCP memory server | mcp | - | ⚠️ DUPLIKAT |

---

## 4. WYKRYTE DUPLIKATY

### 4.1 marcin_memory_mcp

**Duplikat:**
- `files_extracted/marcin_memory_mcp/server.py` (pełny plik, 15KB)
- `marcin_memory_mcp/server.py` (obcięty, <1KB)

**Akcja:** Usunąć `marcin_memory_mcp/` (niepełny), zachować `files_extracted/`

### 4.2 Potencjalne duplikaty w AIONS_V10

**Nie sprawdzone** (poza tym repo):
- `E:\AIONS_V10\AIONS_CBMS_RELEASE_V0\`
- `E:\AIONS_V10\AIONS_CBMS_RELEASE_V1\`
- `E:\AIONS_V10\AIONS_CBMS_RELEASE_V2\`
- `E:\AIONS_V10\AIONS_CBMS_RELEASE_V3\` ← **PRODUKCJA**
- `E:\AIONS_V10\AIONS_CBMS_VANILA\`

**Akcja:** Wykonać `AIONS_MASTER_EXECUTE.ps1` aby skonsolidować

---

## 5. MARTWY KOD

### 5.1 Prawdopodobnie martwe

| Folder/Plik | Powód | Akcja |
|-------------|-------|-------|
| **AIOrchestrator/** | Stary system, brak importów | Zarchiwizować |
| **tu huje/** | Testy, 764MB | Przejrzeć i zarchiwizować |
| **chatgpt_extracted/** | Ekstrakty, archiwum | Zarchiwizować |
| **ustawienia_md/** | Stare ustawienia | Zarchiwizować |
| **FULL_SCAN_*/** | Stare skany | Zarchiwizować |
| **scripts/aions_tray.py** | System tray - nieużywany? | Sprawdzić |

### 5.2 Pliki bez importów

```
show_chroma.py - używany manualnie (OK)
context_admin.py - używany manualnie (OK)
scripts/chatgpt_*.py - archiwum (OK)
```

---

## 6. BRAKUJĄCE ELEMENTY

### 6.1 Krytyczne

1. **README.md** - Brak głównego README!
2. **CBMS** - Główny komponent nie w repo
3. **.gitignore** - Brak lub niepełny (venv w repo!)
4. **LICENSE** - Brak licencji

### 6.2 Dokumentacja

**Istniejące:**
- `docs/MCP_SETUP.md` - Setup MCP
- `docs/NONICATAB_MCP_ARCHITECTURE.md` - Architektura
- `AIONS_MASTER_INSTRUCTIONS.md` - Instrukcje konsolidacji
- `AIONS_MASTER_CONSOLIDATION_PLAN.md` - Plan konsolidacji

**Brakujące:**
- README.md - Główny opis projektu
- CONTRIBUTING.md - Jak kontrybuować
- CHANGELOG.md - Historia zmian
- API.md - Dokumentacja API
- CBMS.md - Dokumentacja CBMS

### 6.3 Testy

**Status:** ❌ BRAK TESTÓW!

Brak folderów:
- `tests/`
- `test_*.py`

**Akcja:** Dodać testy jednostkowe i integracyjne

---

## 7. PROBLEMY KONFIGURACJI

### 7.1 Git

**Problem:** venv/ w repozytorium (1.27GB!)

**Akcja:**
```bash
echo "venv/" >> .gitignore
echo "*.pyc" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "*.db" >> .gitignore
echo "data/chroma/*.bin" >> .gitignore
git rm -r --cached venv/
git commit -m "Remove venv from repo"
```

### 7.2 Python Dependencies

**requirements.txt:**
```
fastapi==0.115.0
uvicorn[standard]==0.30.6
chromadb==0.5.3
sentence-transformers==3.0.1
pydantic==2.8.2
mcp>=1.23.0
```

**Brakujące** (używane ale nie w requirements.txt):
- `playwright` - używany w MCP server
- `httpx` - fallback w web_fetch
- `numpy` - używany przez indeksy

**Akcja:** Zaktualizować requirements.txt

### 7.3 Ścieżki hardcoded

**Problemy w kodzie:**
```python
# mcpServers/VS_CODE_MCP_CODEX/src/server.py
AIONS_V10 = Path("E:/AIONS_V10/AIONS_CBMS_RELEASE_V3")  # ❌ Hardcoded
EVERYTHING_CLI = Path("C:/Program Files/Everything/es.exe")  # ❌ Hardcoded
GIT_EXE = Path("C:/Program Files/Git/bin/git.exe")  # ❌ Hardcoded
NMAP_EXE = Path("C:/Program Files (x86)/Nmap/nmap.exe")  # ❌ Hardcoded
```

**Akcja:** Przenieść do zmiennych środowiskowych lub config.yaml

---

## 8. REKOMENDACJE

### 8.1 KRYTYCZNE (Zrób TERAZ)

1. **Wykonaj konsolidację**
   ```powershell
   cd E:\
   .\AIONS_MASTER_EXECUTE.ps1
   ```
   To skonsoliduje wszystkie wersje AIONS do `E:\AIONS_MASTER\`

2. **Usuń venv z repo**
   ```bash
   echo "venv/" >> .gitignore
   git rm -r --cached venv/
   git commit -m "Remove venv from repository"
   ```

3. **Dodaj README.md**
   ```markdown
   # AIONS - AI Operating System
   
   Rewolucyjna architektura AI z deterministyczną pamięcią.
   
   ## Komponenty
   - CBMS (Chunk-Based Memory System)
   - Korean Keys (97-98% kompresja)
   - ChromaDB (semantic search)
   - Auto-logging
   - MCP Server (32 narzędzia)
   ```

### 8.2 WYSOKIE (Zrób w tym tygodniu)

4. **Zintegruj CBMS**
   - Skopiuj z `E:\AIONS_V10\AIONS_CBMS_RELEASE_V3\`
   - Lub stwórz symlink
   - Zaktualizuj ścieżki w MCP server

5. **Zaktualizuj requirements.txt**
   ```
   playwright>=1.40.0
   httpx>=0.25.0
   numpy>=1.24.0
   ```

6. **Dodaj testy**
   ```
   tests/
   ├── test_store.py
   ├── test_context_schema.py
   ├── test_mcp_server.py
   └── test_korean_keys.py
   ```

### 8.3 ŚREDNIE (Zrób w tym miesiącu)

7. **Zarchiwizuj martwy kod**
   ```
   mkdir archive/
   mv AIOrchestrator/ archive/
   mv "tu huje/" archive/benchmarks/
   mv chatgpt_extracted/ archive/
   mv ustawienia_md/ archive/
   ```

8. **Usuń duplikaty**
   ```
   rm -rf marcin_memory_mcp/
   # Zachowaj files_extracted/marcin_memory_mcp/
   ```

9. **Przenieś hardcoded ścieżki do config**
   ```yaml
   # config.yaml
   paths:
     aions_v10: "E:/AIONS_V10/AIONS_CBMS_RELEASE_V3"
     everything_cli: "C:/Program Files/Everything/es.exe"
     git_exe: "C:/Program Files/Git/bin/git.exe"
   ```

10. **Dodaj dokumentację**
    - API.md
    - CBMS.md
    - CONTRIBUTING.md
    - CHANGELOG.md

---

## 9. PROPONOWANA DOCELOWA STRUKTURA

```
E:\AIONS_MASTER\
├── production/          # Symlink → Desktop AIONS_CBMS_RELEASE_V3
├── versions/            # Wszystkie wersje AIONS
│   ├── V0/
│   ├── V1/
│   ├── V2/
│   ├── V3/
│   └── VANILA/
├── plasters/            # Symlinki → E:\AJAJAJ\plasters_*
│   ├── 200g/
│   ├── howto/
│   ├── programming/
│   ├── general/
│   └── claude/
├── history/             # Poprzednie systemy
│   ├── POLIPEK_V1/
│   ├── MAIPA/
│   ├── AIONS_COMPLETE/
│   └── CBMS_Pocket_QC_Lab/
├── recovery/            # Snapshoty CBMS_RECOVERY
├── reports/             # Raporty audytowe
├── config/              # Konfiguracje
│   ├── aions_paths.json
│   └── aions_history.json
├── scripts/             # Skrypty utility
│   ├── unified_start.ps1
│   └── inventory.ps1
├── docs/                # Dokumentacja
└── backups/             # Backupy

E:\server wiedzy\        # Obecne repo - CZYSTE
├── server/              # Core backend
├── mcpServers/          # MCP servers
├── scripts/             # Utility scripts
├── data/                # ChromaDB + indeksy
├── logs/                # Auto-logging
├── docs/                # Dokumentacja
├── tests/               # Testy
├── .kiro/               # Kiro config
├── .gitignore           # ✅ Z venv/
├── README.md            # ✅ Główny opis
├── requirements.txt     # ✅ Zaktualizowany
└── config.yaml          # ✅ Konfiguracja
```

---

## 10. PODSUMOWANIE STATYSTYK

### Rozmiary

| Kategoria | Rozmiar | % |
|-----------|---------|---|
| venv/ | 1.27GB | 44% |
| "tu huje/" | 764MB | 26% |
| FULL_SCAN_*/ | 472MB | 16% |
| index/ | 179MB | 6% |
| data/chroma/ | 38.6MB | 1% |
| Reszta | ~200MB | 7% |
| **TOTAL** | **~2.9GB** | **100%** |

**Po czyszczeniu:** ~700MB (usunięcie venv, archiwizacja)

### Pliki

| Typ | Liczba |
|-----|--------|
| Python (.py) | ~150 (większość w venv) |
| Markdown (.md) | ~50 |
| JSON (.json) | ~30 |
| PowerShell (.ps1) | ~15 |
| JSONL (.jsonl) | ~10 |
| SQLite (.db) | ~5 |
| Inne | ~100 |

### ChromaDB

- **Sesje:** 25
- **Dokumenty:** 162
- **Metadane:** 1,557
- **Rozmiar:** 38.6MB

### Auto-logging

- **Dni aktywne:** 6 (28.11 - 03.12)
- **Total entries:** ~1,500
- **Rozmiar:** ~120KB

---

## 11. NASTĘPNE KROKI

### Dzisiaj (2025-12-04)

1. ✅ Analiza zakończona - ten dokument
2. ⏳ Przeczytaj `AIONS_MASTER_INSTRUCTIONS.md`
3. ⏳ Uruchom `AIONS_MASTER_EXECUTE.ps1` (jako Administrator)
4. ⏳ Dodaj venv/ do .gitignore

### Jutro (2025-12-05)

5. ⏳ Usuń venv z repo (git rm -r --cached venv/)
6. ⏳ Dodaj README.md
7. ⏳ Zaktualizuj requirements.txt

### Ten tydzień

8. ⏳ Zintegruj CBMS
9. ⏳ Dodaj testy
10. ⏳ Zarchiwizuj martwy kod

---

## KONTAKT

**Projekt:** AIONS (AI Operating System)  
**Autor:** Marcin Szul  
**Data analizy:** 2025-12-04  
**Lokalizacja:** E:\server wiedzy\  
**Status:** GOTOWY DO KONSOLIDACJI

---

**🚀 READY FOR CONSOLIDATION!**

Wykonaj: `.\AIONS_MASTER_EXECUTE.ps1` aby rozpocząć konsolidację.
