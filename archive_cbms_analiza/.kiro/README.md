# AIONS Kiro Configuration

## 🎯 Co to jest?

Konfiguracja Kiro IDE dla projektu AIONS - wymuszająca prawidłowy workflow AI.

## 📁 Struktura

```
.kiro/
├── settings/
│   └── mcp.json              ← Konfiguracja aions-context MCP server
├── steering/
│   ├── claude-workflow.md    ← Zasady workflow AI (CZYTAJ ZAWSZE)
│   ├── aions-architecture.md ← Architektura systemu AIONS
│   └── tools-priority.md     ← Kolejność użycia narzędzi
├── specs/
│   └── claude-behavior/
│       ├── requirements.md   ← Wymagania zachowania AI
│       ├── design.md         ← Design systemu
│       └── tasks.md          ← Konkretne taski do wykonania
├── hooks/
│   ├── on-session-start.json ← Wymusza inicjalizację sesji
│   ├── on-file-modify.json   ← Wymusza sprawdzenie zależności
│   ├── on-session-end.json   ← Wymusza zapisanie kontekstu
│   └── anti-simulation.json  ← Blokuje symulowanie wyników
└── README.md                 ← Ten plik
```

## 🚀 Jak używać?

### 1. Otwórz projekt w Kiro
```
Kiro → Open Folder → E:\server wiedzy\tu huje\
```

### 2. Sprawdź MCP
```
Panel MCP Servers → aions-context powinien być zielony
```

### 3. Zacznij pracę
Kiro automatycznie:
- Wczyta steering docs
- Zastosuje hooks
- Użyje aions-context MCP jako głównego źródła narzędzi

## 🔧 MCP Server: aions-context

### Dostępne narzędzia:

| Kategoria | Narzędzia |
|-----------|-----------|
| **Search** | `fast_search`, `fast_search_ext`, `project_search` |
| **Memory** | `memory_store`, `memory_recall`, `cbms_search`, `session_list` |
| **Logging** | `conv_log`, `conv_dump`, `conv_status`, `conv_history`, `conv_set_threshold` |
| **Project** | `project_scan_turbo`, `project_scan_status`, `project_scan_results`, `project_file_deps` |
| **Git** | `git_status`, `git_log` |
| **Docker** | `docker_ps`, `docker_images` |
| **WSL** | `wsl_run`, `wsl_list` |
| **Browser** | `browser_navigate`, `browser_snapshot`, `browser_click`, `browser_type`, `browser_screenshot`, `browser_get_text`, `browser_close`, `browser_evaluate` |
| **Web** | `web_fetch` |
| **MCP Catalog** | `mcp_find`, `mcp_list`, `mcp_info` |
| **System** | `system_health`, `network_ping` |

### Auto-approved tools (nie wymagają potwierdzenia):
- Wszystkie read-only tools (search, status, recall)

## 📋 Workflow AI

### Start sesji:
1. `system_health()` - sprawdź czy MCP działa
2. `conv_history()` - wczytaj poprzedni kontekst
3. `memory_recall(session, topic)` - wczytaj relevantne memories

### Podczas pracy:
1. **ZAWSZE** używaj aions-context MCP przed innymi narzędziami
2. **ZAWSZE** pokazuj wyniki narzędzi jako dowód
3. **NIGDY** nie symuluj wyników

### Koniec sesji:
1. `conv_log("assistant", "Session summary: ...")` - zapisz podsumowanie
2. `conv_dump()` - wymuś zapis do ChromaDB
3. `conv_status()` - potwierdź że zapisane

## ⚠️ Ważne zasady

1. **NIE symuluj** - każde twierdzenie musi mieć dowód z narzędzia
2. **NIE twórz bałaganu** - pliki w odpowiednich katalogach
3. **NIE ignoruj MCP** - to jest twoje główne źródło narzędzi
4. **ZAWSZE loguj** - `conv_log()` po ważnych akcjach

## 🔗 Powiązane pliki

- Server MCP: `E:\server wiedzy\mcpServers\VS_CODE_MCP_CODEX\src\server.py`
- ChromaDB: `E:\server wiedzy\data\chroma\`
- Logi: `E:\server wiedzy\logs\conversation_dumps\`
- Skills: `E:\server wiedzy\skills\`

## 👤 Autor

Marcin Szul / AIONS Project
Konfiguracja stworzona przez Claude (Opus 4.5) jako architekt.
