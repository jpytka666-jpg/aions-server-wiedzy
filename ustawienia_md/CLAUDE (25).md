# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a home directory containing documentation and analysis for the **AIONS** (AI Optimization Neural System) project - a revolutionary offline AI architecture.

### Primary Version: AIONS_CBMS_RELEASE_V3 🔥
**Location**: `C:\Users\User\OneDrive - Global Banking School\Desktop\AIONS_CBMS_RELEASE_V3\`
- **Status**: OPERATIONAL (as of 2025-11-08 17:04)
- **Chunks**: 521 active
- **Plasters**: 200 PACKs (343,091 Q&As)
- **Additional Resources**: `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\`
  - plasters_fullstack (448 PACKs)
  - chunks_unified (1,033 chunks)
  - Pocket QC emulator

### Legacy Version
- `C:\Users\User\Desktop\AIONS_CBMS_RELEASE\` (symlink to older version)

## Core AIONS Architecture

### CBMS (Chunk-Based Memory System)
- Knowledge stored in addressable JSON blocks at `memory/chunks/`
- Each chunk identified by K[hex] format (K + 12-13 hexadecimal characters)
- Address space: 16^13 = 1.15 × 10^15 possible addresses
- Current state: **521 chunks** in active memory (V3 operational)
- All chunks cross-referenced in `memory/knowledge_manifest.json` (~10 MB, 33,945+ facts)
- Compression ratio: 3.29:1 using Korean syllable decomposition

### Korean Key Compression
- Uses Korean syllable decomposition for semantic addressing
- Character 3-grams + SHA1 hash prefixes for matching
- Set intersection for semantic search (O(n) lookup)
- K-prefix format ensures no tokenization bottleneck
- Prevents hallucinations by enforcing reference-based retrieval
- 4,016+ Korean patterns in active use

### CRLA (Chain Reaction Learning Algorithm)
- NOT simple tournament selection - parametric optimization system
- For each query: generates K=12 candidates with different retrieval strategies
- Multi-dimension scoring (6 factors: Facts, Determinism, Latency, Policies, Trace, Hygiene)
- Stores thinking patterns as CBMS chunks for future learning
- J=0.893 threshold parameter for quality control
- Recent additions: 3 new chunks for CRLA learning (`K9C47BB658D7B`, `KBC93CF11578B`, `K9292F586B56D`)

### Plasters System
- Extended knowledge packs system for specialized domains
- **plasters_200g**: 200 PACKs → 343,091 Q&As (primary)
- **plasters_fullstack**: 448 PACKs → 768,768 Q&As (experimental)
- **chunks_unified**: 1,033 additional chunks
- Location: `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\`
- Configuration: `CBMS_ENABLE_PLASTERS=1`, `CBMS_PLASTERS_DIR` env variable
- Endpoint: `/plasters/stats` for monitoring loaded packs

### Pocket QC - Quantum Computing Emulator
- **CPU-only quantum circuit simulator** (offline, deterministic)
- Location: `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\pocket_qc\CBMS_Pocket_QC_Lab`
- Components:
  - Statevector simulator (H, X, Y, Z, S, T, CNOT, measurement)
  - Quantum-inspired optimizer (QUBO/Ising, SA/Tabu)
  - CRLA policies selector (auto backend selection)
  - Deterministic trace (JSONL + checksums)
- Configuration: `CBMS_POCKET_QC_ROOT` env variable
- Use cases: Circuit simulation, QUBO optimization, auditable QC

### Query Processing Pipeline
```
User Query
  → Math Solver (deterministic)
  → Facts System (database lookup)
  → CBMS Think (Korean key retrieval + synthesis)
  → Plasters (if enabled, extended knowledge)
  → Enhancement (conversation context, style)
  → OOD Detection (safe refusal if out-of-domain)
  → Response
