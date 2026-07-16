---
inclusion: always
---

# AIONS Technical Standards

## Technology Stack

### Core
- **Python 3.11** — unified version for Windows production and WSL dev (see Python Version Policy below)
- **FastMCP** - MCP server framework
- **ChromaDB** - Vector database for semantic search
- **Everything SDK** - Windows file search (via ES.exe)

### Infrastructure
- **WSL Ubuntu** - For AWS CLI and uvx tools
- **Aurora DSQL** - AWS distributed SQL database
- **Playwright** - Browser automation

### Development
- **VSCode/Cursor** - IDE with Claude Code
- **Kiro for CC** - Spec-driven development
- **Git** - Version control

## Architecture

### MCP Server Pattern
```
Claude Code <--stdio--> MCP Server <---> Backend Services
                              |
                              +--> ChromaDB
                              +--> Everything
                              +--> CBMS
                              +--> Playwright
```

### Data Flow
1. User query → Claude Code
2. Claude → MCP tool call
3. MCP Server → Service (ChromaDB/Everything/etc)
4. Service → Response
5. MCP Server → Claude
6. Claude → User

## Code Standards

### Python
```python
# Type hints required
def search_memory(query: str, limit: int = 10) -> list[dict]:
    """
    Search semantic memory for relevant context.

    Args:
        query: Search query string
        limit: Maximum results to return

    Returns:
        List of matching memory entries
    """
    pass

# Use dataclasses for models
@dataclass
class MemoryEntry:
    id: str
    content: str
    metadata: dict
    timestamp: datetime
```

### Error Handling
```python
# Explicit, actionable errors
try:
    result = collection.query(query_texts=[query])
except chromadb.errors.InvalidCollectionError:
    logger.error(f"Collection not found: {collection_name}")
    raise MCPError(f"Memory collection '{collection_name}' does not exist")
```

### Logging
```python
# Use structured logging
logger.info(f"[AIONS] {datetime.now().isoformat()} - Tool {tool_name} called")
```

## API Contracts

### MCP Tool Response Format
```json
{
  "status": "ok|error",
  "timestamp": "ISO8601",
  "data": {},
  "error": "string if status=error"
}
```

### ChromaDB Query Pattern
```python
results = collection.query(
    query_texts=["search term"],
    n_results=10,
    where={"type": "conversation"},
    include=["documents", "metadatas", "distances"]
)
```

## Performance Requirements
- File search: < 100ms
- Memory query: < 500ms
- Project scan: < 60s for 50k files
- MCP tool response: < 5s timeout

## Security
- No hardcoded credentials
- AWS credentials via profiles
- Sanitize all user input
- Validate file paths

## Python Version Policy + aions_python launcher

**One version everywhere: Python 3.11** (Windows prod + WSL dev). SSOT: `.aions/python.env`.

| Environment | Path | Launcher |
|-------------|------|----------|
| Windows production | `E:\server wiedzy\venv` | `scripts\aions_python.ps1` |
| WSL dev | `D:\AIONS_DEV\venv` | `scripts\aions_python.sh` |
| MCP entry | `start_aions_mcp.bat` | → `aions_python.ps1` |
| Cursor MCP | `~/.cursor/mcp.json` | explicit `venv\Scripts\python.exe` |

**Nigdy nie wołaj bare `python`** — zawsze przez `start_aions_mcp.bat`, `start_aions_dev.sh`, lub `scripts/aions_python.*`.

```powershell
# Windows — resolve / run / verify
.\scripts\aions_python.ps1 -ResolveOnly
.\scripts\aions_python.ps1 scripts\verify_python_env.py
.\scripts\ensure_venv.ps1          # utwórz lub zweryfikuj venv
```

```bash
# WSL
./scripts/aions_python.sh --resolve
./scripts/aions_python.sh scripts/verify_python_env.py
/mnt/d/AIONS_DEV/start_aions_dev.sh verify-python
```

**Why not 3.12 on Windows:** `chromadb==0.5.3` pins `chroma-hnswlib==0.7.3`, which has no prebuilt `cp312` wheel; building from source requires MSVC Build Tools. WSL Ubuntu 3.12 was aligned down to 3.11 for parity.

**Do not use** system `Python311` / `Python312` / `Python313` for MCP — `__main__.py` venv guard blocks non-venv interpreters.

**Po zmianie `mcp.json`:** Cursor → Settings → MCP → `aions-context` → Reload (lub restart Cursor).

**Recreate venv (Windows):**
```powershell
Rename-Item "E:\server wiedzy\venv" "venv_backup_$(Get-Date -Format yyyyMMdd)"
.\scripts\ensure_venv.ps1
```

**Recreate venv (WSL):**
```bash
mv /mnt/d/AIONS_DEV/venv /mnt/d/AIONS_DEV/venv_backup_$(date +%Y%m%d)
/mnt/d/AIONS_DEV/start_aions_dev.sh shell   # --ensure-venv via aions_python.sh
```

## Agent Timeout Discipline (Marcin / AIONS)

Agents must not hang indefinitely. Apply these limits in every session:

### Shell
- **Status checks:** max 30s `block_until_ms`
- **Builds:** max 120s
- **Long scans:** `block_until_ms: 0` — background only, never block foreground

### MCP
- If no response within one turn, report the stall and retry **once** — never infinite wait

### Subagents
- Scope small, bounded tasks only
- Max **one inventory** + **one write** per subagent
- If >5 min with no file output → interrupt and report state
- **Never** `Await` a subagent in foreground — background only

### full_system_scan
- `status.json` must update per drive
- Stale >30 min → report dead PID; do not restart a running scan unless user asks
- `F:` jest traktowane jako special-case backing/home volume dla Dev Drive `D:` i jest domyślnie pomijane; jawne `--drives ...F...` nadal je włącza

### User interrupt signals
- Messages like **"timeout"** or **"zawiesiles sie"** → stop current path immediately, report state, propose a smaller next step

## Roadmap phases (AIONS OS v15)

**SSOT:** `.claude/specs/AIONS_OS_ROADMAP.md` — Fazy 1–10 (not legacy Etap numbering).  
**Agent entry:** `AGENTS.md` at repo root.  
**Legacy map:** `.claude/specs/LEGACY_ETAP_MAP.md`

| Faza | Focus |
|------|-------|
| 1 | Core Runtime — **closed** |
| 2 | Deploy Anywhere — `install → boot → GREEN` |
| 3 | AI Control Plane — `control_plane/` |
| 4 | AIONS Identity — MOTD, branding |
| 5–10 | LLM adapter, distributed, autonomy, image, appliance, ecosystem |

**Architectural principle:** Linux = hardware · CBMS = cognitive · MCP = execution · LLM = replaceable interface.
