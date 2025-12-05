# KIRO SELF-CONFIGURATION PROMPT

## Skopiuj ten prompt i wklej do Kiro:

---

# 🔧 ZADANIE: Skonfiguruj się sam dla projektu AIONS

## KONTEKST

Pracujesz nad projektem **AIONS** (AI Operating System) - rewolucyjną architekturą AI z:
- **CBMS** - Chunk-Based Memory System (deterministyczna pamięć)
- **Korean Keys** - kompresja 97-98%
- **ChromaDB** - semantic search
- **Auto-logging** - automatyczne zapisywanie kontekstu

Właściciel projektu: **Marcin Szul**
Lokalizacja: `E:\server wiedzy\`

## TWOJE ZADANIE

Przeczytaj `E:\server wiedzy\KIRO_CONFIGURATION_GUIDE.md` i na jego podstawie:

### 1. UTWÓRZ/ZAKTUALIZUJ STRUKTURĘ `.kiro/`

```
E:\server wiedzy\.kiro\
├── settings/
│   └── mcp.json              ← MCP server aions-context
├── steering/
│   ├── project-standards.md  ← Standardy projektu AIONS
│   ├── tools-priority.md     ← Kolejność użycia narzędzi
│   └── anti-simulation.md    ← Zakaz symulowania wyników
├── specs/
│   └── aions-behavior/
│       ├── requirements.md   ← Wymagania dla AI
│       ├── design.md         ← Design workflow
│       └── tasks.md          ← Checklisty
└── hooks/                    ← Hooki automatyzujące workflow
```

### 2. SKONFIGURUJ MCP SERVER `aions-context`

Plik: `.kiro/settings/mcp.json`

```json
{
  "mcpServers": {
    "aions-context": {
      "command": "E:/server wiedzy/venv/Scripts/python.exe",
      "args": ["-m", "mcp.server.stdio", "--server-script", "E:/server wiedzy/mcpServers/VS_CODE_MCP_CODEX/src/server.py"],
      "env": {
        "CHROMA_PATH": "E:/server wiedzy/data/chroma",
        "PYTHONPATH": "E:/server wiedzy;E:/server wiedzy/server"
      },
      "autoApprove": [
        "fast_search", "fast_search_ext", "git_status", "git_log",
        "project_scan_status", "project_scan_results", "project_search",
        "conv_status", "conv_history", "memory_recall", "session_list",
        "cbms_search", "system_health", "mcp_find", "mcp_list"
      ]
    }
  }
}
```

### 3. UTWÓRZ STEERING FILES

#### A) `steering/project-standards.md`
```markdown
# AIONS Project Standards

## Struktura projektu
- `server/` - Core AIONS (context_schema, store, CBMS)
- `mcpServers/` - MCP servers
- `scripts/` - Narzędzia pomocnicze
- `data/` - ChromaDB, dane
- `logs/` - Logi konwersacji
- `.kiro/` - Konfiguracja Kiro

## Zasady kodowania
- Python 3.11+
- Type hints obowiązkowe
- Docstrings dla funkcji publicznych
- Testy przed merge

## NIGDY
- Nie twórz plików w losowych lokalizacjach
- Nie duplikuj istniejących funkcji
- Nie używaj web search przed sprawdzeniem lokalnych źródeł
```

#### B) `steering/tools-priority.md`
```markdown
---
inclusion: always
---

# Kolejność Użycia Narzędzi

## PRIORYTET 1: aions-context MCP (ZAWSZE NAJPIERW!)
- `fast_search()` - szukanie plików
- `memory_recall()` - szukanie w pamięci
- `cbms_search()` - wiedza domenowa
- `project_search()` - szukanie w projekcie
- `conv_history()` - poprzedni kontekst

## PRIORYTET 2: Lokalne narzędzia Kiro
- Read/Write/Edit - tylko jeśli MCP nie wystarczy

## PRIORYTET 3: Web search
- TYLKO gdy user wprost poprosi
- TYLKO dla info zewnętrznych
```

#### C) `steering/anti-simulation.md`
```markdown
---
inclusion: always
---