```

## Project Locations

### Main AIONS System (V3)
**Location**: `C:\Users\User\OneDrive - Global Banking School\Desktop\AIONS_CBMS_RELEASE_V3\`

**Key Files**:
- `AIONS_ULTIMATE_UNIFIED.py` - Main orchestrator (700+ lines)
- `server/cbms_direct_server.py` - Direct HTTP server (foreground mode)
- `server/cbms_memory.py` - Memory management
- `server/korean_keys.py` - Compression algorithm
- `server/crla_core.py` - Tournament algorithm
- `server/conversation_enhancer.py` - Natural language enhancement
- `server/math_solver.py` - Deterministic math solving
- `server/stylist.py` - Response formatting
- `server/cbms_math_solver.py` - Enhanced math capabilities
- `memory/chunks/` - Knowledge chunks (457 active)
- `memory/knowledge_manifest.json` - Main chunk index

### GPU Benchmarking Service
**Location**: `C:\Users\User\AIONS\`
- Simple FastAPI service with PyTorch GPU benchmarking
- Endpoints: `/ping` (health check), `/dot` (matrix multiplication)

### Documentation & Notes
**Location**: `C:\Users\User\`
- `AIONS_DEEP_UNDERSTANDING.md` - Complete mechanics explanation
- `CRITICAL_ARCHITECTURE_NOTES.md` - Developer briefing
- `AIONS_ECOSYSTEM_MAP.md` - Complete project map
- `EXPLORATION_SUMMARY.md` - System exploration notes
- `AGENTS.md` - Operational guidelines and session state
- `notes/` - Asset maps and session snapshots

## Commands

### Starting AIONS Server

**Standard background mode:**
```powershell
cd C:\Users\User\Desktop\AIONS_CBMS_RELEASE
.\run_server.bat          # Windows batch launcher
.\run_server.ps1          # PowerShell launcher
```

**Foreground mode (debugging):**
```powershell
cd C:\Users\User\Desktop\AIONS_CBMS_RELEASE
python server\cbms_direct_server.py    # Live stdout/stderr
```

**Interactive chat mode:**
```bash
python AIONS_ULTIMATE_UNIFIED.py --mode chat
```

**With plasters enabled:**
```powershell
# Set environment variables first
$env:CBMS_ENABLE_PLASTERS = "1"
$env:CBMS_PLASTERS_DIR = "E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\plasters_200g"
python server\cbms_direct_server.py
```

### Port Management

**Kill processes on port 9000:**
```powershell
# PowerShell method
Get-NetTCPConnection -LocalPort 9000 -State Listen | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

# netstat method
netstat -ano | findstr :9000
taskkill /PID <PID> /F
```

### Testing System Health

```bash
# Check server status
curl http://localhost:9000/health
# Expected: {"status":"ok","chunks":457,"plasters_enabled":true}

# Get system info
curl http://localhost:9000/info

# Check plasters stats (if enabled)
curl http://localhost:9000/plasters/stats

# Send chat query
curl -X POST http://localhost:9000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"Hello world"}'

# CRLA tournament mode
curl -X POST http://localhost:9000/crla/ask \
  -H "Content-Type: application/json" \
  -d '{"query":"What is CBMS?","seed":123,"candidates":8}'
```

### Running Tests

```powershell
cd C:\Users\User\Desktop\AIONS_CBMS_RELEASE

# Quick functional test
python quick_chat_test.py

# Full capabilities test
python test_aions_capabilities.py

# Plasters integration test
python test_plasters_integration.py

# Foreground self-test
.\run_foreground_selftest.bat

# Extended benchmark
.\run_full_benchmark.ps1
.\RUN_ALL_BENCHMARKS.bat

# Benchmark runner (produces logs/)
python tools\bench_runner.py

# Stress test suite
python tools\stress_test_suite.py
```

### Warm-up Procedure

After starting the server, run these warm-up queries:
```bash
# Test CBMS retrieval
curl -X POST http://localhost:9000/api/chat -H "Content-Type: application/json" -d '{"query":"What is CBMS?"}'

# Test CRLA
curl -X POST http://localhost:9000/api/chat -H "Content-Type: application/json" -d '{"query":"Explain CRLA"}'

# Test Korean compression
curl -X POST http://localhost:9000/api/chat -H "Content-Type: application/json" -d '{"query":"Korean 3.29:1 compression"}'

