# BACKUP_MANIFEST

| Pole | Wartość |
|------|---------|
| **Timestamp** | 2026-07-02 00:45:45 (local) |
| **Folder** | `backup_20260702_004545_desktop_mcp` |
| **Powód** | pre-desktop_* deployment + plan execution |
| **Wykonane przez** | Agent (backup point — bez deploy/restart MCP) |

## Skopiowane pliki (wszystkie istniały)

| Plik źródłowy | Plik w backupie |
|---------------|-----------------|
| `mcpServers/VS_CODE_MCP_CODEX/src/server.py` | `mcpServers/VS_CODE_MCP_CODEX/src/server.py` |
| `mcpServers/VS_CODE_MCP_CODEX/src/desktop_control.py` | `mcpServers/VS_CODE_MCP_CODEX/src/desktop_control.py` |
| `mcpServers/VS_CODE_MCP_CODEX/src/__main__.py` | `mcpServers/VS_CODE_MCP_CODEX/src/__main__.py` |
| `requirements.txt` | `requirements.txt` |
| `scripts/full_system_scan.py` | `scripts/full_system_scan.py` |
| `scripts/turbo_scanner.py` | `scripts/turbo_scanner.py` |
| `scripts/launch_full_system_scan.ps1` | `scripts/launch_full_system_scan.ps1` |
| `.cursor/hooks.json` | `.cursor/hooks.json` |
| `.cursor/hooks/autolog_bootstrap.py` | `.cursor/hooks/autolog_bootstrap.py` |
| `start_aions_mcp.bat` | `start_aions_mcp.bat` |
| `C:\Users\User\.cursor\mcp.json` | `mcp.json.cursor.backup` |

## Git (bez commita)

- `backup.patch` — `git diff` ze stanu roboczego (166201 B)
- Commit **nie** utworzony (Marcin nie prosił; wiele zmian poza tym backupem)

## Liczba plików w backupie

- **12** plików (10 kopii projektu + mcp.json.cursor.backup + backup.patch; manifest poza liczbą)

## Nie wykonano

- Restart MCP / deploy
- Modyfikacja plików produkcyjnych
- `git push`

## MCP po python-automat (2026-07-02)

- **SSOT:** `E:\server wiedzy\.aions\python.env` (wersja 3.11, ścieżki venv Win/WSL)
- **Cursor `mcp.json`:** jawny `E:\server wiedzy\venv\Scripts\python.exe` + `__main__.py` (nie bare `python`, nie system Python311)
- **Po zmianie mcp.json:** Cursor → Settings → MCP → `aions-context` → Reload
- **Launcher:** `scripts\aions_python.ps1` — wszystkie skrypty startowe powinny przez niego przechodzić
