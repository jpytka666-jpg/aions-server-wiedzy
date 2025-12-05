# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AIONS/CBMS is a Polish-language AI system that uses a chunk-based memory system (CBMS) with Korean compression techniques. The system is designed to run entirely offline and provides chat capabilities through both CLI and HTTP API interfaces.

### System Context
This is part of a larger AGI ecosystem that includes:
- **AIONS/CBMS** (this repository): Standalone chat system with 76+ knowledge chunks
- **AGI_CODex** (D:\AGI_CODex\): Extended system with 125+ binary chunks and Mistral-7B integration
- **CBMS Complete** (E:\AIONS_COMPLETE\): Full system with 2,270+ chunks and Claude knowledge patterns

The system in this directory is the release version optimized for desktop deployment.

## Commands

### Running the System

**Start the web server (primary method):**
```bash
# Windows - Batch
run_server.bat

# Windows - PowerShell
.\run_server.ps1

# Direct Python execution
py -u server\cbms_direct_server.py
```
Server runs on `http://127.0.0.1:9000`

**Interactive chat mode:**
```bash
# From AIONS_CBMS_RELEASE directory
python AIONS_ULTIMATE_UNIFIED.py --mode chat
```

**Run tests:**
```bash
# Quick chat test
python quick_chat_test.py

# Full capabilities test
python test_aions_capabilities.py

# Benchmark performance
py .\tools\bench_runner.py

# Math tests (GSM8K)
py .\tools\gsm8k_quick.py
```

### API Endpoints
- `GET /health` - System status and chunk count
- `GET /info` - System information and concepts
- `POST /api/chat` - Main chat endpoint (CBMS-only with OOD refusal)
- `POST /crla/ask` - CRLA tournament mode (`{"query":"...", "seed":123, "candidates":8}`)

## Architecture

### Core Components

**Memory System (CBMS)**
- Location: `memory/chunks/` - Contains 76+ JSON knowledge chunks with Korean-compressed keys
- Each chunk has a unique hash ID (e.g., `K2FEAB6375705.json`)
- Manifest file tracks all chunks and their metadata
- Out-of-domain (OOD) detection returns: `NIE WIEM / BRAK DANYCH CBMS-KR.`

**Server Components** (`server/`)
- `cbms_memory.py` - Core CBMS memory management
- `cbms_direct_server.py` - Basic HTTP server implementation
- `cbms_enhanced_server.py` - Enhanced server with conversation features
- `crla_core.py` - CRLA tournament selection algorithm
- `korean_keys.py` - Korean compression key generation (3.29:1 compression ratio)
- `facts_loader.py` - Facts database loader
- `conversation_enhancer.py` - Natural conversation improvements
- `math_solver.py` - Mathematical problem solving
- `stylist.py` - Response styling (passive filter, preserves facts)

**Environment Variables**
The system uses these environment variables (set automatically by run scripts):
- `CBMS_MEMORY_DIR` - Path to memory directory
- `CBMS_WEB_DIR` - Path to web assets directory
- `PYTHONPATH` - Includes server and tools directories

### Data Flow
1. User query → Korean key compression → CBMS chunk matching
2. If match found → CRLA tournament selection → Response styling
3. If no match → OOD refusal message
4. Math queries detected → Redirect to math_solver
5. All responses → Conversation enhancement → Final output

## Development Notes

### Adding New Knowledge
Use the web crawler to import new facts:
```powershell
py .\tools\web_crawler_import.py --seeds=<URL> --allow=<domain> --max-pages=50 --max-mb=10
```
New facts save to `memory/facts.jsonl` and update the index.

### Testing Changes
After modifying server components:
1. Restart the server (`run_server.bat` or `run_server.ps1`)
2. Run quick chat test: `python quick_chat_test.py`
3. Check benchmark: `py .\tools\bench_runner.py`

### Performance Metrics
- Target latency: <100ms (p50: ~30-40ms)
- Chunk loading: 76 chunks baseline (expandable to 2,233)
- Compression: 3.29:1 ratio with 4,016 Korean patterns

### Important Files
- Main launcher: `URUCHOM_AIONS_ULTIMATE.bat` (Desktop) - Interactive menu system
- Unified system: `AIONS_ULTIMATE_UNIFIED.py` - All-in-one implementation
- Logs: `logs/` - Benchmark results, CRLA runs, competitive analysis
- Knowledge base: `biblioteka_agi.json` (Desktop) - Metadata for 2,270+ chunks across the ecosystem