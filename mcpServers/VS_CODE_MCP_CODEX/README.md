# AIONS Context MCP Server

Ten katalog dostarcza w pełni działający MCP server utrzymujący lokalny kontekst (Chroma + FastAPI) dla VS Code / AI Toolkit.

## Co zawiera

| Folder / Plik | Zawartość |
| ------------- | --------- |
| `src/` | Implementacja narzędzi (`context_*`) zintegrowanych z `server/store.py`. |
| `.aitk/mcp.json` | Konfiguracja do użycia w AI Toolkit (`Add by MCP json`). |
| `.vscode/` | Konfiguracje debugowania (Agent Builder, MCP Inspector). |
| `inspector/` | Frontend MCP Inspector (opcjonalny podgląd). |

## Dodanie w AI Toolkit (GUI)
1. `Ctrl+Shift+P` → `AI Toolkit: Add MCP Server`.
2. Wybierz **Add by MCP json**.
3. Wskaż `E:\server wiedzy\mcpServers\VS_CODE_MCP_CODEX\.aitk\mcp.json`.
4. Serwer pojawi się jako `local-server-vs_code_mcp_codex`; kliknij **Connect**.

## Ręczne uruchomienie

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File E:\server wiedzy\scripts\run_mcp_server.ps1 stdio
```

lub HTTP (dla Inspector):

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File E:\server wiedzy\scripts\run_mcp_server.ps1 http
```

## Narzędzia MCP
- `context_health`, `context_list_sessions`
- `context_session_stats`, `context_add_batch`, `context_search`
- `context_dump`, `context_prune`

Wszystkie opierają się na `VectorStore`, który automatycznie normalizuje metadane i utrzymuje TTL.

## Snapshoty
Zainstaluj harmonogram:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File E:\server wiedzy\scripts\install_context_snapshot.ps1 -Prune
```

co 5 min generuje dumpy w `logs/context_dumps` i czyści wygasłe wpisy.

## Diagnostics
FastAPI endpoint `GET /dashboard` udostępnia podsumowanie (liczba sesji, dokumentów, ostatnie aktywne sesje). Możesz też korzystać z CLI `context_admin.py`.
