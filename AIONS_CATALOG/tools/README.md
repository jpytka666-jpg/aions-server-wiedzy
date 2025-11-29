# 🛠️ TOOLS - Narzędzia AIONS

## Narzędzia w serwerze wiedzy

### MCP Server v6
- **Ścieżka**: `E:\server wiedzy\mcpServers\VS_CODE_MCP_CODEX\src\server.py`
- **Funkcje**: Auto-logging, memory store/recall, file operations

### TURBO Scanner
- **Ścieżka**: `E:\server wiedzy\scripts\turbo_scanner.py`
- **Funkcje**: Skan plików z hashami, wykrywanie duplikatów

### ChatGPT Extractor
- **Ścieżka**: `E:\server wiedzy\scripts\chatgpt_ultimate.py`
- **Funkcje**: Ekstrakcja danych z LevelDB cache ChatGPT

## Narzędzia systemowe

### Everything CLI
- **Ścieżka**: `C:\Program Files\Everything\es.exe`
- **Funkcje**: Błyskawiczne wyszukiwanie plików

### mcp_client_tools.py
- **Ścieżka**: `C:\Users\User\mcp_client_tools.py`
- **Funkcje**: CLI do ChromaDB/MCP server

## Narzędzia AIONS

### AIONS Server
- **Ścieżka**: `...\AIONS_CBMS_RELEASE_V3\server\cbms_direct_server.py`
- **Port**: 9000

### Batch launchers
- `run_server.bat` / `run_server.ps1`
- `run_cbms_full_stack_window.bat`
- `LAUNCH_ULTIMATE_AIONS.bat`

### Test tools
- `quick_chat_test.py`
- `test_aions_capabilities.py`
- `test_plasters_integration.py`

## Narzędzia diagnostyczne

### Codex CLI history
- **Ścieżka**: `C:\Users\User\.codex\history.jsonl`
- **Rozmiar**: ~1 MB

### Komendy curl do testowania
```bash
# Health check
curl http://localhost:9000/health

# Chat query
curl -X POST http://localhost:9000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"Co to jest CBMS?"}'

# Plasters stats
curl http://localhost:9000/plasters/stats

# CRLA tournament
curl -X POST http://localhost:9000/crla/ask \
  -H "Content-Type: application/json" \
  -d '{"query":"test","seed":123,"candidates":8}'
```

## Skrypty pomocnicze

| Skrypt | Funkcja |
|--------|---------|
| save_claude_context.py | Zapisywanie kontekstu |
| claude_auto_capture_hook.py | Auto-capture promptów |
| claude_session_recovery.py | Odzyskiwanie sesji |
| context_admin.py | Administracja ChromaDB |
