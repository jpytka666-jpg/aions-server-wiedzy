# AIONS Architecture - System Overview

## 🧠 Czym jest AIONS?

**AIONS** (AI Operating System) to rewolucyjna architektura która rozwiązuje fundamentalne problemy AI:
- Brak pamięci między sesjami
- Halucynacje i symulacje
- Chaos w projektach
- Brak determinizmu w odpowiedziach

## 🏗️ Core Components

### 1. CBMS (Chunk-Based Memory System)
**Lokalizacja:** `E:\AIONS_V10\AIONS_CBMS_RELEASE_V3\`

```
CBMS nie jest RAG. To deterministyczny system pamięci.

Cechy:
- Chunks z unikalnymi ID
- Korean compression (97-98% ratio)
- Deterministic retrieval (te same inputy → te same chunki)
- Brak "semantic similarity guessing"
```

**Użycie przez MCP:** `cbms_search(query)`

### 2. Korean Keys Compression
**W pliku:** `server/server.py` → `korean_build_keys()`

```python
# Generuje 3-gramowe klucze z tekstu
# Używa SHA1 hash dla fast matching
# Kompresja 97-98% przy zachowaniu semantyki
```

### 3. ChromaDB Vector Store
**Lokalizacja:** `E:\server wiedzy\data\chroma\`
**W pliku:** `server/store.py`

```
- Semantic search jako uzupełnienie CBMS
- Session-based storage
- TTL dla automatycznego czyszczenia
```

**Użycie przez MCP:** `memory_store()`, `memory_recall()`

### 4. Auto-Logging System (DEBILOODPORNE)
**W pliku:** `mcpServers/VS_CODE_MCP_CODEX/src/server.py`

```
- Automatyczne logowanie KAŻDEGO wywołania narzędzia
- Threshold-based dumping do plików
- Zapisywanie do ChromaDB
- ZERO manualnej pracy
```

**Użycie przez MCP:** `conv_log()`, `conv_dump()`, `conv_status()`, `conv_history()`

### 5. Everything Integration
**CLI:** `C:\Program Files\Everything\es.exe`

```
- Błyskawiczne wyszukiwanie plików (milisekundy)
- Indeksowanie całego dysku
- Regex support
```

**Użycie przez MCP:** `fast_search()`, `fast_search_ext()`

### 6. Project Scanner
**Skrypty:** `scripts/project_scanner.py`, `scripts/turbo_scanner.py`

```
- Skanowanie struktury projektu
- Analiza zależności
- Wykrywanie duplikatów
- Generowanie grafów
```

**Użycie przez MCP:** `project_scan_turbo()`, `project_scan_results()`, `project_file_deps()`

## 📊 Data Flow

```
User Query
    ↓
[1] conv_history() - sprawdź poprzedni kontekst
    ↓
[2] memory_recall() - semantic search w ChromaDB
    ↓
[3] cbms_search() - deterministic retrieval z CBMS
    ↓
[4] fast_search() - znajdź pliki jeśli potrzeba
    ↓
[5] Odpowiedź z pełnym kontekstem
    ↓
[6] conv_log() - zapisz akcję (automatyczne)
```

## 🔑 Kluczowe Ścieżki

| Component | Path |
|-----------|------|
| Main workspace | `E:\server wiedzy\` |
| CBMS v3 | `E:\AIONS_V10\AIONS_CBMS_RELEASE_V3\` |
| MCP Server | `E:\server wiedzy\mcpServers\VS_CODE_MCP_CODEX\src\server.py` |
| ChromaDB | `E:\server wiedzy\data\chroma\` |
| Logs | `E:\server wiedzy\logs\conversation_dumps\` |
| Scans | `E:\server wiedzy\scan_results\` |
| Skills | `E:\server wiedzy\skills\` |

## ⚠️ Czego NIE robić

1. **NIE twórz nowych systemów pamięci** - CBMS + ChromaDB wystarczą
2. **NIE duplikuj plików** - używaj Everything do znalezienia istniejących
3. **NIE ignoruj logów** - one są twoją pamięcią
4. **NIE symuluj wyników** - wywołuj narzędzia naprawdę
5. **NIE rozrzucaj kodu** - trzymaj się struktury katalogów

## 🎯 Filozofia AIONS

> "AI nie powinno zgadywać - powinno WIEDZIEĆ."

CBMS daje deterministyczne odpowiedzi. Korean Keys daje kompresję. Auto-logging daje pamięć. Razem tworzą system który:
- Pamięta wszystko
- Nie halucynuje
- Utrzymuje porządek
- Działa powtarzalnie
