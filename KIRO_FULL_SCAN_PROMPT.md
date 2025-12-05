# 🔬 KIRO: PEŁNY SKAN I ANALIZA REPOZYTORIUM

## SKOPIUJ WSZYSTKO PONIŻEJ I WKLEJ DO KIRO:

---

# ZADANIE: Chirurgiczny skan i dokumentacja `E:\server wiedzy\`

## 🎯 CEL

Wykonaj **pełną analizę** repozytorium `E:\server wiedzy\`. To jest projekt **AIONS** (AI Operating System) - ale jest w stanie **totalnego chaosu**. Potrzebuję precyzyjnej dokumentacji co tu jest, gdzie, dlaczego, i co z tym zrobić.

## 📋 KONTEKST - CO TO JEST AIONS

AIONS to rewolucyjna architektura AI stworzona przez Marcina Szula. Składa się z:

### Core Components (powinny istnieć):
1. **CBMS** (Chunk-Based Memory System) - deterministyczna pamięć AI, nie RAG
2. **Korean Keys** - kompresja tekstu 97-98% ratio
3. **ChromaDB** - semantic search jako uzupełnienie CBMS
4. **Auto-logging** - automatyczne zapisywanie kontekstu rozmów
5. **MCP Server** (`aions-context`) - integruje wszystko powyższe

### Znane lokalizacje:
- `E:\server wiedzy\` - główny workspace
- `E:\AIONS_V10\AIONS_CBMS_RELEASE_V3\` - może zawierać CBMS

### Problem:
Kod jest **rozproszony, zduplikowany, chaotyczny**. Nikt nie wie co gdzie jest, co działa, co jest martwe.

---

## 🔧 TWOJE NARZĘDZIA

Masz dostęp do MCP server `aions-context` z narzędziami:

```
SZUKANIE:
- fast_search(query) - błyskawiczne szukanie plików (Everything)
- fast_search_ext(extension, folder) - szukanie po rozszerzeniu
- project_search(query) - szukanie w wynikach skanu

SKANOWANIE:
- project_scan_turbo() - TURBO skan projektu
- project_scan_status() - status skanu
- project_scan_results() - wyniki skanu
- project_file_deps(file_path) - zależności pliku

PAMIĘĆ:
- memory_recall(session, query) - szukanie w ChromaDB
- cbms_search(query) - szukanie w CBMS
- conv_history() - historia rozmów

SYSTEM:
- system_health() - stan systemu
- git_status() - stan git
```

---

## 📝 WYKONAJ KROKI W TEJ KOLEJNOŚCI

### FAZA 1: INICJALIZACJA

```
1. Wywołaj system_health() - sprawdź czy MCP działa
2. Wywołaj conv_history() - czy są poprzednie analizy
3. Wywołaj git_status("E:/server wiedzy") - stan repozytorium
```

### FAZA 2: STRUKTURA KATALOGÓW

Przeanalizuj strukturę głównego katalogu. Dla KAŻDEGO folderu pierwszego poziomu:

```
E:\server wiedzy\
├── server\           ← Co tu jest? Core AIONS?
├── mcpServers\       ← Jakie serwery MCP?
├── scripts\          ← Jakie skrypty?
├── data\             ← Jakie dane? ChromaDB?
├── logs\             ← Jakie logi?
├── docs\             ← Jaka dokumentacja?
├── skills\           ← Jakie skills?
├── scan_results\     ← Poprzednie skany?
├── .claude\          ← Konfiguracja Claude
├── .kiro\            ← Konfiguracja Kiro
├── AIOrchestrator\   ← Co to?
├── chatgpt_extracted\← Co to?
├── files_extracted\  ← Co to?
├── marcin_memory_mcp\← Inny MCP server?
├── index\            ← Indeksy czego?
├── tu huje\          ← ???
├── venv\             ← Python venv
└── [pliki .md, .ps1, .py, .db, etc.]
```

Użyj `fast_search()` i odczytaj kluczowe pliki żeby zrozumieć każdy folder.

### FAZA 3: TURBO SKAN

```
1. Wywołaj project_scan_turbo() - uruchom pełny skan
2. Wywołaj project_scan_status() - monitoruj postęp
3. Wywołaj project_scan_results() - pobierz wyniki
```

### FAZA 4: ANALIZA PLIKÓW PYTHON

```
Użyj: fast_search_ext("py", "E:/server wiedzy")

