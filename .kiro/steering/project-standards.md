---
inclusion: always
---

# AIONS Project Standards

## Project Structure

### Core Directories
- `server/` - Core AIONS backend (context_schema.py, store.py, models.py, CBMS implementation)
- `mcpServers/` - MCP server implementations (VS_CODE_MCP_CODEX and others)
- `scripts/` - Utility scripts (installers, scanners, extractors)
- `data/chroma/` - ChromaDB vector database storage
- `logs/` - Conversation dumps and context snapshots
- `.kiro/` - Kiro IDE configuration (steering, settings, MCP config)
- `AIONS_CATALOG/` - Organized knowledge base (chunks, facts, plasters, thinking_patterns, tools)

### Key Files
- `context_admin.py` - Context management utilities
- `requirements.txt` - Python dependencies
- `AIONS_MASTER_INSTRUCTIONS.md` - Project overview and instructions

## Code Standards

### Python Requirements
- **Version**: Python 3.11 or higher
- **Type Hints**: Required for all function signatures and class attributes
- **Docstrings**: Required for all public functions, classes, and modules (Google or NumPy style)
- **Formatting**: Follow PEP 8 conventions
- **Error Handling**: Use explicit exception handling, avoid bare `except` clauses

### Code Organization
- Keep related functionality together in modules
- Use clear, descriptive names for functions and variables
- Avoid deep nesting (max 3-4 levels)
- Extract complex logic into separate functions

### Testing
- Write tests before merging new features
- Test files should mirror source structure
- Include both unit and integration tests where appropriate

## Architecture Patterns

### MCP Server Pattern
- MCP servers communicate via stdio using the Model Context Protocol
- Each server should have clear tool definitions with JSON schemas
- Use `patched_stdio.py` for Windows compatibility when needed
- Configuration lives in `.kiro/settings/mcp.json`

### Context Management
- Use ChromaDB for vector storage and semantic search
- Context schemas defined in `server/context_schema.py`
- Store conversation history in `logs/conversation_dumps/`
- CBMS (Context-Based Memory System) for domain knowledge

### Data Flow
1. User input → MCP tools (fast_search, memory_recall, cbms_search)
2. Context retrieval → ChromaDB queries
3. Response generation → Context storage
4. Conversation logging → JSONL format

## Critical Rules

### File Management
- **NEVER** create files in random locations outside the established structure
- **ALWAYS** check if functionality exists before implementing duplicates
- **ALWAYS** use appropriate directories: scripts in `scripts/`, servers in `mcpServers/`, etc.
- Respect the AIONS_CATALOG structure for knowledge organization

### Search Priority
1. **First**: Use aions-context MCP tools (fast_search, memory_recall, cbms_search, project_search)
2. **Second**: Use local Kiro tools (grepSearch, fileSearch, readFile)
3. **Last**: Web search (only when explicitly requested or for external information)

### Code Modifications
- **ALWAYS** read files before modifying them
- **NEVER** assume file contents or structure
- **ALWAYS** verify changes with getDiagnostics after editing Python files
- Use `strReplace` for targeted edits, `fsWrite` for new files

### Dependencies
- Check `requirements.txt` before adding new Python packages
- Verify MCP server dependencies in their respective directories
- Document any new dependencies with version constraints

## Common Patterns

### Adding a New MCP Tool
1. Define tool schema in server code
2. Implement tool handler function
3. Update MCP configuration in `.kiro/settings/mcp.json`
4. Test with MCP inspector
5. Document in relevant README

### Working with ChromaDB
```python
# Standard pattern for vector operations
from server.store import get_collection
collection = get_collection("collection_name")
results = collection.query(query_texts=["search term"], n_results=5)
```

### Logging Conversations
- Use JSONL format (one JSON object per line)
- Include timestamps, user messages, and assistant responses
- Store in `logs/conversation_dumps/` with date-based filenames

## Project-Specific Conventions

### Language
- Code comments and docstrings: English
- Documentation files: May be in Polish or English depending on context
- Variable/function names: English only

### Naming Conventions
- Python files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- MCP tools: `snake_case` (e.g., `fast_search`, `memory_recall`)

### Configuration Files
- MCP config: `.kiro/settings/mcp.json`
- Workspace settings: `.kiro/settings/` directory
- Steering rules: `.kiro/steering/*.md`

## Performance Considerations

- Use batch operations for ChromaDB when processing multiple items
- Implement caching for frequently accessed data
- Avoid loading entire large files when partial reads suffice
- Use streaming for large file operations

## Security Notes

- Never commit sensitive data (API keys, passwords) to version control
- Use environment variables for sensitive configuration
- Sanitize user input before database operations
- Validate file paths to prevent directory traversal
