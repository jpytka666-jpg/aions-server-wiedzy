---
inclusion: always
---

# AIONS Product Conventions

## Product Vision
AIONS (AI-Orchestrated Intelligence Network System) is a context management and knowledge orchestration system that:
- Provides semantic search across files, memory, and domain knowledge
- Manages conversation context and history
- Integrates with MCP (Model Context Protocol) for tool access
- Stores and retrieves knowledge using ChromaDB vector database

## Core Features

### 1. Context Search (Priority: HIGH)
- `fast_search` - Blazing fast file search using Everything
- `memory_recall` - Semantic search in ChromaDB memory
- `cbms_search` - Domain knowledge search in CBMS
- `project_search` - Search scanned project files

### 2. Memory Management (Priority: HIGH)
- `memory_store` - Store context to ChromaDB
- `conv_log` - Log conversation messages
- `conv_dump` - Force save conversation buffer
- `conv_history` - Retrieve past conversations

### 3. Project Analysis (Priority: MEDIUM)
- `project_scan_turbo` - Fast project scanning
- `project_file_deps` - Analyze file dependencies
- `git_status` / `git_log` - Git integration

### 4. Browser Automation (Priority: LOW)
- Playwright-based browser tools
- Screenshot, navigation, interaction

## User Personas

### Primary: Developer (Marcin)
- Uses Claude Code for development
- Needs fast context retrieval
- Works with multiple MCP servers
- Requires conversation persistence

### Secondary: AI Agents
- Automated agents using MCP tools
- Need reliable tool responses
- Require structured data formats

## Success Metrics
- Search response time < 1 second
- Memory recall accuracy > 90%
- Zero data loss in conversation logs
- MCP server uptime > 99%

## Product Principles
1. **Speed First** - All operations should feel instant
2. **Reliability** - Never lose user data
3. **Transparency** - Show what's happening
4. **Integration** - Work seamlessly with Claude Code