# Test math solver
curl -X POST http://localhost:9000/api/chat -H "Content-Type: application/json" -d '{"query":"1337*42"}'
```

### GPU Testing

```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Run GPU benchmark
cd C:\Users\User\AIONS
python bench.py
```

## Development Environment

### Python Setup
- **Python Version**: 3.11.x
- **Primary Environment**: Miniconda3 (`C:\Users\User\Miniconda3\`)
- **AIONS Conda Env**: `conda activate aions`
- **PyTorch**: 2.2.2 with CUDA 11.8 support

### Key Dependencies
- `torch==2.2.2+cu118` - GPU acceleration
- `fastapi` - HTTP API framework
- `uvicorn` - ASGI server
- `msgspec`, `orjson` - Fast JSON serialization
- `loguru`, `rich` - Logging and terminal output

### Visual Studio 2022 Developer PowerShell
The developer uses VS 2022 Developer PowerShell with custom orchestration commands like `Run-AI`. This is a full Microsoft development environment with Azure SDK integration.

## Architecture Principles

### Zero Hallucinations (Architectural Guarantee)
Every response traces back to one of four sources:
1. **Math**: Deterministic solver (pure logic)
2. **Facts**: Explicit database lookup
3. **CBMS**: Chunks retrieved and synthesized
4. **Fallback**: Safe refusal ("NIE WIEM / BRAK DANYCH CBMS-KR.")

No probabilistic generation beyond known facts exists in the system.

### Learning Mechanism
- First query with new concept → generate thinking pattern → save as CBMS chunk
- Similar future queries → retrieve stored thinking pattern → faster response
- Thinking patterns stored with Korean markers and metadata
- System improves performance through accumulated thinking patterns

### CBMS Blocks Are Sacred
- **DO NOT** delete or move chunks without backups
- Each chunk represents real knowledge with cross-references
- Losing chunks breaks semantic understanding
- CRLA patterns are learned optimizations - back up religiously

### Korean Markers Are Structural
- Not decorative - they're how the system thinks
- K[hex] format is semantic addressing, not just IDs
- Changing markers breaks knowledge retrieval
- System cannot generate beyond addressable knowledge

## Module Organization

### Directory Structure
- `server/` - CBMS runtime (direct server, CRLA, stylist, loaders). Production code - changes must be focused by capability.
- `memory/` - Chunks, concept maps, kb.mmap, and manifests. Regenerate only when facts change.
- `tools/` - Crawlers, benchmark harnesses, stress suites
- `logs/` - Every benchmark/self-test artifact for traceability
- `web/` - Static web assets
- Root scripts - Entrypoints (`run_server*.bat|ps1`, `RUN_ALL_BENCHMARKS.bat`, `test_plasters_integration.py`)

### Coding Standards
- **Python**: Follow PEP 8 (4 spaces, snake_case functions, CapWords classes, CONSTANT_CASE flags)
- **Module headers**: Document required env vars (`CBMS_ENABLE_PLASTERS`, etc.)
- **Batch/PowerShell**: Mirror existing naming (`run_*.bat`, `*.ps1`) and echo progress for readable logs
- **Documentation**: Prefer docstrings over excessive inline comments
- **Logging**: Concise messages when touching loaders or CRLA evaluators

### Testing Guidelines
- Core scripts: `test_plasters_integration.py`, `quick_chat_test.py`, `tools/stress_test_suite.py`
- Fast regression: `run_foreground_selftest.bat`
- Full validation: `RUN_ALL_BENCHMARKS.bat` (attach `logs/` files to PRs)
- Name tests after behaviors (e.g., `test_korean_keys_edgecases.py`)
- Ensure tests can run offline with bundled memory

## Important Warnings

### From Developer
> "JAK SIE NE NAUCZYSZ CO I JAK W 100% TO NAROBISZ TYLKO ZNISZCZEN A NIC NIE STWOZYSZ"
>
> Translation: "If you don't learn what and how 100%, you'll only cause destruction and create nothing"

This is production code based on novel architecture. Wrong changes can break the entire system.

### Critical Rules
1. **Learn completely** before making changes
2. **Test thoroughly** before modifications
3. **Back up religiously** - especially memory/ directory
4. **Never disable** OOD detection (security feature)
5. **Respect the architecture** - it's more sophisticated than it appears
6. **Never embed secrets** - use env vars set in `run_server.bat`/PowerShell
7. **Validate after mutations** - `curl http://127.0.0.1:9000/health` after changing `memory/` or `logs/`

## Data Structures

### Chunk Format
```json
{
  "id": "K[12-13-hex-chars]",
  "concept": "concept name",
  "content": "knowledge content",
  "references": ["K...", "K..."],
  "access_count": 0,
  "metadata": {}
}
```

### Facts Index Format
```json
{
  "fact_id": "unique_id",
  "content": "fact content",
  "chunk_key": "K[hex]",
  "metadata": {}
}
```

### CRLA Candidate
```python
{
  "id": int,
  "min_hits": int,
  "max_steps": int,
  "window_size": int,
  "style_strength": float,
  "score": float
}
```

### Knowledge Manifest
```json
{
  "chunks": {...},
  "concept_map": {
    "concept_name": ["K...", "K..."]
  },
  "metadata": {}
}
```

## Performance Characteristics

