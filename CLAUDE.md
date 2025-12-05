# CLAUDE.md - AIONS Project Guidance

## Project Overview

AIONS (AI-Orchestrated Intelligence Network System) is a context management and knowledge orchestration system for Claude Code development.

## Quick Start

### Primary Tools (USE FIRST!)
```
aions-context MCP tools:
- fast_search()     → File search (Everything)
- memory_recall()   → Semantic memory search
- cbms_search()     → Domain knowledge
- project_search()  → Project files
- conv_history()    → Past conversations
```

### Secondary Tools
- Read/Write/Edit - Local file operations
- aurora-dsql - AWS database queries

### Avoid Unless Necessary
- Web search (only when user explicitly requests)

## Project Structure

```
E:\server wiedzy\
├── .claude/           ← Kiro for CC configuration
│   ├── agents/        ← AI agents (kfc/, aions-expert/)
│   ├── specs/         ← Feature specifications
│   ├── steering/      ← AI guidance (product.md, tech.md, structure.md)
│   └── settings/      ← kfc-settings.json
├── .kiro/             ← Legacy Kiro config (specs, steering, mcp.json)
├── server/            ← Core backend (context_schema, store, cbms)
├── mcpServers/        ← MCP servers (aions-context)
├── data/chroma/       ← ChromaDB vector database
├── logs/              ← Conversation history
└── AIONS_CATALOG/     ← Knowledge base
```

## Development Workflow

### Spec-Driven Development (Kiro for CC)
1. **Requirements** → Define what to build (EARS format)
2. **Design** → Architecture and components (Mermaid diagrams)
3. **Tasks** → Implementation checklist

### Code Standards
- Python 3.11+ with type hints
- Docstrings for all public functions
- Error handling with explicit exceptions
- ChromaDB for vector storage

## Critical Rules

### DO
- Always search before claiming file contents
- Read files before modifying
- Use aions-context tools first
- Verify with actual tool output

### DON'T
- Assume or guess file paths
- Fabricate tool results
- Create files without checking existing structure
- Skip reading before editing

## Key Files

| File | Purpose |
|------|---------|
| `mcpServers/VS_CODE_MCP_CODEX/src/server.py` | Main MCP server |
| `server/store.py` | ChromaDB interface |
| `server/context_schema.py` | Data models |
| `.kiro/settings/mcp.json` | MCP configuration |
| `.claude/settings/kfc-settings.json` | Kiro for CC settings |

## MCP Servers

| Server | Status | Purpose |
|--------|--------|---------|
| aions-context | ✅ Active | Primary - search, memory, CBMS |
| aurora-dsql | ✅ Active | AWS database |
| MCP_DOCKER | ✅ Active | Browser automation, Docker tools |

## Commands

```bash
# Python venv
E:\server wiedzy\venv\Scripts\python.exe

# ChromaDB location
E:\server wiedzy\data\chroma

# Run MCP server manually
python mcpServers/VS_CODE_MCP_CODEX/src/server.py
```

## Contact

Project Owner: Marcin
Language: Polish preferred, English acceptable