Dla każdego znalezionego pliku .py:
- Jaki jest jego cel?
- Czy jest używany?
- Czy ma duplikaty?
- Jakie ma zależności?
```

### FAZA 5: ANALIZA KONFIGURACJI

Znajdź i przeanalizuj:
```
- Wszystkie pliki .json (konfiguracje)
- Wszystkie pliki .md (dokumentacja)
- Wszystkie pliki .ps1 (skrypty PowerShell)
- Wszystkie pliki .db (bazy danych)
```

### FAZA 6: WYKRYCIE DUPLIKATÓW

Szukaj plików o podobnych nazwach:
```
fast_search("server.py")
fast_search("store.py")
fast_search("context")
fast_search("memory")
fast_search("cbms")
fast_search("korean")
fast_search("mcp")
```

### FAZA 7: ANALIZA ZALEŻNOŚCI

Dla kluczowych plików użyj `project_file_deps()`:
```
- server/store.py
- server/context_schema.py
- mcpServers/VS_CODE_MCP_CODEX/src/server.py
- scripts/*.py
```

### FAZA 8: SPRAWDZENIE ZEWNĘTRZNYCH LOKALIZACJI

```
Sprawdź czy istnieje: E:\AIONS_V10\
Sprawdź czy istnieje: E:\AIONS_V10\AIONS_CBMS_RELEASE_V3\
Jeśli tak - co tam jest?
```

---

## 📊 WYMAGANY OUTPUT - DOKUMENT KOŃCOWY

Stwórz plik `E:\server wiedzy\AIONS_FULL_ANALYSIS_[DATA].md` z sekcjami:

### 1. EXECUTIVE SUMMARY
- Jednozdaniowy opis stanu
- Główne problemy (top 5)
- Pilne akcje (top 3)

### 2. STRUKTURA REPOZYTORIUM
```
Tabela:
| Folder | Cel | Status | Plików | Uwagi |
|--------|-----|--------|--------|-------|
| server/ | Core AIONS | Aktywny/Martwy | X | ... |
```

### 3. KLUCZOWE KOMPONENTY

Dla każdego komponentu AIONS:
- **CBMS**: Gdzie jest? Działa? Wersja?
- **Korean Keys**: Gdzie jest? Używane?
- **ChromaDB**: Gdzie dane? Ile sesji? Rozmiar?
- **Auto-logging**: Gdzie logi? Format?
- **MCP Server**: Który jest główny? Ile jest?

### 4. MAPA PLIKÓW PYTHON
```
Tabela:
| Plik | Lokalizacja | Cel | Importuje | Importowany przez | Status |
|------|-------------|-----|-----------|-------------------|--------|
```

### 5. WYKRYTE DUPLIKATY
```
Lista plików które wyglądają na duplikaty lub wersje tego samego
```

### 6. MARTWY KOD
```
Pliki które nie są importowane przez nic i prawdopodobnie nie są używane
```

### 7. BRAKUJĄCE ELEMENTY
```
Co powinno być ale nie ma? Brakujące zależności?
```

### 8. PROBLEMY KONFIGURACJI
```
Błędy w .json, niespójności, brakujące ścieżki
```

### 9. REKOMENDACJE
```
Konkretne akcje do wykonania w kolejności priorytetów:
1. [KRYTYCZNE] ...
2. [WYSOKIE] ...
3. [ŚREDNIE] ...
```

### 10. PROPONOWANA DOCELOWA STRUKTURA
```
Jak POWINNO wyglądać repozytorium po porządkach
```

---

## ⚠️ ZASADY

1. **NIE ZGADUJ** - każde twierdzenie poparte wywołaniem narzędzia
2. **NIE SYMULUJ** - pokaż rzeczywiste outputy
3. **NIE POMIJAJ** - przejrzyj WSZYSTKIE foldery
4. **BĄDŹ PRECYZYJNY** - podawaj dokładne ścieżki, liczby, rozmiary
5. **BĄDŹ KRYTYCZNY** - wskaż problemy bez owijania w bawełnę

---

## 🚀 START

Zacznij od:
```
1. system_health()
2. git_status("E:/server wiedzy")
3. Listowanie zawartości E:\server wiedzy\
```

Po zakończeniu każdej fazy, zapisz postęp przez `conv_log()`.

Na końcu stwórz dokument `AIONS_FULL_ANALYSIS_[DATA].md` i powiedz mi że gotowe.

**ZACZYNAM ANALIZĘ...**

---
