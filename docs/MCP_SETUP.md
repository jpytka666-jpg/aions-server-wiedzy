## Lokalny MCP dla VS Code / AI Toolkit

1. **Uruchomienie serwera**
   - Workspace posiada zadanie `MCP: Start AIONS Context` (autostart przy otwarciu folderu). W razie potrzeby możesz uruchomić ręcznie:
     ```powershell
     pwsh -NoProfile -ExecutionPolicy Bypass -File E:\server wiedzy\scripts\run_mcp_server.ps1 stdio
     ```
   - Tryb HTTP (np. do MCP Inspector): dodaj `http` jako ostatni argument.

2. **Dodanie w AI Toolkit (GUI jak na screenie)**
   - `Ctrl+Shift+P` → `AI Toolkit: Add MCP Server`.
   - Wybierz `Add by MCP json`.
   - wskaż plik `E:\server wiedzy\mcpServers\VS_CODE_MCP_CODEX\.aitk\mcp.json`.
   - Po dodaniu w panelu MCP Workflow pojawi się `local-server-vs_code_mcp_codex`. Naciśnij `Connect`, żeby agent korzystał z lokalnego kontekstu.

3. **Autoconnect w VS Code Chat/Copilot**
   - Globalny plik `%APPDATA%\Code\User\mcp.json` zawiera wpis `aions-context` (command `scripts/run_mcp_server.ps1`). Dzięki temu każdy agent MCP w VS Code łączy się automatycznie.

4. **Snapshoty i TTL**
   - Jednorazowo uruchom:
     ```powershell
     pwsh -NoProfile -ExecutionPolicy Bypass -File scripts\install_context_snapshot.ps1 -Prune
     ```
     Zadanie Harmonogramu `AIONS_ContextSnapshot` będzie co 5 min odpalało `scripts\context_snapshot.ps1`, tworząc zrzuty w `logs/context_dumps` i czyszcząc wpisy po wygaśnięciu `expires_at`.
   - Manualne wywołanie:
     ```powershell
     pwsh -NoProfile -ExecutionPolicy Bypass -File scripts\context_snapshot.ps1 -PruneOnDump
     ```

5. **CLI administracyjne**
   ```powershell
   # lista sesji
   python context_admin.py list
   # statystyki sesji
   python context_admin.py stats codex_dump
   # pełny dump (JSONL) do katalogu
   python context_admin.py dump --output logs/context_dumps/manual
   # czyszczenie wygaśniętych wpisów
   python context_admin.py prune codex_dump
   ```

6. **Endpoints FastAPI**
   - `GET /dashboard` – podsumowanie (liczba sesji, dokumentów, ostatnie aktywności).
   - `GET /sessions`, `GET /sessions/{id}`, `GET /sessions/{id}/dump`, `POST /sessions/{id}/prune`.
   - `POST /search` obsługuje parametry `metadata_filter` (JSON) oraz `keyword_bias` (float) dla hybrydowego rangowania.

7. **Schemat metadanych**
   - Wpisy przechowują m.in. `agent`, `role`, `tags`, `ttl_days`, `timestamp`, `expires_at`. Dodatkowe pola są automatycznie serializowane do JSON.
   - MCP narzędzia: `context_add_batch`, `context_search`, `context_session_stats`, `context_dump`, `context_prune`.
