---
inclusion: always
---

# AIONS Code Organization

## Directory Structure

```
E:\server wiedzy\
├── .claude/                    # Claude Code configuration (Kiro for CC)
│   ├── agents/                 # AI agent definitions
│   │   ├── kfc/               # Built-in Kiro agents
│   │   │   ├── spec-requirements.md
│   │   │   ├── spec-design.md
│   │   │   ├── spec-tasks.md
│   │   │   ├── spec-judge.md
│   │   │   ├── spec-impl.md
│   │   │   └── spec-test.md
│   │   └── aions-expert/      # Custom AIONS agent
│   │       ├── agent.json
│   │       └── system-prompt.md
│   ├── specs/                 # Feature specifications
│   │   └── {feature-name}/
│   │       ├── requirements.md
│   │       ├── design.md
│   │       └── tasks.md
│   ├── steering/              # AI guidance documents
│   │   ├── product.md
│   │   ├── tech.md
│   │   └── structure.md
│   ├── settings/
│   │   └── kfc-settings.json
│   └── system-prompts/
│       └── spec-workflow-starter.md
│
├── .kiro/                      # Kiro IDE legacy config
│   ├── specs/                 # Specs (linked from kfc-settings.json)
│   ├── steering/              # Steering files
│   └── settings/
│       └── mcp.json           # MCP server configuration
│
├── server/                     # Core AIONS backend
│   ├── context_schema.py      # Context data models
│   ├── store.py               # ChromaDB operations
│   ├── models.py              # Data models
│   └── cbms/                  # Context-Based Memory System
│
├── mcpServers/                 # MCP server implementations
│   └── VS_CODE_MCP_CODEX/
│       └── src/
│           └── server.py      # Main aions-context server
│
├── scripts/                    # Utility scripts
│   ├── installers/
│   ├── scanners/
│   └── extractors/
│
├── data/
│   └── chroma/                # ChromaDB database files
│
├── logs/
│   └── conversation_dumps/    # Conversation history (JSONL)
│
├── AIONS_CATALOG/             # Knowledge base
│   ├── chunks/                # Information chunks
│   ├── facts/                 # Verified facts
│   ├── plasters/              # Quick fixes
│   ├── thinking_patterns/     # Reasoning templates
│   └── tools/                 # Tool documentation
│
├── docs/                       # Documentation
│
└── venv/                       # Python virtual environment
```

## File Naming Conventions

### Python Files
- `snake_case.py` - All Python modules
- `test_*.py` - Test files
- `*_utils.py` - Utility modules

### Configuration Files
- `*.json` - JSON configuration
- `*.md` - Markdown documentation and steering
- `*.yaml` / `*.yml` - YAML configuration

### Data Files
- `*.jsonl` - JSON Lines (conversation logs)
- `*.db` - Database files

## Module Dependencies

```
server/
├── context_schema.py ← models.py
├── store.py ← context_schema.py, models.py
└── cbms/ ← store.py

mcpServers/VS_CODE_MCP_CODEX/
└── server.py ← server/*, chromadb, fastmcp
```

## Import Guidelines

```python
# Standard library first
import os
import json
from datetime import datetime
from pathlib import Path

# Third-party
import chromadb
from fastmcp import FastMCP

# Local imports
from server.store import get_collection
from server.models import ContextEntry
```

## Configuration Hierarchy

1. **Environment Variables** - Highest priority
2. **Local Settings** - `.claude/settings.local.json`
3. **Project Settings** - `.claude/settings.json`
4. **Defaults** - Hardcoded in code

## Key Entry Points

| Component | Entry Point | Purpose |
|-----------|-------------|---------|
| aions-context MCP | `mcpServers/VS_CODE_MCP_CODEX/src/server.py` | Main MCP server |
| Context Admin | `context_admin.py` | CLI for context management |
| ChromaDB | `server/store.py` | Vector database interface |
| CBMS | `server/cbms/` | Domain knowledge system |