- **Response Latency**: 30-40ms (p50), ~150ms (p95)
- **Compression Ratio**: 3.29:1
- **Memory Footprint**: ~4 GB (with PyTorch)
- **Database Size**: ~10 MB facts + ~100-300 bytes per chunk
- **Concurrent Capacity**: ~200-300 requests (current single-process design)
- **Active Chunks**: 521 (as of 2025-11-08 17:04)
- **Plasters**: 200 PACKs (343,091 Q&As) + 448 fullstack (768,768 Q&As)
- **Unified Chunks**: 1,033 additional in chunks_unified
- **Pocket QC**: CPU-only quantum emulator integrated

## Network Ports

- **9000**: Main AIONS API server
- **8000**: Alternative API (AIONS benchmarking service)
- **8721**: OAuth callback (Kodex-ESI project)

## Troubleshooting

### Port Already in Use
```powershell
Get-NetTCPConnection -LocalPort 9000 -State Listen | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

### CUDA Not Detected
```bash
pip install torch==2.2.2 -f https://download.pytorch.org/whl/cu118
```

### Memory Chunks Not Loading
```bash
# Verify directory exists
dir "C:\Users\User\Desktop\AIONS_CBMS_RELEASE\memory\chunks"

# Validate JSON
python -c "import json; json.load(open('memory/knowledge_manifest.json'))"
```

### Conda Environment Issues
```powershell
conda env list
conda activate aions
```

### Server Won't Start
```powershell
# Kill any existing processes on port 9000
Get-NetTCPConnection -LocalPort 9000 -State Listen | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

# Check Python path
where python

# Verify conda environment
conda activate aions
python -c "import fastapi; print('FastAPI OK')"
```

## File Preservation Priority

**Critical** (never delete):
- `memory/knowledge_manifest.json` - Chunk index
- `memory/chunks/` - All chunk files (457 active)
- `memory/facts_index.json` - Core knowledge database
- `AIONS_ULTIMATE_UNIFIED.py` - Main orchestrator
- `server/cbms_direct_server.py` - Production server

**Important** (back up regularly):
- `server/` - All component modules
- `memory/crla_runs.jsonl` - Learning history
- `memory/thinking_log.jsonl` - Thinking patterns
- `logs/` - Benchmark results and artifacts
- `notes/` - Session snapshots and asset maps

**Optional** (can regenerate):
- `__pycache__/` - Python bytecode
- `*.pyc` - Compiled Python files
- Log files older than 30 days

## Current Session State (2025-11-08 17:04)

### Active Configuration - AIONS V3 OPERATIONAL 🟢
- **Chunks**: 521 active (updated from 457)
- **Plasters**: Multiple systems available:
  - `plasters_200g`: 200 PACKs → 343,091 Q&As
  - `plasters_fullstack`: 448 PACKs → 768,768 Q&As 🔥
  - `chunks_unified`: 1,033 chunks
  - Location: `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\`
- **Pocket QC**: Quantum computing emulator integrated ✅
  - Location: `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\pocket_qc\CBMS_Pocket_QC_Lab`
  - Statevector simulator + quantum-inspired optimizer
  - CPU-only, offline, deterministic
- **Server Status**: Running on port 9000 (PID: 47600)
- **Last Test**: 2025-11-08 17:04 - Smoke tests PASSED ✅

### Health Check (Current)
```json
{
  "status": "ok",
  "chunks": 521,
  "plasters_enabled": true
}
```

### Plasters Stats (Current)
```json
{
  "total_packs": 200,
  "loaded_packs": 1,
  "total_qa_count": 343091,
  "loaded_pack_ids": ["PACK-0000"],
  "max_loaded": 1
}
```

### Known Working Queries
1. "What is CBMS?" - Tests chunk retrieval
2. "Explain CRLA" - Tests learning algorithm
3. "Korean 3.29:1 compression" - Tests compression system
4. "1337*42" - Tests math solver (deterministic: 56154)

## Related Documentation

- `AIONS_DEEP_UNDERSTANDING.md` - Complete mechanics explanation
- `CRITICAL_ARCHITECTURE_NOTES.md` - Developer briefing
- `AIONS_ECOSYSTEM_MAP.md` - Complete project map
- `EXPLORATION_SUMMARY.md` - System exploration notes
- `AGENTS.md` - Operational guidelines and current session state
- `notes/CBMS_asset_map.md` - Resource location mapping

## Additional Projects in Ecosystem

### Claude_Workspace
**Location**: `C:\Users\User\Claude_Workspace\`
- Test and analysis suite for AIONS
- Contains `aions_test/` directory with test cases
- Git repository for tracking test results

### CBMS_WORK
**Location**: `C:\Users\User\CBMS_WORK\`
- Development workspace for CBMS experiments
- Separate from production AIONS release
