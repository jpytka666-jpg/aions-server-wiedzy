---
inclusion: always
---

# AIONS Technical Standards

## Technology Stack

### Core
- **Python 3.11+** - Main backend language
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
