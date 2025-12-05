---
inclusion: always
---

# AIONS Project - Product Vision

## Overview

AIONS (AI-Orchestrated Intelligent Network System) to zaawansowany system zarządzania kontekstem i pamięcią dla AI agentów, zbudowany na ChromaDB i MCP (Model Context Protocol).

## Core Features

### 1. Context Management
- **ChromaDB Vector Store** - semantyczne wyszukiwanie i przechowywanie kontekstu
- **CBMS (Context-Based Memory System)** - deterministyczne pobieranie chunków wiedzy
- **Korean Keys** - szybkie dopasowywanie przez hashowanie

### 2. MCP Server (AIONS-CONTEXT)
- **fast_search** - błyskawiczne wyszukiwanie plików (Everything)
- **memory_store/recall** - długoterminowa pamięć w ChromaDB
- **cbms_search** - wiedza domenowa
- **conv_log/dump/history** - automatyczne logowanie rozmów
- **project_scan_turbo** - skanowanie projektów
- **git_status/log** - integracja z Git
- **docker_ps/images** - zarządzanie kontenerami
- **wsl_run** - wykonywanie komend w WSL/Ubuntu
- **browser_**** - automatyzacja przeglądarki (Playwright)

### 3. Auto-Logging System
- Każde wywołanie narzędzia = automatyczny log
- Threshold-based auto-dump do ChromaDB
- JSONL backup w logs/conversation_dumps/

## Target Users

- **Marcin Szul** - główny developer i użytkownik
- **AI Agents** - Claude, GPT, Kiro jako konsumenci kontekstu

## Project Goals

1. **Zero-friction context** - agent zawsze ma dostęp do potrzebnego kontekstu
2. **Persistent memory** - rozmowy i decyzje są zapamiętywane
3. **Fast retrieval** - błyskawiczne wyszukiwanie (Everything + ChromaDB)
4. **Multi-modal** - pliki, kod, dokumentacja, rozmowy

## Roadmap

### Current (v6)
- ✅ AIONS-CONTEXT MCP server
- ✅ ChromaDB integration
- ✅ Auto-logging system
- ✅ Project scanner
- ✅ Git/Docker/WSL tools

### Next
- [ ] Multi-agent coordination
- [ ] Real-time sync between agents
- [ ] Advanced CBMS patterns
- [ ] Cost tracking per session

## Key Directories

```
E:/server wiedzy/
├── server/              # Core backend (store.py, context_schema.py)
├── mcpServers/          # MCP server implementations
├── data/chroma/         # ChromaDB storage
├── logs/                # Conversation dumps
├── scripts/             # Utility scripts
├── .kiro/               # Kiro configuration
└── AIONS_CATALOG/       # Knowledge base
```

## Success Metrics

- **Response time** < 100ms dla fast_search
- **Memory recall accuracy** > 90%
- **Zero data loss** - wszystkie rozmowy zapisane
- **Uptime** - MCP server zawsze dostępny