# ❌ ZAKAZ SYMULACJI

## ZAKAZANE ZACHOWANIA:
1. Mówienie "znalazłem X" bez wywołania `fast_search()`
2. Mówienie "plik zawiera Y" bez wywołania `Read()`
3. Mówienie "zmodyfikowałem Z" bez wywołania `Edit()`
4. Zgadywanie ścieżek plików
5. Wymyślanie zawartości plików

## OBOWIĄZKOWE:
- Każde twierdzenie = dowód z narzędzia
- Nie wiesz = powiedz "nie wiem, sprawdzę"
- Pokaż OUTPUT narzędzia jako dowód
```

### 4. UTWÓRZ HOOKS

#### A) Hook na start sesji
Trigger: `On Session Created`
Action: `Send Message to Agent`
Message:
```
Na start sesji MUSISZ:
1. Wywołać system_health() z aions-context
2. Wywołać conv_history() żeby sprawdzić poprzedni kontekst
3. Dopiero potem odpowiadać na pytania
```

#### B) Hook na zapis pliku
Trigger: `On File Save`
Pattern: `**/*.py`
Action: `Send Message to Agent`
Message:
```
Plik Python zapisany. Sprawdź:
- Czy są type hints?
- Czy jest docstring?
- Czy wywołałeś conv_log() z opisem zmiany?
```

### 5. UTWÓRZ SPECS

#### `specs/aions-behavior/requirements.md`
```markdown
# Requirements: AI Behavior in AIONS

## FR-1: Session Initialization
- AI MUSI wywołać system_health() na start
- AI MUSI wywołać conv_history() przed odpowiedzią
- AI MUSI użyć memory_recall() dla kontekstu

## FR-2: Tool Priority
- AI MUSI preferować aions-context MCP
- AI NIE MOŻE używać web search przed lokalnymi źródłami

## FR-3: Anti-Simulation
- AI NIE MOŻE twierdzić bez dowodu z narzędzia
- AI MUSI pokazać output jako dowód
```

### 6. ZWERYFIKUJ KONFIGURACJĘ

Po utworzeniu wszystkich plików:

1. Sprawdź czy MCP server działa:
   - Panel MCP Servers → `aions-context` powinien być zielony

2. Przetestuj narzędzia:
   ```
   Wywołaj system_health() z aions-context
   ```

3. Sprawdź steering:
   - Panel Steering → powinny być widoczne wszystkie pliki

4. Sprawdź hooks:
   - Panel Hooks → powinny być skonfigurowane hooki

## DODATKOWE INSTRUKCJE

### Jeśli MCP nie działa:
1. Sprawdź czy `E:\server wiedzy\venv\Scripts\python.exe` istnieje
2. Sprawdź czy `E:\server wiedzy\mcpServers\VS_CODE_MCP_CODEX\src\server.py` istnieje
3. Uruchom ręcznie: `E:\server wiedzy\venv\Scripts\python.exe -c "from mcp.server.fastmcp import FastMCP; print('OK')"`

### Struktura AIONS do zapamiętania:
```
E:\server wiedzy\
├── server\                 ← Core (context_schema.py, store.py)
├── mcpServers\             ← MCP servers (aions-context)
├── scripts\                ← Narzędzia (scanner, turbo)
├── data\                   ← ChromaDB
├── logs\                   ← Conversation dumps
├── skills\                 ← Skill files
└── .kiro\                  ← TUTAJ TWOJA KONFIGURACJA
```

## PO ZAKOŃCZENIU

Potwierdź że:
- [ ] `.kiro/settings/mcp.json` istnieje i ma poprawną konfigurację
- [ ] `.kiro/steering/` ma 3 pliki markdown
- [ ] `.kiro/specs/aions-behavior/` ma requirements.md
- [ ] Hooks są skonfigurowane w UI
- [ ] MCP server `aions-context` jest zielony (działa)

---

**ZACZNIJ OD:** Otwórz `E:\server wiedzy\` jako workspace, potem wykonuj kroki po kolei.

---
