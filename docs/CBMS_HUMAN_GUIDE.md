# CBMS — przewodnik dla Marcina (człowiek)

**Data:** 2026-07-10  
**Dla kogo:** Marcin — korzystanie z CBMS bez pośrednictwa agenta AI

CBMS (Cognitive Base Memory System) to kanoniczna baza wiedzy AIONS: **561 chunków** w plikach JSON + indeks wektorowy ChromaDB. Agent w Cursorze korzysta z tego codziennie przez MCP; Ty możesz to samo robić ręcznie lub przez GUI.

---

## Ścieżki (canonical)

| Co | Ścieżka |
|----|---------|
| CBMS / `AIONS_PATH` | `E:\server wiedzy\aions_core` |
| Chunki (pełna treść) | `E:\server wiedzy\aions_core\memory\chunks\` |
| Indeks chunków | `E:\server wiedzy\aions_core\memory\knowledge_manifest.json` |
| ChromaDB (wektory) | `E:\server wiedzy\data\chroma` |
| Prod MCP (Cursor) | `aions-context` → venv `E:\server wiedzy\venv` |
| Dev MCP (WSL staging) | `aions-dev` → `D:\AIONS_DEV\` |

**Uwaga:** starsze chunki (np. `KCBMSACCESS001`) mogą w treści wspominać `D:\AIONS-INTEGRATION\` — to legacy. Kanoniczna ścieżka od migracji 2026-07 to **`E:\server wiedzy\aions_core`**.

---

## Sposób 1 — Przeglądanie chunków ręcznie (najprostszy)

1. Otwórz Explorer: `E:\server wiedzy\aions_core\memory\chunks\`
2. Każdy plik to jeden chunk, np. `KCBMSPIPE001.json`
3. Struktura JSON:
   - `id` — identyfikator (np. `KBOOTSTRAP`, `KCBMSACCESS001`)
   - `concept` — kategoria (`general`, `cbms_pipeline`, `plasters`, …)
   - `content` — **pełna treść wiedzy** (czasem 2000+ znaków)
   - `references` — ścieżki do plików źródłowych w repo
   - `access_count` / `last_accessed` — statystyki użycia

**Szybki start — ważne chunki:**

| ID | Temat |
|----|-------|
| `KBOOTSTRAP` | Checkpoint startowy CBMS |
| `KCBMSACCESS001` | Jak AI (i Ty) czytacie pełne chunki po wyszukaniu |
| `KCBMSPIPE001` | Pipeline CBMS |

**Indeks:** `knowledge_manifest.json` — lista wszystkich 561 chunków z `concept`, `size`, ścieżką do pliku. Wyszukaj w pliku po słowie kluczowym lub `concept`.

---

## Sposób 2 — ChromaFlowStudio (GUI ChromaDB)

Lokalna aplikacja w repo: `E:\server wiedzy\tools\ChromaFlowStudio\`

**Do czego:** przeglądanie kolekcji Chroma, similarity search, eksport JSON, wizualizacja embeddingów — **nie** edycja chunków CBMS (to osobne pliki JSON).

**Uruchomienie (jeśli venv już istnieje):**

```powershell
cd "E:\server wiedzy\tools\ChromaFlowStudio"
.\Run.bat
```

Pierwsza instalacja: patrz `tools\ChromaFlowStudio\README.md` (`VENV_Create.bat` → `Install.bat`).

**W Settings aplikacji** ustaw ścieżkę do bazy Chroma:

```
E:\server wiedzy\data\chroma
```

Przydatne kolekcje (po ingest tier-1):

- `claude_marcin_main` — pamięć sesji / autolog
- `aions_operator` — profil operatora + metadata skarbów

---

## Sposób 3 — MCP w Cursorze (jak agent, ale Ty pytasz)

W Cursorze włączony serwer **`aions-context`** (prod). W czacie możesz prosić agenta o:

| Narzędzie MCP | Co robi |
|---------------|---------|
| `cbms_search` | Wyszukaj chunki po zapytaniu → zwraca ID + krótką odpowiedź |
| `cbms_get_chunk` | Pobierz pełną treść chunka po ID |
| `memory_recall` | Semantyczne wyszukiwanie w Chroma (`claude_marcin_main`) |
| `memory_store` | Zapisz notatkę do pamięci długoterminowej |
| `session_bootstrap` | Health + autolog + profil operatora na start sesji |

**Typowy workflow (taki sam jak dla AI):**

1. `cbms_search` z zapytaniem, np. „packer build” lub „plasters pipeline”
2. Z listy ID otwórz plik: `aions_core\memory\chunks\{ID}.json`
3. Śledź `references` → kod źródłowy w repo

Reload MCP: **Cursor Settings → MCP → aions-context → Reload** (po zmianie `mcp.json` lub venv).

Szczegóły prod vs dev MCP: [`README_DEV.md`](../README_DEV.md) § Cursor MCP.

---

## Sposób 4 — Python (opcjonalnie, terminal)

Z katalogu repo, z aktywnym venv:

```powershell
cd "E:\server wiedzy"
.\venv\Scripts\activate
$env:AIONS_PATH = "E:\server wiedzy\aions_core"
python -c "from aions_core.server.cbms_memory import search_chunks; print(search_chunks('bootstrap', limit=3))"
```

(Ścieżka importu może wymagać `PYTHONPATH` — jeśli błąd, użyj MCP lub przeglądania plików.)

---

## Czego CBMS **nie** robi sam

- Nie synchronizuje się automatycznie z Chroma po ręcznej edycji pliku `.json` — ingest to osobny krok
- Nie zastępuje git / notatek — chunki to kuratorowana wiedza, nie logi
- ChromaFlowStudio pokazuje **wektory**, nie zastępuje czytania `content` w chunkach

---

## Powiązane dokumenty

| Dokument | Temat |
|----------|-------|
| [`AGENTS.md`](../AGENTS.md) | Ścieżki canonical, MCP health gate |
| [`.claude/specs/AIONS_OS_ROADMAP.md`](../.claude/specs/AIONS_OS_ROADMAP.md) | Roadmapa faz |
| [`aions_core/memory/CBMS_SEED_DISCOVERY.md`](../aions_core/memory/CBMS_SEED_DISCOVERY.md) | Historia seedowania chunków |
| [`README_DEV.md`](../README_DEV.md) | sync E:→D:, prod vs dev MCP |

*Gdy powstanie `docs/OPERATOR_NEXT_STAGES.md` — tam będzie plan zmysłów operatora i schedulera; ten przewodnik zostaje przy CBMS/pamięci.*
