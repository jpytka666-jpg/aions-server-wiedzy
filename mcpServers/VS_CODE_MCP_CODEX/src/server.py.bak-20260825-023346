"""
AIONS ULTIMATE MCP SERVER v6
============================
DEBILOODPORNE AUTO-LOGGING!

Każde wywołanie narzędzia = automatyczny log do bufora.
Zero myślenia, zero pamiętania.

Integruje:
- ChromaDB (semantic search)
- CBMS chunks (deterministic retrieval) 
- Korean keys (fast matching)
- DEBILOODPORNE AUTO-LOGGING ⭐⭐⭐
- Project Scanner + TURBO
- Everything (blazing fast file search)
- Docker, WSL, Git, Network tools

Autor: Marcin Szul / AIONS Project
"""

from __future__ import annotations

import json
import os
import queue
import sys
import re
import hashlib
import uuid
import traceback
import importlib.util
import subprocess
import threading
import shutil
import functools
import platform
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

try:
    from .desktop_provider import DesktopProviderError
    from .filesystem_provider import SearchProviderError
    from .provider_registry import (
        create_linux_search_provider,
        desktop_provider_capabilities,
        get_desktop_provider,
        resolve_search_provider_name,
        search_provider_status,
    )
except ImportError:
    from desktop_provider import DesktopProviderError
    from filesystem_provider import SearchProviderError
    from provider_registry import (
        create_linux_search_provider,
        desktop_provider_capabilities,
        get_desktop_provider,
        resolve_search_provider_name,
        search_provider_status,
    )


def _is_huge_repo(repo_path: str = "") -> bool:
    """Check if this is a huge repo that would hang git commands"""
    try:
        git_dir = Path(repo_path or ".") / ".git"
        if not git_dir.exists():
            return False
        
        # Quick heuristic - check .git size
        pack_dir = git_dir / "objects" / "pack"; total_size = sum(f.stat().st_size for f in pack_dir.iterdir() if f.is_file()) if pack_dir.exists() else 0  # FAST - no rglob
        if total_size > 100 * 1024 * 1024:  # > 100MB .git folder
            return True
            
        # Check if we are at root of a drive (like E:\)
        repo_root = Path(repo_path or ".")
        if len(str(repo_root.resolve()).split(":")) == 2 and str(repo_root.resolve()).endswith(":\\"):
            return True
            
        return False
    except:
        return False  # If check fails, assume its safe

# =============================================================================
# STDERR LOGGING
# =============================================================================

def log(msg: str):
    print(f"[AIONS] {datetime.now().isoformat()} - {msg}", file=sys.stderr, flush=True)

log("Server v6 loading (DEBILOODPORNE)...")

# =============================================================================
# PATH SETUP - AUTO-DISCOVERY (env vars -> common locations -> PATH)
# =============================================================================

def _find_dir(env_var: str, candidates: list) -> Optional[Path]:
    """Find directory from env var or candidate locations."""
    if os.environ.get(env_var):
        p = Path(os.environ[env_var])
        if p.exists(): return p
    for c in candidates:
        p = Path(c) if isinstance(c, str) else c
        if p.exists(): return p
    return None

def _find_exe(name: str, extra: list = None) -> str:
    """Find executable: PATH first, then extra locations."""
    found = shutil.which(name)
    if found: return found
    for p in (extra or []):
        if Path(p).exists(): return p
    return name

def _env_truthy(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}

def _find_python_exe() -> Path:
    env_py = os.environ.get("AIONS_PYTHON_EXE")
    candidates = []
    if env_py:
        candidates.append(Path(env_py))
    candidates.extend(
        [
            REPO_ROOT / "venv" / "Scripts" / "python.exe",
            REPO_ROOT / "venv" / "bin" / "python",
            Path(sys.executable),
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path(sys.executable)

def _split_search_roots(raw: str) -> List[Path]:
    sep = ";" if os.name == "nt" else ":"
    roots = []
    for entry in raw.split(sep):
        candidate = entry.strip().strip('"').strip("'")
        if candidate:
            roots.append(Path(candidate))
    return roots

REPO_ROOT = Path(__file__).resolve().parents[3]
DUMPS_DIR = REPO_ROOT / "logs" / "conversation_dumps"
SCAN_RESULTS_DIR = REPO_ROOT / "scan_results"
SCANNER_SCRIPT = REPO_ROOT / "scripts" / "project_scanner.py"
TURBO_SCANNER_SCRIPT = REPO_ROOT / "scripts" / "turbo_scanner.py"
PYTHON_EXE = _find_python_exe()
PLATFORM_NAME = platform.system().lower()
DEPLOYMENT_PROFILE = os.environ.get(
    "AIONS_DEPLOYMENT_PROFILE",
    "windows-primary" if os.name == "nt" else "linux",
)
VECTOR_BACKEND = os.environ.get("AIONS_VECTOR_BACKEND", "embedded").strip().lower()
API_BASE_URL = os.environ.get("AIONS_API_BASE_URL", "http://127.0.0.1:8765").rstrip("/")
SEARCH_ROOTS = _split_search_roots(os.environ.get("AIONS_SEARCH_ROOTS", str(REPO_ROOT)))
SEARCH_PROVIDER_OVERRIDE = os.environ.get("AIONS_SEARCH_PROVIDER", "").strip().lower()
SEARCH_INDEX_PATH = Path(
    os.environ.get(
        "AIONS_SEARCH_INDEX_PATH",
        str(REPO_ROOT / "runtime" / "state" / "aions_search_index.json"),
    )
)
SEARCH_AUTO_REFRESH_SECONDS = int(os.environ.get("AIONS_SEARCH_AUTO_REFRESH_SECONDS", "900"))
DESKTOP_ENABLED = _env_truthy("DESKTOP_ENABLED", default=(os.name == "nt"))


def _clamped_float_env(name: str, default: float, minimum: float, maximum: float) -> float:
    try:
        value = float(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        value = default
    return min(max(value, minimum), maximum)


SYSTEM_HEALTH_TIMEOUT_SECONDS = _clamped_float_env(
    "AIONS_SYSTEM_HEALTH_TIMEOUT_S",
    12.0,
    1.0,
    15.0,
)

# AIONS - AIONS_PATH env var, then common locations
AIONS_V10 = _find_dir("AIONS_PATH", [
    "E:/server wiedzy/aions_core",
    "/mnt/e/server wiedzy/aions_core",
    "/mnt/d/AIONS_DEV/cbms",
    "/home/aions/aions/data/cbms",
    Path.home() / "aions" / "data" / "cbms",
])

# Tools - PATH first, then common locations  
EVERYTHING_CLI = Path(_find_exe("es", ["C:/Program Files/Everything/es.exe"]))
DOCKER_EXE = _find_exe("docker")
WSL_EXE = _find_exe("wsl")
GIT_EXE = _find_exe("git", ["C:/Program Files/Git/bin/git.exe"])
GH_EXE = _find_exe("gh")
NMAP_EXE = _find_exe("nmap", ["C:/Program Files (x86)/Nmap/nmap.exe"])

DUMPS_DIR.mkdir(parents=True, exist_ok=True)
SCAN_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

server_pkg_path = REPO_ROOT / "server"

for p in [AIONS_V10, AIONS_V10 / "server"] if AIONS_V10 else []:
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

# =============================================================================
# MCP IMPORTS
# =============================================================================

try:
    from mcp.server.fastmcp import FastMCP
    log("FastMCP imported successfully")
except ImportError as e:
    log(f"FastMCP import failed: {e}")
    raise

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def _today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")

# CONTEXT GUARD - compress large responses to save Claude context window
CONTEXT_GUARD_THRESHOLD = 800  # chars threshold
_offload_cache = {}  # {ref_id: full_json}

def _success(payload: Dict[str, Any], guard: bool = True) -> str:
    """Success response with optional context guard for large payloads."""
    result = {"status": "ok", "timestamp": _now_iso(), **payload}
    result_json = json.dumps(result, ensure_ascii=False)

    # Context guard: compress if too large
    if guard and len(result_json) > CONTEXT_GUARD_THRESHOLD:
        ref_id = f"OFF_{str(uuid.uuid4())[:8]}"
        _offload_cache[ref_id] = result_json

        # Build summary
        summary_parts = []
        for k, v in list(payload.items())[:4]:
            if isinstance(v, str): summary_parts.append(f"{k}:{len(v)}ch")
            elif isinstance(v, list): summary_parts.append(f"{k}:{len(v)}items")
            elif isinstance(v, dict): summary_parts.append(f"{k}:{len(v)}keys")

        return json.dumps({
            "status": "ok", "timestamp": _now_iso(),
            "offloaded": ref_id, "size": len(result_json),
            "summary": ", ".join(summary_parts) if summary_parts else "large payload"
        }, ensure_ascii=False)

    return result_json

def _guard(result_json: str, guard: bool = True) -> str:
    """Context guard for pre-serialized JSON strings (control-plane tools).

    Additive helper restoring aions_plan / aions_execute_step /
    aions_execution_status. Mirrors _success() offload behavior but accepts an
    already-serialized JSON string instead of a payload dict.
    """
    if guard and len(result_json) > CONTEXT_GUARD_THRESHOLD:
        ref_id = f"OFF_{str(uuid.uuid4())[:8]}"
        _offload_cache[ref_id] = result_json
        return json.dumps({
            "status": "ok", "timestamp": _now_iso(),
            "offloaded": ref_id, "size": len(result_json),
            "summary": "large control-plane payload"
        }, ensure_ascii=False)
    return result_json

def _error(message: str) -> str:
    return json.dumps({"status": "error", "message": message, "timestamp": _now_iso()}, ensure_ascii=False)

def _generate_id() -> str:
    return str(uuid.uuid4())[:12]

def _run_command(cmd: List[str], timeout: int = 30) -> Dict[str, Any]:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=False,
        )
        return {"success": result.returncode == 0, "stdout": result.stdout[:5000], "stderr": result.stderr[:1000], "returncode": result.returncode}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Command timed out after {timeout}s"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# =============================================================================
# KOREAN KEYS
# =============================================================================

def korean_build_keys(text: str) -> set:
    if not text:
        return set()
    tokens = re.findall(r"[A-Za-z0-9]{2,}", text.lower())
    keys = set()
    for tok in tokens[:30]:
        for i in range(len(tok) - 2):
            keys.add(f"g:{tok[i:i+3]}")
        h = hashlib.sha1(tok.encode()).hexdigest()[:12]
        keys.add(f"h:{h[0:3]}")
    return keys

# =============================================================================
# AUTO-CATEGORIZATION
# =============================================================================

def extract_categories(text: str) -> List[str]:
    categories = []
    text_lower = text.lower()
    if any(k in text_lower for k in ["python", "javascript", "code", "function", "class", "api", "database"]):
        categories.append("programming")
    if any(k in text_lower for k in ["ai", "machine learning", "model", "gpt", "claude", "llm"]):
        categories.append("ai_ml")
    if any(k in text_lower for k in ["aions", "cbms", "chunk", "korean", "crla", "mcp"]):
        categories.append("aions_system")
    if any(k in text_lower for k in ["docker", "container", "wsl", "linux"]):
        categories.append("devops")
    if any(k in text_lower for k in ["git", "github", "commit", "branch"]):
        categories.append("version_control")
    if any(k in text_lower for k in ["scan", "file", "search", "find"]):
        categories.append("file_ops")
    return categories if categories else ["general"]

# =============================================================================
# DEBILOODPORNE AUTO-LOGGING SYSTEM
# =============================================================================

_auto_log_buffer: List[Dict] = []
_auto_log_session: str = "claude_marcin_main"
_auto_log_threshold: int = 5
_auto_log_last_dump: datetime = datetime.now(timezone.utc)

# =============================================================================
# PROVENANCE — one Claude, many machines
# =============================================================================
# The session stays single (_auto_log_session). Which host / surface produced a
# write is METADATA, not a separate memory. Purely additive: every key here is
# new, callers always win on collision, and records missing these keys are simply
# "written before the split" — no backfill required to keep working.
# Filterable via store.search(metadata_filter={"host": "..."}) — these are scalar
# keys on purpose, because `tags` gets comma-joined into a string and Chroma
# cannot substring-match a string in a `where` clause.

_RUN_ID: str = (
    f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:8]}"
)


def _default_host() -> str:
    try:
        import socket

        name = socket.gethostname()
        if name:
            return name.strip().lower()
    except Exception:
        pass
    return (os.environ.get("COMPUTERNAME") or "unknown").strip().lower()


def _client_identity() -> Dict[str, str]:
    """Identity the CALLER declared via HTTP headers, if any.

    Provenance is computed server-side, so without this every remote write would
    be stamped with the server's hostname — a laptop in another room would look
    like it was typed here. Remote clients declare themselves:

        claude mcp add --transport http aions <url> \
          --header "X-AIONS-Host: ubuntu-dev" \
          --header "X-AIONS-Surface: code-cli"

    Never raises: stdio calls simply have no request context, and a write must
    never fail because provenance could not be determined.
    """
    try:
        from mcp.server.lowlevel.server import request_ctx

        headers = getattr(getattr(request_ctx.get(), "request", None), "headers", None)
        if not headers:
            return {}
        found: Dict[str, str] = {}
        for header, key in (("x-aions-host", "host"), ("x-aions-surface", "surface")):
            value = headers.get(header)
            if value:
                found[key] = str(value).strip().lower()[:64]
        return found
    except Exception:
        return {}


def provenance() -> Dict[str, str]:
    """Who wrote this, wearing which machine."""
    server_host = os.environ.get("AIONS_HOST", _default_host())
    prov = {
        "agent": os.environ.get("AIONS_AGENT", "claude"),
        "host": server_host,          # who wrote it (client wins if declared)
        "server_host": server_host,   # where it physically landed — always true
        "surface": os.environ.get("AIONS_SURFACE", "unknown"),
        "run_id": _RUN_ID,
        "os": platform.system().lower(),
        "era": "multi-machine",
    }
    prov.update(_client_identity())
    return prov


def with_provenance(metadata: Optional[Dict] = None) -> Dict:
    """Additive merge — caller's keys win, nothing existing is dropped."""
    merged = provenance()
    merged.update(metadata or {})
    return merged


# Tools to SKIP logging (to avoid infinite loops)
SKIP_LOG_TOOLS = {
    "conv_log", "conv_dump", "conv_status", "conv_set_threshold",
    "conv_history", "session_bootstrap",
}

# Desktop tools whose auto-log preview must omit huge payloads (e.g. base64 PNG)
DESKTOP_TRUNCATE_LOG_TOOLS = {"desktop_snapshot"}

def _auto_log_entry(tool_name: str, args: Dict, result_preview: str):
    """AUTOMATYCZNIE loguje każde wywołanie narzędzia"""
    global _auto_log_buffer
    
    if tool_name in SKIP_LOG_TOOLS:
        return  # Skip conv_* tools to avoid loops
    
    # Create log entry
    args_str = ", ".join([f"{k}={repr(v)[:50]}" for k, v in args.items() if v])
    entry = {
        "id": _generate_id(),
        "timestamp": _now_iso(),
        "tool": tool_name,
        "args": args_str[:200],
        "result": result_preview[:300]
    }
    
    _auto_log_buffer.append(entry)
    log(f"AUTO-LOG: {tool_name}({args_str[:50]}) -> buffer={len(_auto_log_buffer)}")
    
    # Auto-dump when threshold reached
    if len(_auto_log_buffer) >= _auto_log_threshold:
        _auto_dump_logs()

def _auto_dump_logs():
    """Dump accumulated logs to file and ChromaDB"""
    global _auto_log_buffer, _auto_log_last_dump
    
    if not _auto_log_buffer:
        return
    
    try:
        # Format logs
        log_text = f"AUTO-LOG DUMP ({_today_str()})\n\n"
        for entry in _auto_log_buffer:
            log_text += f"[{entry['timestamp'][:19]}] {entry['tool']}({entry['args']})\n"
            log_text += f"  -> {entry['result']}\n\n"
        
        # Save to JSONL file
        dump_file = DUMPS_DIR / f"autolog_{_today_str()}.jsonl"
        with open(dump_file, "a", encoding="utf-8") as f:
            for entry in _auto_log_buffer:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
        # Save to ChromaDB
        vs = get_vector_store()
        if vs:
            doc_id = f"autolog_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            metadata = with_provenance({
                "type": "auto_log",
                "entry_count": len(_auto_log_buffer),
                "tools_used": ",".join(set(e["tool"] for e in _auto_log_buffer)),
                "timestamp": _now_iso()
            })
            vs.add_items(_auto_log_session, [(doc_id, log_text, metadata)])
        
        log(f"AUTO-DUMP: {len(_auto_log_buffer)} entries saved")
        
        _auto_log_buffer = []
        _auto_log_last_dump = datetime.now(timezone.utc)
        
    except Exception as e:
        log(f"AUTO-DUMP error: {e}")

def auto_logged(func: Callable) -> Callable:
    """Decorator that auto-logs tool calls - DEBILOODPORNE!"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get tool name
        tool_name = func.__name__
        
        # Call original function
        result = func(*args, **kwargs)
        
        # Auto-log (skip if in SKIP_LOG_TOOLS)
        if tool_name not in SKIP_LOG_TOOLS:
            try:
                # Parse result for preview
                if isinstance(result, str):
                    try:
                        parsed = json.loads(result)
                        if tool_name in DESKTOP_TRUNCATE_LOG_TOOLS and parsed.get("image_base64"):
                            preview = (
                                f"{parsed.get('status', 'ok')}: "
                                f"{parsed.get('width')}x{parsed.get('height')} "
                                f"({parsed.get('size_bytes', '?')} bytes, base64 omitted)"
                            )
                        else:
                            preview = parsed.get("status", "") + ": " + str(list(parsed.keys()))[:100]
                    except:
                        preview = result[:100] if tool_name not in DESKTOP_TRUNCATE_LOG_TOOLS else result[:80] + "…"
                else:
                    preview = str(result)[:100]
                
                _auto_log_entry(tool_name, kwargs, preview)
            except Exception as e:
                log(f"Auto-log error for {tool_name}: {e}")
        
        return result
    return wrapper

# =============================================================================
# LAZY-LOADED STORES
# =============================================================================

_vector_store = None
_cbms_memory = None

def _load_server_module(module_name: str, file_name: str):
    module_path = server_pkg_path / file_name
    if not module_path.exists():
        raise FileNotFoundError(f"Store module not found: {module_path}")
    spec = importlib.util.spec_from_file_location(
        module_name,
        module_path,
        submodule_search_locations=[str(server_pkg_path)],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def _vector_store_backend() -> str:
    backend = VECTOR_BACKEND
    if backend in {"api", "http-api"}:
        return "api"
    return "embedded"

def get_vector_store():
    global _vector_store
    if _vector_store is None:
        try:
            context_schema_path = server_pkg_path / "context_schema.py"
            if not context_schema_path.exists():
                raise FileNotFoundError("Store files not found")
            
            spec_cs = importlib.util.spec_from_file_location("aions_context_schema", context_schema_path)
            context_schema_module = importlib.util.module_from_spec(spec_cs)
            sys.modules["aions_context_schema"] = context_schema_module
            spec_cs.loader.exec_module(context_schema_module)
            
            sys.modules["server"] = type(sys)("server")
            sys.modules["server"].__path__ = [str(server_pkg_path)]
            sys.modules["server.context_schema"] = context_schema_module

            backend = _vector_store_backend()
            if backend == "api":
                store_module = _load_server_module("server.store_api", "store_api.py")
                _vector_store = store_module.VectorStore(
                    persist_path=os.environ.get("CHROMA_PATH"),
                    api_base_url=API_BASE_URL,
                )
                log(f"VectorStore loaded via API backend ({API_BASE_URL})")
                return _vector_store

            store_module = _load_server_module("server.store", "store.py")
            VectorStore = store_module.VectorStore
            _vector_store = VectorStore(persist_path=os.environ.get("CHROMA_PATH"))
            log("VectorStore loaded via embedded backend")
        except Exception as e:
            log(f"VectorStore failed: {e}")
            _vector_store = "FAILED"
    return _vector_store if _vector_store != "FAILED" else None

def get_cbms():
    global _cbms_memory
    if _cbms_memory is None:
        try:
            if not AIONS_V10:
                raise FileNotFoundError("AIONS_PATH/CBMS directory not found")
            # Add CBMS server folder to path
            cbms_server_path = AIONS_V10 / "server"
            if cbms_server_path.exists() and str(cbms_server_path) not in sys.path:
                sys.path.insert(0, str(cbms_server_path))
            from cbms_memory import CBMSMemory
            cbms_dir = AIONS_V10 / "memory" if AIONS_V10.exists() else None
            _cbms_memory = CBMSMemory(memory_dir=str(cbms_dir) if cbms_dir else None)
            log(f"CBMS loaded from {cbms_server_path}")
        except Exception as e:
            log(f"CBMS failed: {e}")
            _cbms_memory = "FAILED"
    return _cbms_memory if _cbms_memory != "FAILED" else None

# =============================================================================
# IN-MEMORY STORE
# =============================================================================

_memory_store: Dict[str, List[Dict]] = {}
_korean_index: Dict[str, Dict[str, set]] = {}

def memory_store_add(session_id: str, doc_id: str, text: str, metadata: dict):
    if session_id not in _memory_store:
        _memory_store[session_id] = []
    _memory_store[session_id].append({"id": doc_id, "text": text, "metadata": metadata})
    if session_id not in _korean_index:
        _korean_index[session_id] = {}
    _korean_index[session_id][doc_id] = korean_build_keys(text)

def memory_store_search(session_id: str, query: str, top_k: int = 5) -> List[Dict]:
    if session_id not in _memory_store:
        return []
    query_keys = korean_build_keys(query)
    session_keys = _korean_index.get(session_id, {})
    scores = []
    for doc in _memory_store[session_id]:
        doc_keys = session_keys.get(doc["id"], set())
        overlap = len(query_keys & doc_keys)
        if overlap > 0:
            scores.append((doc, overlap / max(len(query_keys), 1)))
    scores.sort(key=lambda x: x[1], reverse=True)
    return [{"id": d["id"], "text": d["text"], "score": s, "metadata": d["metadata"]} for d, s in scores[:top_k]]

# =============================================================================
# SCANNER STATE
# =============================================================================

_scan_status: Dict[str, Any] = {"state": "idle"}

# =============================================================================
# MCP SERVER
# =============================================================================

mcp_server = FastMCP("aions_context_server")
log("FastMCP server created")
LINUX_SEARCH_PROVIDER = create_linux_search_provider(
    SEARCH_ROOTS,
    SEARCH_INDEX_PATH,
    auto_refresh_seconds=SEARCH_AUTO_REFRESH_SECONDS,
)
DESKTOP_PROVIDER = get_desktop_provider(
    desktop_enabled=DESKTOP_ENABLED,
    platform_name=PLATFORM_NAME,
)

# =============================================================================
# FILE SEARCH TOOLS (AUTO-LOGGED)
# =============================================================================

def _normalize_folder_prefix(folder: str) -> str:
    """Normalize folder to Everything path-prefix (handles spaces in paths)."""
    prefix = folder.strip().strip('"').strip("'")
    prefix = prefix.replace("/", "\\")
    if not prefix.endswith("\\"):
        prefix += "\\"
    return prefix

def _build_everything_ext_query(extension: str, folder: str = "") -> str:
    """
    Build Everything query for extension search.
    Quoted-folder + ext: syntax fails on Windows paths with spaces;
    path-prefix glob (E:\\folder\\*.py) works reliably.
    """
    ext = extension.lstrip(".")
    if folder:
        return f"{_normalize_folder_prefix(folder)}*.{ext}"
    return f"ext:{ext}"

def _everything_search(query: str, max_results: int, timeout: int = 15, folder: str = "") -> Dict[str, Any]:
    if not EVERYTHING_CLI.exists():
        return {"ok": False, "error": "Everything CLI not found"}
    cmd = [str(EVERYTHING_CLI), "-n", str(max_results)]
    # Everything treats each CLI argument as a search term (ANDed together).
    # Passing the folder as its own term filters by path-substring (the whole
    # subtree), while the query term matches the file name/path anywhere under
    # it. This is more reliable than concatenating folder+query into one literal
    # path prefix, which silently missed files living in sub-directories.
    if folder:
        cmd.append(folder.rstrip("\\/"))
    if query:
        cmd.append(query)
    result = _run_command(cmd, timeout=timeout)
    if not result["success"]:
        err = result.get("error") or result.get("stderr") or "Search failed"
        return {"ok": False, "error": err}
    files = [f for f in result["stdout"].strip().split("\n") if f.strip()]
    return {"ok": True, "files": files, "query": (f"{folder} {query}".strip() if folder else query)}

def _search_provider() -> str:
    return resolve_search_provider_name(
        platform_name=PLATFORM_NAME,
        everything_available=EVERYTHING_CLI.exists(),
        provider_override=SEARCH_PROVIDER_OVERRIDE,
    )

def _platform_search(query: str, max_results: int, folder: str = "") -> Dict[str, Any]:
    provider = _search_provider()
    if provider == "everything":
        payload = _everything_search(query, max_results, timeout=10, folder=folder)
        payload["provider"] = provider
        return payload
    if provider == LINUX_SEARCH_PROVIDER.provider_name:
        try:
            return LINUX_SEARCH_PROVIDER.search(query, max_results, folder=folder)
        except SearchProviderError as exc:
            return {"ok": False, "provider": provider, "error": str(exc)}
    return {
        "ok": False,
        "provider": provider,
        "error": "No filesystem search provider available",
    }

@mcp_server.tool(name="fast_search", description="Fast file search (Everything on Windows, aions-linux-index on Linux).")
@auto_logged
def fast_search(query: str, max_results: int = 50, folder: str = "") -> str:
    try:
        payload = _platform_search(query, max_results, folder=folder)
        if not payload.get("ok"):
            return _error(payload.get("error", "Search failed"))
        files = payload["files"]
        return _success({
            "query": payload.get("query", query),
            "folder": folder or None,
            "provider": payload.get("provider", _search_provider()),
            "files": files[:max_results],
            "count": len(files),
        })
    except Exception as e:
        return _error(str(e))

@mcp_server.tool(name="fast_search_ext", description="Search files by extension.")
@auto_logged
def fast_search_ext(extension: str, folder: str = "", max_results: int = 100) -> str:
    try:
        provider = _search_provider()
        if provider == "everything":
            query = _build_everything_ext_query(extension, folder)
            payload = _everything_search(query, max_results, timeout=15)
        elif provider == LINUX_SEARCH_PROVIDER.provider_name:
            query = f"*.{extension.lstrip('.')}"
            payload = LINUX_SEARCH_PROVIDER.search_ext(extension, max_results, folder=folder)
        else:
            return _error("Extension search requires an available filesystem provider")
        if not payload.get("ok"):
            return _error(payload.get("error", "Search failed"))
        files = payload["files"]
        return _success({
            "extension": extension.lstrip("."),
            "folder": folder or None,
            "query": query,
            "provider": provider,
            "files": files,
            "count": len(files),
        })
    except Exception as e:
        return _error(str(e))

# =============================================================================
# DOCKER TOOLS (AUTO-LOGGED)
# =============================================================================

@mcp_server.tool(name="docker_ps", description="List Docker containers.")
@auto_logged
def docker_ps(all_containers: bool = False) -> str:
    try:
        cmd = [DOCKER_EXE, "ps", "--format", "json"]
        if all_containers:
            cmd.insert(2, "-a")
        result = _run_command(cmd, timeout=10)
        if result["success"]:
            containers = []
            for line in result["stdout"].strip().split("\n"):
                if line:
                    try:
                        containers.append(json.loads(line))
                    except:
                        pass
            return _success({"containers": containers, "count": len(containers)})
        return _error(result.get("stderr", "Docker failed"))
    except Exception as e:
        return _error(str(e))

@mcp_server.tool(name="docker_images", description="List Docker images.")
@auto_logged
def docker_images() -> str:
    try:
        cmd = [DOCKER_EXE, "images", "--format", "json"]
        result = _run_command(cmd, timeout=10)
        if result["success"]:
            images = []
            for line in result["stdout"].strip().split("\n"):
                if line:
                    try:
                        images.append(json.loads(line))
                    except:
                        pass
            return _success({"images": images, "count": len(images)})
        return _error("Docker failed")
    except Exception as e:
        return _error(str(e))

# =============================================================================
# WSL TOOLS (AUTO-LOGGED)
# =============================================================================

@mcp_server.tool(name="wsl_run", description="Run command in WSL/Ubuntu Linux.")
@auto_logged
def wsl_run(command: str, distribution: str = "") -> str:
    try:
        cmd = [WSL_EXE]
        if distribution:
            cmd.extend(["-d", distribution])
        cmd.extend(["--", "bash", "-c", command])
        result = _run_command(cmd, timeout=60)
        return _success({"command": command, "output": result["stdout"], "success": result["success"]})
    except Exception as e:
        return _error(str(e))

@mcp_server.tool(name="wsl_list", description="List WSL distributions.")
@auto_logged
def wsl_list() -> str:
    try:
        result = _run_command([WSL_EXE, "-l", "-v"], timeout=10)
        return _success({"distributions": result["stdout"]})
    except Exception as e:
        return _error(str(e))

# =============================================================================
# GIT TOOLS (AUTO-LOGGED)
# =============================================================================

@mcp_server.tool(name="git_status", description="Get Git status.")
@auto_logged
def git_status(repo_path: str = "") -> str:
    try:
        # Handle paths with spaces - use shell=True on Windows
        git_cmd = GIT_EXE if isinstance(GIT_EXE, str) else str(GIT_EXE)
        cwd = repo_path if repo_path else None
        
        # Verify git exists
        if not Path(git_cmd).exists() and not shutil.which("git"):
            return _error(f"Git not found at {git_cmd}")
        
        # Verify repo path exists if provided
        
        # Check if this is a huge repo that would hang
        if _is_huge_repo(cwd):
            return _success({"branch": "unknown", "changes": [], "clean": True, "path": cwd or "current", "note": "Skipped - repo too large"})
        if cwd and not Path(cwd).exists():
            return _error(f"Path not found: {cwd}")
        
        result = subprocess.run(
            [git_cmd, "status", "--porcelain", "-b"], 
            capture_output=True, 
            text=True, 
            cwd=cwd, 
            timeout=2,
            shell=False
        )
        
        if result.returncode != 0 and "not a git repository" in result.stderr.lower():
            return _error(f"Not a git repository: {cwd or 'current dir'}")
        
        lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
        branch = ""
        changes = []
        for line in lines:
            if line.startswith("##"):
                branch = line[3:].split("...")[0]
            elif line:
                changes.append(line)
        return _success({"branch": branch, "changes": changes, "clean": len(changes) == 0, "path": cwd or "current"})
    except Exception as e:
        return _error(f"Git error: {str(e)}")

@mcp_server.tool(name="git_log", description="Get recent commits.")
@auto_logged
def git_log(repo_path: str = "", count: int = 10) -> str:
    try:
        git_cmd = GIT_EXE if isinstance(GIT_EXE, str) else str(GIT_EXE)
        cwd = repo_path if repo_path else None
        
        # Verify path
        
        # Check if this is a huge repo that would hang
        if _is_huge_repo(cwd):
            return _success({"commits": [], "path": cwd or "current", "note": "Skipped - repo too large"})
        if cwd and not Path(cwd).exists():
            return _error(f"Path not found: {cwd}")
        
        result = subprocess.run(
            [git_cmd, "log", f"-{count}", "--pretty=format:%h|%an|%ar|%s"], 
            capture_output=True, 
            text=True, 
            cwd=cwd, 
            timeout=10
        )
        
        if result.returncode != 0:
            return _error(f"Git log failed: {result.stderr[:200]}")
        
        commits = []
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split("|", 3)
                if len(parts) == 4:
                    commits.append({"hash": parts[0], "author": parts[1], "date": parts[2], "message": parts[3]})
        return _success({"commits": commits, "path": cwd or "current"})
    except Exception as e:
        return _error(f"Git error: {str(e)}")

# =============================================================================
# NETWORK TOOLS (AUTO-LOGGED)
# =============================================================================

@mcp_server.tool(name="network_ping", description="Ping a host.")
@auto_logged
def network_ping(host: str, count: int = 4) -> str:
    try:
        result = _run_command(["ping", "-n", str(count), host], timeout=30)
        return _success({"host": host, "output": result["stdout"], "success": result["success"]})
    except Exception as e:
        return _error(str(e))

# =============================================================================
# PROJECT SCANNER TOOLS (AUTO-LOGGED)
# =============================================================================

@mcp_server.tool(name="project_scan_turbo", description="TURBO SCAN using Everything - FAST! Optional scan_paths: semicolon-separated folders.")
@auto_logged
def project_scan_turbo(output_dir: str = "", scan_paths: str = "") -> str:
    global _scan_status
    try:
        if _scan_status.get("state") == "running":
            return _error("Scan already running")
        if not EVERYTHING_CLI.exists():
            return _error("Everything CLI not found")
        
        out_dir = output_dir or str(SCAN_RESULTS_DIR)
        scan_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        if scan_paths.strip():
            folder_args = [p.strip().strip('"') for p in scan_paths.replace("|", ";").split(";") if p.strip()]
        else:
            folder_args = [str(REPO_ROOT)]
        _scan_status = {"state": "starting", "scan_id": scan_id, "type": "turbo", "scan_paths": folder_args}
        
        def run_turbo():
            global _scan_status
            log_file = REPO_ROOT / "logs" / f"turbo_scan_{scan_id}.log"
            try:
                _scan_status["state"] = "running"
                log_file.parent.mkdir(parents=True, exist_ok=True)
                cmd = [str(PYTHON_EXE), str(TURBO_SCANNER_SCRIPT), *folder_args, "-o", out_dir]
                with open(log_file, "w", encoding="utf-8", errors="replace") as log_f:
                    result = subprocess.run(
                        cmd,
                        stdout=log_f,
                        stderr=subprocess.STDOUT,
                        cwd=str(REPO_ROOT),
                        timeout=1800,
                    )
                _scan_status["state"] = "completed" if result.returncode == 0 else "error"
                _scan_status["log_file"] = str(log_file)
                if result.returncode != 0:
                    tail = log_file.read_text(encoding="utf-8", errors="replace")[-500:] if log_file.exists() else ""
                    _scan_status["error"] = tail or f"Scanner exited with code {result.returncode}"
            except Exception as e:
                _scan_status["state"] = "error"
                _scan_status["error"] = str(e)
        
        threading.Thread(target=run_turbo, daemon=True).start()
        return _success({"message": "TURBO scan started!", "scan_id": scan_id, "scan_paths": folder_args, "engine": "Everything (es.exe)"})
    except Exception as e:
        return _error(str(e))

@mcp_server.tool(name="project_scan_status", description="Check scan status.")
@auto_logged
def project_scan_status() -> str:
    try:
        status = dict(_scan_status)
        if SCAN_RESULTS_DIR.exists():
            scans = sorted([d for d in SCAN_RESULTS_DIR.iterdir() if d.is_dir()], reverse=True)
            if scans:
                status["latest_scan"] = scans[0].name
                summary = scans[0] / "summary.json"
                if summary.exists():
                    with open(summary, "r", encoding="utf-8") as f:
                        status["latest_summary"] = json.load(f)
        return _success(status)
    except Exception as e:
        return _error(str(e))

@mcp_server.tool(name="project_scan_results", description="Get scan results.")
@auto_logged
def project_scan_results(scan_id: str = "") -> str:
    try:
        if not scan_id:
            scans = sorted([d for d in SCAN_RESULTS_DIR.iterdir() if d.is_dir()], reverse=True)
            if not scans:
                return _error("No scans found")
            scan_dir = scans[0]
        else:
            scan_dir = SCAN_RESULTS_DIR / scan_id
        
        results = {"scan_id": scan_dir.name}
        for fname in ["summary.json", "analysis.json", "duplicates.json"]:
            fpath = scan_dir / fname
            if fpath.exists():
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if fname == "summary.json":
                        results["summary"] = data
                    elif fname == "analysis.json":
                        results["hubs"] = data.get("hubs", [])[:20]
                        results["orphans_count"] = len(data.get("orphans", []))
                    elif fname == "duplicates.json":
                        results["duplicate_groups"] = len(data)
        return _success(results)
    except Exception as e:
        return _error(str(e))

@mcp_server.tool(name="project_search", description="Search scanned files.")
@auto_logged
def project_search(query: str, scan_id: str = "") -> str:
    try:
        if not scan_id:
            scans = sorted([d for d in SCAN_RESULTS_DIR.iterdir() if d.is_dir()], reverse=True)
            if not scans:
                return _error("No scans")
            scan_dir = scans[0]
        else:
            scan_dir = SCAN_RESULTS_DIR / scan_id
        
        files_json = scan_dir / "files.json"
        if not files_json.exists():
            return _error("No files data")
        
        with open(files_json, "r", encoding="utf-8") as f:
            files = json.load(f)
        
        matches = [{"path": p, "name": i.get("name")} for p, i in files.items() if query.lower() in p.lower()][:50]
        return _success({"query": query, "matches": matches, "count": len(matches)})
    except Exception as e:
        return _error(str(e))

@mcp_server.tool(name="project_file_deps", description="Get file dependencies.")
@auto_logged
def project_file_deps(file_path: str, scan_id: str = "") -> str:
    try:
        if not scan_id:
            scans = sorted([d for d in SCAN_RESULTS_DIR.iterdir() if d.is_dir()], reverse=True)
            if not scans:
                return _error("No scans")
            scan_dir = scans[0]
        else:
            scan_dir = SCAN_RESULTS_DIR / scan_id
        
        deps_json = scan_dir / "dependencies.json"
        if not deps_json.exists():
            return _error("No deps data")
        
        with open(deps_json, "r", encoding="utf-8") as f:
            deps = json.load(f)
        
        forward = deps.get("forward", {})
        reverse = deps.get("reverse", {})
        match = next((p for p in forward if file_path.lower() in p.lower()), None)
        
        if not match:
            return _error(f"File not found: {file_path}")
        
        return _success({"file": match, "imports": forward.get(match, []), "imported_by": reverse.get(match, [])})
    except Exception as e:
        return _error(str(e))

# =============================================================================
# CONVERSATION TOOLS (NOT AUTO-LOGGED - to avoid loops)
# =============================================================================

@mcp_server.tool(name="conv_log", description="Log message to buffer (manual).")
def conv_log(role: str, content: str, save_now: bool = False) -> str:
    try:
        global _auto_log_buffer
        entry = {"id": _generate_id(), "timestamp": _now_iso(), "tool": "manual_log", "args": f"role={role}", "result": content[:200]}
        _auto_log_buffer.append(entry)
        if save_now or len(_auto_log_buffer) >= _auto_log_threshold:
            _auto_dump_logs()
        return _success({"logged": True, "buffer_size": len(_auto_log_buffer)})
    except Exception as e:
        return _error(str(e))

@mcp_server.tool(name="conv_dump", description="Force dump buffer NOW.")
def conv_dump(summary: str = "") -> str:
    try:
        if summary:
            _auto_log_buffer.append({"id": _generate_id(), "timestamp": _now_iso(), "tool": "summary", "args": "", "result": summary})
        count = len(_auto_log_buffer)
        _auto_dump_logs()
        return _success({"dumped": True, "entries_saved": count})
    except Exception as e:
        return _error(str(e))

@mcp_server.tool(name="conv_status", description="Check buffer status.")
def conv_status() -> str:
    return _success({
        "buffer_size": len(_auto_log_buffer),
        "threshold": _auto_log_threshold,
        "session": _auto_log_session,
        "last_dump": _auto_log_last_dump.isoformat()
    })

@mcp_server.tool(name="conv_set_threshold", description="Set auto-dump threshold.")
def conv_set_threshold(threshold: int = 5) -> str:
    global _auto_log_threshold
    _auto_log_threshold = max(1, min(50, threshold))
    return _success({"threshold": _auto_log_threshold})

def _read_autolog_entries(date: str = "", limit: int = 30) -> Dict[str, Any]:
    """Read auto-log JSONL for a date (default today)."""
    target = date or _today_str()
    dump_file = DUMPS_DIR / f"autolog_{target}.jsonl"
    if not dump_file.exists():
        return {"date": target, "entries": [], "count": 0, "file": str(dump_file)}
    entries: List[Dict] = []
    with open(dump_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    tail = entries[-limit:] if limit > 0 else entries
    return {"date": target, "entries": tail, "count": len(entries), "file": str(dump_file)}


def _load_operator_profile() -> Dict[str, Any]:
    """Load Fala 1 operator profile from canonical CBMS memory."""
    profile_path = (AIONS_V10 / "memory" / "operator_profile.json") if AIONS_V10 else None
    if not profile_path or not profile_path.is_file():
        return {
            "loaded": False,
            "path": str(profile_path) if profile_path else None,
            "error": "operator_profile.json not found",
        }
    try:
        with open(profile_path, "r", encoding="utf-8") as f:
            return {"loaded": True, "path": str(profile_path), "profile": json.load(f)}
    except Exception as e:
        return {"loaded": False, "path": str(profile_path), "error": str(e)}


@mcp_server.tool(name="conv_history", description="Get log history.")
def conv_history(date: str = "") -> str:
    try:
        data = _read_autolog_entries(date, limit=30)
        return _success({"date": data["date"], "entries": data["entries"], "count": data["count"]})
    except Exception as e:
        return _error(str(e))


@mcp_server.tool(
    name="session_bootstrap",
    description=(
        "One-call session bootstrap: system_health + recent auto-log + memory_recall. "
        "Use when sessionStart hook is unavailable (cloud agent, hooks disabled)."
    ),
)
def session_bootstrap(
    session_id: str = "claude_marcin_main",
    autolog_limit: int = 20,
    memory_query: str = "COMPACT_BOOTSTRAP session context recent work",
    memory_top_k: int = 3,
    include_yesterday: bool = True,
) -> str:
    """Combine health, autolog tail, and compact memory in one MCP call."""
    try:
        health_raw = json.loads(system_health())
        autolog_today = _read_autolog_entries("", limit=autolog_limit)
        autolog_entries = list(autolog_today["entries"])
        autolog_dates = [autolog_today["date"]] if autolog_today["entries"] else []

        if include_yesterday and len(autolog_entries) < autolog_limit:
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            older = _read_autolog_entries(yesterday, limit=autolog_limit)
            if older["entries"]:
                autolog_dates.append(yesterday)
                need = autolog_limit - len(autolog_entries)
                autolog_entries = older["entries"][-need:] + autolog_entries

        memory_raw = json.loads(
            memory_recall(session_id=session_id, query=memory_query, top_k=memory_top_k)
        )
        status_raw = json.loads(conv_status())

        operator_profile = _load_operator_profile()

        return _success({
            "bootstrap": True,
            "health": health_raw.get("data", health_raw),
            "autolog": {
                "dates": autolog_dates,
                "entries": autolog_entries,
                "count_shown": len(autolog_entries),
            },
            "memory": memory_raw.get("data", memory_raw),
            "conv_status": status_raw.get("data", status_raw),
            "operator_profile": operator_profile,
            "hook_hint": (
                "Desktop: .cursor/hooks sessionStart injects autolog automatically. "
                "Call conv_history() only after long gaps. "
                "Operator profile: aions_core/memory/operator_profile.json (Fala 1)."
            ),
        })
    except Exception as e:
        return _error(str(e))

# =============================================================================
# MEMORY TOOLS (AUTO-LOGGED)
# =============================================================================

@mcp_server.tool(name="memory_store", description="Store context to ChromaDB.")
@auto_logged
def memory_store(session_id: str, text: str, ttl_days: int = 30) -> str:
    try:
        doc_id = _generate_id()
        categories = extract_categories(text)
        metadata = with_provenance({"categories": ",".join(categories), "timestamp": _now_iso()})
        vs = get_vector_store()
        if vs:
            vs.add_items(session_id, [(doc_id, text, metadata)])
        memory_store_add(session_id, doc_id, text, metadata)
        return _success({"doc_id": doc_id, "categories": categories})
    except Exception as e:
        return _error(str(e))

@mcp_server.tool(name="memory_recall", description="Search memory.")
@auto_logged
def memory_recall(session_id: str, query: str, top_k: int = 5) -> str:
    try:
        results = []
        vs = get_vector_store()
        if vs:
            try:
                for hit in vs.search(session_id, query, top_k * 2):
                    results.append({"id": hit["id"], "text": hit["text"][:300], "score": hit["score"], "source": "chromadb"})
            except:
                pass
        for kr in memory_store_search(session_id, query, top_k):
            if not any(r["id"] == kr["id"] for r in results):
                results.append({"id": kr["id"], "text": kr["text"][:300], "score": kr["score"], "source": "korean"})
        cbms = get_cbms()
        if cbms:
            try:
                # FIX (score fabrication): previously every CBMS hit was hardcoded
                # to score=0.5 regardless of actual relevance, corrupting blended
                # ranking. Use the real graded confidence from control_plane's
                # cbms_gate.retrieve() (Korean-key overlap + lexical + Chroma
                # boost) instead of inventing a number. If a genuine score is
                # unavailable for a given chunk, mark it honestly rather than
                # faking one.
                cbms_score_by_id = {}
                try:
                    from control_plane.cbms_gate import retrieve as _cbms_gate_retrieve
                    gate_hits = _cbms_gate_retrieve(query, top_k=3).get("hits", [])
                    cbms_score_by_id = {h.get("id"): h.get("score") for h in gate_hits if h.get("id")}
                except Exception:
                    cbms_score_by_id = {}
                for cid in cbms.cbms_think(query).get("chunk_references", [])[:3]:
                    chunk = cbms.retrieve_chunk(cid)
                    if chunk:
                        real_score = cbms_score_by_id.get(cid)
                        entry = {"id": f"cbms:{cid}", "text": chunk.get("content", "")[:300], "source": "cbms"}
                        if real_score is not None:
                            entry["score"] = real_score
                        else:
                            entry["score"] = None
                            entry["score_available"] = False
                        results.append(entry)
            except:
                pass
        chroma_results = [r for r in results if r["source"] == "chromadb"]
        other_results = [r for r in results if r["source"] != "chromadb"]
        if chroma_results:
            chroma_results.sort(key=lambda x: (x["score"] if x["score"] is not None else -1), reverse=True)
            other_results.sort(key=lambda x: (x["score"] if x["score"] is not None else -1), reverse=True)
            results = chroma_results + other_results
        else:
            chroma_results = [r for r in results if r["source"] == "chromadb"]
        other_results = [r for r in results if r["source"] != "chromadb"]
        if chroma_results:
            chroma_results.sort(key=lambda x: (x["score"] if x["score"] is not None else -1), reverse=True)
            other_results.sort(key=lambda x: (x["score"] if x["score"] is not None else -1), reverse=True)
            results = chroma_results + other_results
        else:
            results.sort(key=lambda x: (x["score"] if x["score"] is not None else -1), reverse=True)
        return _success({"results": results[:top_k]})
    except Exception as e:
        return _error(str(e))

@mcp_server.tool(name="session_list", description="List sessions.")
@auto_logged
def session_list() -> str:
    try:
        sessions = []
        vs = get_vector_store()
        if vs:
            sessions = vs.list_sessions()
        return _success({"sessions": sessions})
    except Exception as e:
        return _error(str(e))

@mcp_server.tool(name="cbms_search", description="Direct CBMS search.")
@auto_logged
def cbms_search(query: str) -> str:
    try:
        cbms = get_cbms()
        if not cbms:
            return _error("CBMS not available")
        result = cbms.cbms_think(query)
        return _success({"answer": result.get("answer", ""), "chunks": result.get("chunk_references", [])})
    except Exception as e:
        return _error(str(e))

@mcp_server.tool(name="cbms_get_chunk", description="Get full CBMS chunk by ID. Returns complete content, references, metadata.")
@auto_logged
def cbms_get_chunk(chunk_id: str) -> str:
    try:
        cbms = get_cbms()
        if not cbms:
            return _error("CBMS not available")
        chunk = cbms.retrieve_chunk(chunk_id)
        if not chunk:
            return _error(f"Chunk '{chunk_id}' not found")
        return _success({
            "id": chunk.get("id", chunk_id),
            "concept": chunk.get("concept", ""),
            "content": chunk.get("content", ""),
            "references": chunk.get("references", []),
            "access_count": chunk.get("access_count", 0),
            "last_accessed": chunk.get("last_accessed"),
            "size": chunk.get("size", len(chunk.get("content", "")))
        })
    except Exception as e:
        return _error(str(e))

# =============================================================================
# ACAE — wyszukiwanie w KODZIE tego repozytorium
# =============================================================================
#
# CBMS odpowiada "co o tym wiemy", ACAE odpowiada "gdzie to jest w kodzie".
# Dwie strony tej samej odpowiedzi, dlatego stoja obok siebie w jednym serwerze,
# a nie w dwoch osobnych.
#
# KOSZT: indeks budowany RAZ przy pierwszym pytaniu (~2,3 s), kazde kolejne pytanie
# ponizej dziesieciu milisekund. Dlatego to musi zyc w dlugowiecznym procesie serwera,
# a nie byc odpalane od zera jak skrypt.

_acae_state: Dict[str, Any] = {
    "index": None, "entries": None, "reader": None, "built_at": None,
    "provenance": {}, "ranker": None, "files": 0, "symbols": 0,
}
_acae_lock = threading.Lock()


def _acae_build(force: bool = False) -> Dict[str, Any]:
    """
    Buduje indeks raz i trzyma go w pamieci procesu.

    Przy braku modelu albo opisow schodzi cicho do rankera leksykalnego — narzedzie
    ma dzialac gorzej, a nie nie dzialac wcale. Roznica jest zmierzona: 62% wobec 25%
    trafien na zbiorze 306 pytan zadanych po ludzku.
    """
    with _acae_lock:
        if _acae_state["index"] is not None and not force:
            return _acae_state
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))

        import tomllib

        from acae import parsecache
        from acae.core import collect_entries
        from acae.pack import FsLocator, FsReader

        acae_dir = REPO_ROOT / "acae"
        with open(acae_dir / "config" / "acae.toml", "rb") as fh:
            cfg = tomllib.load(fh)
        locator = FsLocator(
            root=str(REPO_ROOT),
            roots=cfg["pack"]["roots"],
            prune_dirs=cfg.get("baseline", {}).get("prune_dirs", []),
            max_file_bytes=cfg["pack"]["max_file_bytes"],
        )
        reader = FsReader(str(REPO_ROOT))

        cache_path = acae_dir / "_out" / "parse_cache.json"
        outline_cache = parsecache.load(cache_path)
        przed = len(outline_cache)
        entries, _skipped = collect_entries(locator, reader, outline_cache=outline_cache)
        if len(outline_cache) != przed:
            parsecache.save(cache_path, outline_cache)

        index, ranker, prov = None, "words", {}
        try:
            from acae.describe import load_descriptions
            from acae.embed import StaticEmbedder
            from acae.embedindex import EmbedIndex, index_key, load_vectors, save_vectors

            # `strict=False`: rozjazd pack_hash tylko oznacza opisy jako nieswieze.
            # W pomiarze przerywa, w uzyciu nie — bo gdy zmienisz dwa pliki ze 169,
            # opisy pozostalych 167 sa nadal prawdziwe.
            opisy, prov = load_descriptions(
                acae_dir / "_desc" / "descriptions.json", strict=False
            )
            model_dir = acae_dir / "_model"
            vec_path = acae_dir / "_out" / "embed_vectors.npz"
            klucz = index_key(entries, opisy, model_dir)
            wektory = load_vectors(vec_path, klucz)
            index = EmbedIndex(StaticEmbedder(model_dir), entries, opisy, vectors=wektory)
            if wektory is None:
                save_vectors(vec_path, klucz, index.M)
            ranker = "meaning"

            # Sprawdzenie swiezosci PO POKRYCIU, nie po `pack_hash`. Policzenie
            # aktualnego `pack_hash` wymaga zbudowania calego packa (~3,4 s) przy kazdym
            # starcie, a najgrozniejszy rodzaj rozjazdu — plik doszedl albo zniknal —
            # widac po samych sciezkach i kosztuje zero.
            prov = dict(prov)
            prov["files_without_description"] = sorted(
                {str(e["path"]) for e in entries} - set(opisy)
            )[:10]
        except Exception as e:
            prov = {"fallback_reason": f"{type(e).__name__}: {e}"}

        _acae_state.update(
            index=index, entries=entries, reader=reader, built_at=time.time(),
            provenance=prov, ranker=ranker, files=len(entries),
            symbols=sum(len(e["symbols"]) for e in entries),
        )
        return _acae_state


@mcp_server.tool(
    name="acae_ask",
    description=(
        "Find the code in THIS repository that answers a question. Returns a compact "
        "slice: matching symbols with their signatures, plus full bodies of the best few. "
        "ASK IN ENGLISH — the index is English; the same question in Polish scores 20% "
        "instead of 70%. Translate the user's question before calling. "
        "Costs roughly 4% of what grepping and reading files would cost. "
        "Use for 'where is X', 'what does Y', 'why does Z not work' about this codebase. "
        "For 'what do we know about X' use cbms_search instead."
    ),
)
@auto_logged
def acae_ask(query: str, drill: int = 3, outline_limit: int = 30, refresh: bool = False) -> str:
    try:
        if not query.strip():
            return _error("query is empty")
        st = _acae_build(force=refresh)

        from acae.retrieve import build_slice

        ranked = None
        if st["ranker"] == "meaning" and st["index"] is not None:
            ranked = st["index"].ranked(query, max(outline_limit, drill))

        # Tresc wycinka jest grupowana po pliku i sortowana ALFABETYCZNIE — tak zostal
        # zaprojektowany format, zeby dalo sie go czytac, i na nim stoi bramka M2.
        # Nie ruszamy go. Ale wtedy czytajacy nie wie, co bylo najlepszym trafieniem,
        # wiec kolejnosc trafnosci podajemy OBOK, w odpowiedzi narzedzia.
        top_files: List[str] = []
        if ranked:
            for r in ranked:
                p = str(r["path"])
                if p not in top_files:
                    top_files.append(p)

        start = time.time()
        text, meta = build_slice(
            st["entries"], query, st["reader"],
            outline_limit=outline_limit, drill_limit=drill, ranked=ranked,
        )
        elapsed = int((time.time() - start) * 1000)

        out_path = REPO_ROOT / "acae" / "_out" / "ask_slice.txt"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(text)

        return _success({
            "query": query,
            "ranker": st["ranker"],
            "scope": {"files": st["files"], "symbols": st["symbols"]},
            "slice_path": str(out_path),
            "best_matches": top_files[:8],
            "slice": {
                "files": meta["files"],
                "symbols": meta["outline_symbols"],
                "drilled": meta["drilled"],
                "terms": meta["terms"],
            },
            "elapsed_ms": elapsed,
            "files_without_description": st["provenance"].get("files_without_description", []),
            "fallback_reason": st["provenance"].get("fallback_reason"),
            "content": text.decode("utf-8", "replace"),
        })
    except Exception as e:
        return _error(f"{type(e).__name__}: {e}")


# =============================================================================
# CODE HEALTH — samoaudyt repo bez modelu i bez tokenow
# =============================================================================

def _health_run(nazwa: str, wyjscie: str, dodatkowe: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Uruchamia jeden ze skryptow audytu i oddaje jego raport JSON.

    Osobny proces, a nie import, z dwoch powodow. Skrypty sa napisane jako narzedzia
    wiersza polecen i dzialaja — regula ADDITIVE ONLY mowi, zeby ich nie przerabiac
    pod nowego wolajacego. A `probe_imports` uzywa `find_spec`, wiec MUSI widziec czysty
    interpreter: serwer ma juz zaimportowana polowe tych modulow i pozmieniana `sys.path`,
    wiec w jego procesie sonda odpowiadalaby na inne pytanie niz zadane.
    """
    import subprocess

    skrypt = REPO_ROOT / "acae" / "scripts" / f"{nazwa}.py"
    if not skrypt.exists():
        raise FileNotFoundError(f"brak skryptu audytu: {skrypt.name}")

    cmd = [sys.executable, str(skrypt), "--root", ".", "--json-out", wyjscie]
    cmd += dodatkowe or []
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True,
                          text=True, timeout=240)
    if proc.returncode != 0:
        raise RuntimeError(f"{nazwa} zakonczony kodem {proc.returncode}: "
                           f"{(proc.stderr or proc.stdout)[-400:]}")
    return json.loads((REPO_ROOT / wyjscie).read_text(encoding="utf-8"))


# Stan audytu. Liczenie idzie w WATKU, a nie w wywolaniu narzedzia.
#
# POWOD (zmierzony 2026-08-16 po restarcie): te same trzy skrypty trwaja 9,4 s
# uruchomione z terminala i ~2 s z procesu, ktory dopiero wstal — ale w ZYWYM,
# dlugo dzialajacym serwerze te same trzy uruchomienia zajmuja ~60 s. Sprawdzone
# po czasach zapisu plikow: praca sie KONCZY (audit.json 13:30:28, triaz 13:30:31,
# importy 13:30:33), tylko klient przestaje czekac po 60 s i melduje blad.
#
# Czyli narzedzie „nie dzialalo" wylacznie z punktu widzenia wolajacego. To jest
# ten sam rodzaj klamstwa, ktory tropimy w tym repo od rana, wiec nie zostawiam go:
# narzedzie ma ODPOWIADAC OD RAZU i uczciwie mowic, ze liczy.
_health_state: Dict[str, Any] = {"wynik": None, "kiedy": None, "trwa": False, "blad": None}
_health_lock = threading.Lock()


def _health_compute() -> Dict[str, Any]:
    """Pelny audyt. Wolane z watku w tle — NIGDY wprost z narzedzia."""
    start = time.time()
    surowy = _health_run("audit_calls", "acae/_out/audit.json")
    triaz = _health_run("triage_audit", "acae/_out/triaz.json")
    importy = _health_run("probe_imports", "acae/_out/importy.json")

    wyjatki = [x for x in triaz["B_wyjatki"] if x["kubelek"] == "RYZYKO"]
    parametry = [x for x in triaz["A_parametry"] if x["kubelek"] == "RYZYKO"]
    brak = importy["brakujace"]
    podsumowanie = {
        "sygnatury_niezgodne": len(surowy["D_sygnatury"]),
        "polkniety_wyjatek_wokol_zapisu": len(wyjatki),
        "ignorowany_parametr_ktory_ktos_podaje": len(parametry),
        "podsystem_zastapiony_zaslepka": len(brak),
    }
    return {
        "summary": podsumowanie,
        "total_findings": sum(podsumowanie.values()),
        "raw_counts_before_triage": {
            "swallowed_exceptions": len(surowy["B_polkniete"]),
            "unused_parameters": len(surowy["A_nieuzyte_parametry"]),
            "dead_imports": len(surowy["C_martwe_importy"]),
        },
        "elapsed_ms": int((time.time() - start) * 1000),
        "_D": surowy["D_sygnatury"],
        "_B": wyjatki,
        "_A": parametry,
        "_brak": brak,
        "_niepewne": len(importy.get("niepewne", [])),
    }


def _health_worker() -> None:
    try:
        wynik = _health_compute()
        with _health_lock:
            _health_state.update(wynik=wynik, kiedy=time.time(), trwa=False, blad=None)
    except Exception as e:                      # blad MUSI dojsc do wolajacego
        with _health_lock:
            _health_state.update(trwa=False, blad=f"{type(e).__name__}: {e}")


@mcp_server.tool(
    name="code_health",
    description=(
        "Static self-audit of THIS repository. No model, no tokens, ~10 seconds. "
        "Detects four failure patterns that have each already broken AIONS in production: "
        "(1) a call whose arguments do not match the function's signature — the endpoint "
        "returns 500 every time; (2) an exception swallowed around a WRITE — this is how "
        "conversation logging died silently for weeks; (3) a parameter accepted but never "
        "used while callers do pass it — this is how eight 'different' CRLA candidates all "
        "computed the same thing; (4) an optional import whose module cannot be found, which "
        "silently swaps a whole subsystem for a do-nothing stub. "
        "Findings are triaged: only high-risk ones are returned by default, because the raw "
        "counts are mostly benign noise. Run after editing code, or when something reports "
        "success but produces nothing. "
        "The report is CACHED and carries `report_age_s`; pass refresh=true to recompute. "
        "If the audit is still running you get {state: 'liczę'} immediately instead of a "
        "hang — call again in ~30 s."
    ),
)
@auto_logged
def code_health(level: str = "risk", limit: int = 25, refresh: bool = False) -> str:
    """level: 'risk' (tylko grozne) albo 'all' (same liczby). refresh: policz od nowa."""
    try:
        with _health_lock:
            trwa, wynik, kiedy, blad = (_health_state["trwa"], _health_state["wynik"],
                                        _health_state["kiedy"], _health_state["blad"])
            if not trwa and (refresh or wynik is None):
                _health_state.update(trwa=True, blad=None)
                threading.Thread(target=_health_worker, daemon=True).start()
                trwa = True

        # Krotkie czekanie: gdy maszyna jest szybka, wynik przychodzi w tym samym
        # wywolaniu. Gdy wolna — oddajemy sterowanie zamiast wisiec do limitu klienta.
        if trwa and (wynik is None or refresh):
            koniec = time.time() + 25
            while time.time() < koniec:
                time.sleep(0.5)
                with _health_lock:
                    if not _health_state["trwa"]:
                        wynik, kiedy, blad = (_health_state["wynik"], _health_state["kiedy"],
                                              _health_state["blad"])
                        break
            else:
                return _success({"state": "liczę", "hint":
                                 "audit is running in the background; call code_health "
                                 "again in ~30 s to get the report"})

        if blad:
            return _error(f"audyt nie doszedl do konca: {blad}")
        if wynik is None:
            return _success({"state": "liczę", "hint": "call again in ~30 s"})

        odp: Dict[str, Any] = {k: v for k, v in wynik.items() if not k.startswith("_")}
        odp["report_age_s"] = int(time.time() - kiedy) if kiedy else None

        if level == "risk":
            odp["signature_mismatch"] = [
                f"{x['plik']}:{x['linia']} {x['wolane']}() — {x['powod']}"
                for x in wynik["_D"][:limit]
            ]
            odp["swallowed_around_write"] = [
                f"{x['plik']}:{x['linia']} — {x['powod']}" for x in wynik["_B"][:limit]
            ]
            odp["ignored_parameter"] = [
                f"{x['plik']}:{x['linia']} {x['funkcja']}() ignores `{x['parametr']}` — {x['powod']}"
                for x in wynik["_A"][:limit]
            ]
            odp["missing_module"] = [
                f"{x['plik']}:{x['linia']} needs `{x['modul']}` — "
                + (f"it lives in {x['lezy_w'][0]}" if x["lezy_w"] else "NOT IN THE REPO AT ALL")
                for x in wynik["_brak"][:limit]
            ]
            # Nierozstrzygniete mowimy GLOSNO. Milczenie o nich czytaloby sie jak
            # "sprawdzone i czyste", a to nieprawda: dla tych plikow sonda nie ma zdania.
            odp["undecided_imports"] = wynik["_niepewne"]

        return _success(odp)
    except Exception as e:
        return _error(f"{type(e).__name__}: {e}")


# =============================================================================
# OPERATOR SENSES — Google Calendar (read-only)
# =============================================================================

def _calendar_get_events_impl(
    start: str,
    end: str,
    max_results: int = 10,
) -> dict[str, Any]:
    """Load calendar integration and fetch events (raises on misconfiguration)."""
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from runtime.integrations.calendar.get_events import get_events as _cal_get_events

    events = _cal_get_events(start, end, max_results=max_results)
    return {
        "count": len(events),
        "events": events,
        "start": start,
        "end": end,
        "max_results": max_results,
    }


@mcp_server.tool(
    name="calendar_get_events",
    description=(
        "Google Calendar read-only: list events between start and end (ISO date/datetime). "
        "Alias: calendar.get_events. Requires runtime/secrets/google_calendar_token.json."
    ),
)
@auto_logged
def calendar_get_events(start: str, end: str, max_results: int = 10) -> str:
    try:
        payload = _calendar_get_events_impl(start, end, max_results=max_results)
        return _success(payload)
    except Exception as exc:
        name = type(exc).__name__
        if name in ("NotConfiguredError", "DependencyMissingError"):
            return _error(str(exc))
        return _error(f"calendar_get_events failed: {exc}")

# =============================================================================
# SYSTEM HEALTH (AUTO-LOGGED)
# =============================================================================

def _component_state(component: Any) -> str:
    if component == "FAILED":
        return "failed"
    if component is None:
        return "not_loaded"
    return "ready"


def _run_with_wall_timeout(fn: Callable[[], Dict[str, Any]], timeout_s: float) -> Dict[str, Any]:
    """Return within timeout_s even if the worker is stuck in slow startup code."""
    result_queue: "queue.Queue[Dict[str, Any]]" = queue.Queue(maxsize=1)

    def _worker() -> None:
        try:
            result_queue.put({"ok": True, "payload": fn()}, block=False)
        except Exception as exc:
            result_queue.put({"ok": False, "error": str(exc)}, block=False)

    thread = threading.Thread(target=_worker, daemon=True, name="aions-system-health")
    thread.start()
    try:
        result = result_queue.get(timeout=timeout_s)
    except queue.Empty:
        return {"ok": False, "error": "timeout"}
    return result


def _system_health_payload(deep: bool = False) -> Dict[str, Any]:
    backend = _vector_store_backend()
    provider = _search_provider()
    health = {
        "server": "v6 DEBILOODPORNE",
        "platform": PLATFORM_NAME,
        "deployment_profile": DEPLOYMENT_PROFILE,
        "health_mode": "deep" if deep else "fast",
        "health_timeout_s": SYSTEM_HEALTH_TIMEOUT_SECONDS,
        "vector_backend": backend,
        "api_base_url": API_BASE_URL if backend == "api" else None,
        "search_provider": provider,
        "search": search_provider_status(
            provider,
            linux_provider=LINUX_SEARCH_PROVIDER,
            everything_available=EVERYTHING_CLI.exists(),
        ),
        "auto_log_buffer": len(_auto_log_buffer),
        "auto_log_threshold": _auto_log_threshold,
        "scan_status": _scan_status.get("state", "idle"),
        "everything": "ok" if EVERYTHING_CLI.exists() else "missing",
        "docker": "ok" if shutil.which("docker") else "missing",
        "wsl": "ok" if shutil.which("wsl") else "missing",
        "git": "ok" if shutil.which("git") else "missing",
        "chromadb": {
            "state": _component_state(_vector_store),
            "check": "deferred" if not deep else "deep",
        },
        "cbms": {
            "state": _component_state(_cbms_memory),
            "check": "deferred" if not deep else "deep",
        },
    }
    try:
        health["desktop_enabled"] = DESKTOP_ENABLED
        health["desktop_provider"] = getattr(DESKTOP_PROVIDER, "provider_name", "unknown")
        if deep:
            health["desktop_capabilities"] = desktop_provider_capabilities(DESKTOP_PROVIDER)
            health["desktop"] = "ok" if DESKTOP_ENABLED and DESKTOP_PROVIDER.is_ready() else DESKTOP_PROVIDER.unavailable_message()
        else:
            health["desktop"] = "deferred"
    except Exception as de:
        health["desktop"] = f"unavailable: {de}"

    if deep:
        vs = get_vector_store()
        health["chromadb"] = {
            "state": "ready" if vs else "failed",
            "sessions": vs.sessions_count() if vs else None,
            "check": "deep",
        }
        cbms = get_cbms()
        health["cbms"] = {
            "state": "ready" if cbms else "failed",
            "chunks": cbms.get_memory_stats().get("total_chunks", 0) if cbms else None,
            "check": "deep",
        }
    return health


@mcp_server.tool(name="system_health", description="System health check.")
@auto_logged
def system_health(deep: bool = False) -> str:
    start = time.perf_counter()
    timeout_s = SYSTEM_HEALTH_TIMEOUT_SECONDS
    try:
        result = _run_with_wall_timeout(lambda: _system_health_payload(deep=bool(deep)), timeout_s)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        if not result.get("ok"):
            if result.get("error") == "timeout":
                return json.dumps({
                    "status": "error",
                    "error": "timeout",
                    "message": f"system_health exceeded {timeout_s:.1f}s wall-clock deadline",
                    "elapsed_ms": elapsed_ms,
                    "timeout_s": timeout_s,
                    "deep": bool(deep),
                    "timestamp": _now_iso(),
                }, ensure_ascii=False)
            return _error(result.get("error", "system_health failed"))
        health = result["payload"]
        health["elapsed_ms"] = elapsed_ms
        return _success(health)
    except Exception as e:
        return _error(str(e))

# =============================================================================
# PLAYWRIGHT BROWSER TOOLS (AUTO-LOGGED)
# Playwright Sync API must run off the MCP asyncio loop — dedicated thread.
# =============================================================================

import concurrent.futures

_browser_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="aions-playwright")
_browser_state: Dict[str, Any] = {"playwright": None, "browser": None, "context": None, "page": None}
_browser_init_error: Optional[str] = None
_page_snapshot = None

def _browser_thread_init() -> None:
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 720})
    page = context.new_page()
    _browser_state["playwright"] = pw
    _browser_state["browser"] = browser
    _browser_state["context"] = context
    _browser_state["page"] = page
    log("Playwright browser launched")

def _run_browser(fn: Callable, timeout: int = 60) -> Any:
    global _browser_init_error
    def _task():
        if _browser_state["page"] is None:
            _browser_thread_init()
        return fn(_browser_state["page"])

    try:
        return _browser_executor.submit(_task).result(timeout=timeout)
    except Exception as e:
        _browser_init_error = str(e)
        log(f"Playwright op failed: {e}")
        raise

def get_browser():
    """Legacy helper — page must only be used inside _run_browser."""
    try:
        _run_browser(lambda page: page)
        return _browser_state["browser"], _browser_state["page"]
    except Exception:
        return None, None

def _browser_unavailable_msg() -> str:
    return f"Browser not available: {_browser_init_error or 'init failed'}"

@mcp_server.tool(name="browser_navigate", description="Navigate to URL in browser.")
@auto_logged
def browser_navigate(url: str) -> str:
    try:
        def op(page):
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            return {"url": page.url, "title": page.title()}
        return _success(_run_browser(op))
    except Exception as e:
        return _error(_browser_unavailable_msg() if "Sync API" in str(e) or _browser_init_error else str(e))

@mcp_server.tool(name="browser_snapshot", description="Get accessibility snapshot of current page.")
@auto_logged
def browser_snapshot() -> str:
    global _page_snapshot
    try:
        def op(page):
            snapshot = page.accessibility.snapshot()
            return snapshot, page.url, page.title()

        snapshot, url, title = _run_browser(op)
        _page_snapshot = snapshot

        def flatten_tree(node, depth=0, results=None):
            if results is None:
                results = []
            if not node:
                return results
            name = node.get("name", "")
            role = node.get("role", "")
            if name or role not in ("none", "generic", ""):
                ref = f"ref_{len(results)}"
                results.append({"ref": ref, "role": role, "name": name[:100], "depth": depth})
            for child in node.get("children", []):
                flatten_tree(child, depth + 1, results)
            return results

        elements = flatten_tree(snapshot)
        return _success({"url": url, "title": title, "elements": elements[:100]})
    except Exception as e:
        return _error(_browser_unavailable_msg() if _browser_init_error else str(e))

@mcp_server.tool(name="browser_click", description="Click element by text or selector.")
@auto_logged
def browser_click(selector: str = "", text: str = "") -> str:
    try:
        def op(page):
            if text:
                page.get_by_text(text, exact=False).first.click(timeout=5000)
            elif selector:
                page.click(selector, timeout=5000)
            else:
                raise ValueError("Provide selector or text")
            page.wait_for_load_state("domcontentloaded", timeout=5000)
            return {"clicked": text or selector, "url": page.url}
        return _success(_run_browser(op))
    except ValueError as e:
        return _error(str(e))
    except Exception as e:
        return _error(_browser_unavailable_msg() if _browser_init_error else str(e))

@mcp_server.tool(name="browser_type", description="Type text into input field.")
@auto_logged
def browser_type(selector: str = "", text: str = "", placeholder: str = "", submit: bool = False) -> str:
    try:
        def op(page):
            if placeholder:
                elem = page.get_by_placeholder(placeholder, exact=False).first
            elif selector:
                elem = page.locator(selector).first
            else:
                raise ValueError("Provide selector or placeholder")
            elem.fill(text)
            if submit:
                elem.press("Enter")
                page.wait_for_load_state("domcontentloaded", timeout=5000)
            return {"typed": text[:50], "submitted": submit}
        return _success(_run_browser(op))
    except ValueError as e:
        return _error(str(e))
    except Exception as e:
        return _error(_browser_unavailable_msg() if _browser_init_error else str(e))

@mcp_server.tool(name="browser_screenshot", description="Take screenshot of current page.")
@auto_logged
def browser_screenshot(filename: str = "", full_page: bool = False) -> str:
    try:
        fname = filename or f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        fpath = DUMPS_DIR / fname

        def op(page):
            page.screenshot(path=str(fpath), full_page=full_page)
            return {"file": str(fpath), "url": page.url}
        return _success(_run_browser(op))
    except Exception as e:
        return _error(_browser_unavailable_msg() if _browser_init_error else str(e))

@mcp_server.tool(name="browser_get_text", description="Get text content from page or element.")
@auto_logged
def browser_get_text(selector: str = "") -> str:
    try:
        def op(page):
            if selector:
                text = page.locator(selector).first.inner_text(timeout=5000)
            else:
                text = page.inner_text("body")
            return {"text": text[:5000], "length": len(text)}
        return _success(_run_browser(op))
    except Exception as e:
        return _error(_browser_unavailable_msg() if _browser_init_error else str(e))

@mcp_server.tool(name="browser_close", description="Close browser.")
@auto_logged
def browser_close() -> str:
    def op(_page):
        global _browser_init_error
        if _browser_state["page"]:
            _browser_state["page"].close()
        if _browser_state["context"]:
            _browser_state["context"].close()
        if _browser_state["browser"]:
            _browser_state["browser"].close()
        if _browser_state["playwright"]:
            _browser_state["playwright"].stop()
        _browser_state.update({"playwright": None, "browser": None, "context": None, "page": None})
        _browser_init_error = None
        return {"closed": True}

    try:
        if _browser_state["page"] is None:
            return _success({"closed": True})
        return _success(_browser_executor.submit(op, _browser_state["page"]).result(timeout=30))
    except Exception as e:
        return _error(str(e))

@mcp_server.tool(name="browser_evaluate", description="Execute JavaScript on page.")
@auto_logged
def browser_evaluate(script: str) -> str:
    try:
        def op(page):
            result = page.evaluate(script)
            return {"result": str(result)[:2000]}
        return _success(_run_browser(op))
    except Exception as e:
        return _error(_browser_unavailable_msg() if _browser_init_error else str(e))

# =============================================================================
# DESKTOP CONTROL TOOLS (AUTO-LOGGED)
# pyautogui / pywin32 must run off the MCP asyncio loop — dedicated thread.
# =============================================================================

_desktop_import_ok = True


def _desktop_err(e: Exception) -> str:
    msg = str(e)
    if (not _desktop_import_ok) or isinstance(e, DesktopProviderError) or "Desktop" in msg or "dependency" in msg.lower():
        try:
            return DESKTOP_PROVIDER.unavailable_message()
        except Exception:
            pass
    return msg


@mcp_server.tool(name="desktop_snapshot", description="Screenshot full screen or active window; returns base64 PNG + dimensions.")
@auto_logged
def desktop_snapshot(target: str = "screen") -> str:
    try:
        payload = DESKTOP_PROVIDER.snapshot(target=target)
        return _success(payload, guard=True)
    except Exception as e:
        return _error(_desktop_err(e))


@mcp_server.tool(name="desktop_click", description="Click at screen coordinates (x, y). button: left/right/middle; optional double click.")
@auto_logged
def desktop_click(x: int, y: int, button: str = "left", double: bool = False) -> str:
    try:
        return _success(DESKTOP_PROVIDER.click(x, y, button, double))
    except Exception as e:
        return _error(_desktop_err(e))


@mcp_server.tool(name="desktop_type", description="Type text; optional clear_first (Ctrl+A). Optionally click x,y first.")
@auto_logged
def desktop_type(text: str, clear_first: bool = False, x: int = 0, y: int = 0, click_first: bool = False, press_enter: bool = False) -> str:
    try:
        pos_x = int(x) if click_first else None
        pos_y = int(y) if click_first else None
        return _success(DESKTOP_PROVIDER.type(text, clear_first, pos_x, pos_y, press_enter))
    except Exception as e:
        return _error(_desktop_err(e))


@mcp_server.tool(name="desktop_key", description="Press key or combo, e.g. 'enter', 'ctrl+c', 'alt+tab'.")
@auto_logged
def desktop_key(combo: str) -> str:
    try:
        return _success(DESKTOP_PROVIDER.key(combo))
    except Exception as e:
        return _error(_desktop_err(e))


@mcp_server.tool(name="desktop_windows", description="List visible open windows (title, hwnd, process).")
@auto_logged
def desktop_windows() -> str:
    try:
        return _success(DESKTOP_PROVIDER.windows())
    except Exception as e:
        return _error(_desktop_err(e))


@mcp_server.tool(name="desktop_focus", description="Focus window by title substring or hwnd.")
@auto_logged
def desktop_focus(title: str = "", hwnd: int = 0) -> str:
    try:
        h = int(hwnd) if hwnd else None
        return _success(DESKTOP_PROVIDER.focus(title, h))
    except Exception as e:
        return _error(_desktop_err(e))


@mcp_server.tool(name="desktop_launch", description="Launch app by path or known exe name (notepad, calc, etc.).")
@auto_logged
def desktop_launch(path_or_name: str, args: str = "") -> str:
    try:
        return _success(DESKTOP_PROVIDER.launch(path_or_name, args))
    except Exception as e:
        return _error(_desktop_err(e))


@mcp_server.tool(name="desktop_scroll", description="Scroll at x,y. amount: positive=up, negative=down.")
@auto_logged
def desktop_scroll(x: int, y: int, amount: int = 3, direction: str = "vertical") -> str:
    try:
        return _success(DESKTOP_PROVIDER.scroll(x, y, amount, direction))
    except Exception as e:
        return _error(_desktop_err(e))


@mcp_server.tool(name="desktop_shell", description="Run a host shell command (max 30s timeout); returns stdout/stderr.")
@auto_logged
def desktop_shell(command: str, timeout: int = 30) -> str:
    try:
        return _success(DESKTOP_PROVIDER.shell(command, timeout))
    except Exception as e:
        return _error(_desktop_err(e))


@mcp_server.tool(name="desktop_ui_tree", description="Simplified UI accessibility tree of the active window (pywinauto).")
@auto_logged
def desktop_ui_tree(max_depth: int = 4, max_nodes: int = 80) -> str:
    try:
        return _success(DESKTOP_PROVIDER.ui_tree(max_depth, max_nodes))
    except Exception as e:
        return _error(_desktop_err(e))


@mcp_server.tool(name="desktop_clipboard", description="Read or write host clipboard. action: get|set; text required for set.")
@auto_logged
def desktop_clipboard(action: str, text: str = "") -> str:
    try:
        return _success(DESKTOP_PROVIDER.clipboard(action, text))
    except Exception as e:
        return _error(_desktop_err(e))

# =============================================================================
# MCP CATALOG (BUILT-IN)
# =============================================================================

MCP_CATALOG = {
    "github-official": {"description": "GitHub API integration", "url": "https://github.com/github/github-mcp-server"},
    "filesystem": {"description": "Local filesystem operations", "url": "https://github.com/anthropics/mcp-servers"},
    "fetch": {"description": "HTTP fetch tool", "url": "https://github.com/anthropics/mcp-servers"},
    "puppeteer": {"description": "Browser automation with Puppeteer", "url": "https://github.com/anthropics/mcp-servers"},
    "postgres": {"description": "PostgreSQL database access", "url": "https://github.com/anthropics/mcp-servers"},
    "sqlite": {"description": "SQLite database operations", "url": "https://github.com/anthropics/mcp-servers"},
    "brave-search": {"description": "Brave Search API", "url": "https://github.com/anthropics/mcp-servers"},
    "google-drive": {"description": "Google Drive integration", "url": "https://github.com/anthropics/mcp-servers"},
    "slack": {"description": "Slack workspace integration", "url": "https://github.com/anthropics/mcp-servers"},
    "memory": {"description": "Knowledge graph memory", "url": "https://github.com/anthropics/mcp-servers"},
    "sequential-thinking": {"description": "Step-by-step reasoning", "url": "https://github.com/anthropics/mcp-servers"},
    "time": {"description": "Time and timezone tools", "url": "https://github.com/anthropics/mcp-servers"},
    "context7": {"description": "Context window management", "url": "https://github.com/upstash/context7"},
    "playwright": {"description": "Browser automation (ALREADY BUILT-IN!)", "url": "built-in"},
    "desktop-control": {"description": "Windows desktop automation (ALREADY BUILT-IN! desktop_* tools)", "url": "built-in"},
    "aions-context": {"description": "THIS SERVER - ChromaDB + CBMS + Everything + Desktop", "url": "built-in"},
}

@mcp_server.tool(name="mcp_find", description="Search MCP servers catalog.")
@auto_logged
def mcp_find(query: str, limit: int = 10) -> str:
    try:
        query_lower = query.lower()
        matches = []
        for name, info in MCP_CATALOG.items():
            if query_lower in name.lower() or query_lower in info["description"].lower():
                matches.append({"name": name, "description": info["description"], "url": info["url"]})
        return _success({"query": query, "servers": matches[:limit], "total": len(matches)})
    except Exception as e:
        return _error(str(e))

@mcp_server.tool(name="mcp_list", description="List all available MCP servers in catalog.")
@auto_logged
def mcp_list() -> str:
    try:
        servers = [{"name": k, "description": v["description"]} for k, v in MCP_CATALOG.items()]
        return _success({"servers": servers, "total": len(servers)})
    except Exception as e:
        return _error(str(e))

@mcp_server.tool(name="mcp_info", description="Get detailed info about MCP server.")
@auto_logged
def mcp_info(name: str) -> str:
    try:
        if name in MCP_CATALOG:
            info = MCP_CATALOG[name]
            return _success({"name": name, **info})
        return _error(f"Server '{name}' not found in catalog")
    except Exception as e:
        return _error(str(e))

# =============================================================================
# WEB FETCH TOOL (AUTO-LOGGED)
# =============================================================================

@mcp_server.tool(name="web_fetch", description="Fetch URL content and extract text.")
@auto_logged
def web_fetch(url: str, selector: str = "") -> str:
    try:
        _, page = get_browser()
        if not page:
            # Fallback to httpx
            import httpx
            resp = httpx.get(url, follow_redirects=True, timeout=30)
            return _success({"url": str(resp.url), "status": resp.status_code, "text": resp.text[:5000]})

        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        if selector:
            text = page.locator(selector).first.inner_text(timeout=5000)
        else:
            text = page.inner_text("body")
        return _success({"url": page.url, "title": page.title(), "text": text[:5000]})
    except Exception as e:
        return _error(str(e))

# =============================================================================
# ENTRY POINT
# =============================================================================

# =============================================================================
# SEQUENTIAL THINKING ENGINE (AIONS FUSION v1.0)
# =============================================================================
# WKLEJONE AUTOMATYCZNIE PRZEZ backup_and_install.ps1
# Data: {TIMESTAMP}
# =============================================================================
"""
Integruje Sequential Thinking bezpośrednio z AIONS:
- Auto-search CBMS przy każdym kroku myślowym
- Sugestie narzędzi AIONS na podstawie kontekstu
- Persistent thinking sessions z thread-safety
- Branch/parallel reasoning dla eksploracji alternatyw
- Auto-store conclusions do ChromaDB
"""

import concurrent.futures
from threading import Lock

# Thread-safe storage for thinking sessions
_thinking_sessions: Dict[str, Dict] = {}
_thinking_lock = Lock()
_thinking_cleanup_interval = timedelta(hours=1)

# Prevent auto-logging loops for status checks
SKIP_LOG_TOOLS.add("think_status")

# Tool suggestion keywords -> AIONS tools mapping
THINK_TOOL_KEYWORDS = {
    # File operations
    "file": ["fast_search", "fast_search_ext", "project_search"],
    "find": ["fast_search", "cbms_search", "project_search"],
    "search": ["fast_search", "cbms_search", "memory_recall"],
    "locate": ["fast_search", "fast_search_ext"],
    
    # Code analysis
    "code": ["project_scan_turbo", "project_file_deps", "git_status"],
    "function": ["cbms_search", "project_search", "project_file_deps"],
    "class": ["cbms_search", "project_search"],
    "import": ["project_file_deps", "project_search"],
    "dependency": ["project_file_deps", "project_scan_results"],
    
    # Memory & knowledge
    "remember": ["memory_recall", "cbms_search", "conv_history"],
    "memory": ["memory_store", "memory_recall", "session_list"],
    "knowledge": ["cbms_search", "cbms_get_chunk", "memory_recall"],
    "context": ["cbms_search", "memory_recall"],
    "history": ["conv_history", "git_log", "memory_recall"],
    
    # System operations
    "docker": ["docker_ps", "docker_images"],
    "container": ["docker_ps", "docker_images"],
    "linux": ["wsl_run", "wsl_list"],
    "wsl": ["wsl_run", "wsl_list"],
    "git": ["git_status", "git_log"],
    "commit": ["git_log", "git_status"],
    
    # Web & browser
    "web": ["browser_navigate", "web_fetch"],
    "browser": ["browser_navigate", "browser_snapshot", "browser_screenshot"],
    "url": ["browser_navigate", "web_fetch"],
    "page": ["browser_snapshot", "browser_get_text"],
    "screenshot": ["desktop_snapshot", "browser_screenshot"],
    "desktop": ["desktop_snapshot", "desktop_windows", "desktop_click"],
    "pulpit": ["desktop_snapshot", "desktop_windows", "desktop_click"],
    "okno": ["desktop_windows", "desktop_focus"],
    "klik": ["desktop_click"],
    "clipboard": ["desktop_clipboard"],
    "schowek": ["desktop_clipboard"],
    
    # Network & health
    "network": ["network_ping", "system_health"],
    "ping": ["network_ping"],
    "health": ["system_health"],
    
    # Project scanning
    "scan": ["project_scan_turbo", "project_scan_status", "project_scan_results"],
    "project": ["project_scan_turbo", "project_search", "project_file_deps"],
    "analyze": ["project_scan_turbo", "cbms_search", "project_scan_results"],
    # Polish keywords (same mappings as English)
    "plik": ["fast_search", "fast_search_ext", "project_search"],
    "szukaj": ["fast_search", "cbms_search", "memory_recall"],
    "znajdz": ["fast_search", "cbms_search", "project_search"],
    "pamiec": ["memory_store", "memory_recall", "session_list"],
    "zapamietaj": ["memory_store", "memory_recall"],
    "wiedza": ["cbms_search", "cbms_get_chunk", "memory_recall"],
    "kontekst": ["cbms_search", "memory_recall"],
    "historia": ["conv_history", "git_log", "memory_recall"],
    "projekt": ["project_scan_turbo", "project_search", "project_file_deps"],
    "skan": ["project_scan_turbo", "project_scan_status", "project_scan_results"],
    "kod": ["project_scan_turbo", "project_file_deps", "git_status"],
    "zaleznosc": ["project_file_deps", "project_scan_results"],
    "zaleznosci": ["project_file_deps", "project_scan_results"],
    "siec": ["network_ping", "system_health"],
    "zdrowie": ["system_health"],
}

def _suggest_aions_tools(text: str) -> List[Dict[str, Any]]:
    """Analizuje tekst i sugeruje odpowiednie narzędzia AIONS."""
    suggestions = []
    text_lower = text.lower()
    seen_tools = set()
    
    for keyword, tools in THINK_TOOL_KEYWORDS.items():
        if keyword in text_lower:
            for tool in tools:
                if tool not in seen_tools:
                    seen_tools.add(tool)
                    pos = text_lower.find(keyword)
                    confidence = 0.9 if pos < 50 else 0.7 if pos < 200 else 0.5
                    suggestions.append({
                        "tool": tool,
                        "keyword": keyword,
                        "confidence": confidence,
                        "reason": f"Keyword '{keyword}' detected in thought"
                    })
    
    suggestions.sort(key=lambda x: x["confidence"], reverse=True)
    return suggestions[:5]

def _thinking_auto_cbms(text: str, timeout: float = 2.0) -> Dict[str, Any]:
    """Automatyczne przeszukanie CBMS z timeout protection."""
    try:
        cbms = get_cbms()
        if not cbms:
            return {"status": "unavailable", "chunks": []}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(cbms.cbms_think, text[:500])
            try:
                result = future.result(timeout=timeout)
                return {
                    "status": "ok",
                    "answer": result.get("answer", "")[:500],
                    "chunks": result.get("chunk_references", [])[:5]
                }
            except concurrent.futures.TimeoutError:
                return {"status": "timeout", "chunks": []}
    except Exception as e:
        return {"status": "error", "error": str(e), "chunks": []}

def _thinking_cleanup():
    """Usuwa sesje thinking starsze niż 1 godzina."""
    with _thinking_lock:
        now = datetime.now(timezone.utc)
        expired = []
        for sid, data in _thinking_sessions.items():
            try:
                created = datetime.fromisoformat(data["created"].replace("Z", "+00:00"))
                if now - created > _thinking_cleanup_interval:
                    expired.append(sid)
            except:
                expired.append(sid)
        for sid in expired:
            del _thinking_sessions[sid]
        return len(expired)


@mcp_server.tool(name="think_start", description="Start sequential thinking chain with AIONS context integration. Auto-searches CBMS and suggests relevant tools.")
@auto_logged
def think_start(
    goal: str,
    context: str = "",
    auto_search_cbms: bool = True,
    max_steps: int = 10
) -> str:
    """
    Inicjalizuje nowy łańcuch myślowy.
    
    Args:
        goal: Cel analizy/rozumowania
        context: Dodatkowy kontekst (opcjonalny)
        auto_search_cbms: Czy automatycznie przeszukać CBMS dla kontekstu
        max_steps: Maksymalna liczba kroków (default: 10)
    
    Returns:
        JSON z session_id, cbms_context, suggested_tools
    """
    try:
        cleaned = _thinking_cleanup()
        session_id = f"think_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{_generate_id()}"
        
        session = {
            "id": session_id,
            "goal": goal,
            "context": context,
            "created": _now_iso(),
            "max_steps": max_steps,
            "current_step": 0,
            "steps": [],
            "branches": {"main": []},
            "active_branch": "main",
            "status": "active",
            "cbms_context": None,
            "suggested_tools": []
        }
        
        cbms_result = {"status": "skipped", "chunks": []}
        if auto_search_cbms:
            search_text = f"{goal} {context}".strip()
            cbms_result = _thinking_auto_cbms(search_text)
            session["cbms_context"] = cbms_result
        
        combined_text = f"{goal} {context}"
        suggested = _suggest_aions_tools(combined_text)
        session["suggested_tools"] = suggested
        
        with _thinking_lock:
            _thinking_sessions[session_id] = session
        
        return _success({
            "session_id": session_id,
            "goal": goal,
            "max_steps": max_steps,
            "cbms_context": {
                "status": cbms_result.get("status"),
                "relevant_chunks": cbms_result.get("chunks", [])[:3],
                "preview": cbms_result.get("answer", "")[:200] if cbms_result.get("answer") else None
            },
            "suggested_tools": suggested,
            "message": f"Thinking session started. Use think_step() to add reasoning steps.",
            "sessions_cleaned": cleaned
        }, guard=False)
        
    except Exception as e:
        log(f"think_start error: {e}")
        return _error(f"Failed to start thinking: {str(e)}")


@mcp_server.tool(name="think_step", description="Execute single thinking step with auto CBMS lookup and tool suggestions.")
@auto_logged
def think_step(
    session_id: str,
    thought: str,
    step_number: int,
    needs_more_steps: bool = True,
    branch_id: str = "main",
    auto_cbms: bool = True
) -> str:
    """
    Wykonuje pojedynczy krok myślowy z auto-integracją AIONS.
    
    Args:
        session_id: ID sesji thinking (z think_start)
        thought: Treść myśli/analizy
        step_number: Numer kroku (1-indexed)
        needs_more_steps: Czy potrzebne dalsze kroki
        branch_id: ID gałęzi (default: "main")
        auto_cbms: Czy auto-szukać w CBMS
    """
    try:
        with _thinking_lock:
            if session_id not in _thinking_sessions:
                return _error(f"Session '{session_id}' not found. Use think_start() first.")
            
            session = _thinking_sessions[session_id]
            
            if session["status"] != "active":
                return _error(f"Session is {session['status']}. Cannot add steps.")
            
            if step_number > session["max_steps"]:
                return _error(f"Exceeded max steps ({session['max_steps']})")
            
            if branch_id not in session["branches"]:
                session["branches"][branch_id] = []
        
        cbms_hits = {"status": "skipped", "chunks": []}
        if auto_cbms:
            cbms_hits = _thinking_auto_cbms(thought)
        
        suggested = _suggest_aions_tools(thought)
        
        step_record = {
            "step": step_number,
            "thought": thought,
            "timestamp": _now_iso(),
            "branch": branch_id,
            "cbms_hits": cbms_hits.get("chunks", [])[:3],
            "suggested_tools": [s["tool"] for s in suggested],
            "needs_more": needs_more_steps
        }
        
        with _thinking_lock:
            session["branches"][branch_id].append(step_record)
            session["current_step"] = step_number
            session["steps"].append(step_record)
            session["active_branch"] = branch_id
        
        next_suggestions = []
        if needs_more_steps:
            if cbms_hits.get("chunks"):
                next_suggestions.append("Consider exploring CBMS chunks: " + ", ".join(cbms_hits["chunks"][:2]))
            if suggested:
                tools_str = ", ".join([s["tool"] for s in suggested[:3]])
                next_suggestions.append(f"Recommended tools: {tools_str}")
            next_suggestions.append(f"Continue with think_step(step_number={step_number + 1})")
        else:
            next_suggestions.append("Ready to conclude. Use think_finish() to summarize.")
        
        return _success({
            "session_id": session_id,
            "step": step_number,
            "branch": branch_id,
            "thought_preview": thought[:100] + "..." if len(thought) > 100 else thought,
            "cbms_context": {
                "status": cbms_hits.get("status"),
                "chunks_found": cbms_hits.get("chunks", [])[:3]
            },
            "suggested_tools": suggested[:3],
            "needs_more_steps": needs_more_steps,
            "next_suggestions": next_suggestions,
            "total_steps": len(session["steps"])
        })
        
    except Exception as e:
        log(f"think_step error: {e}")
        return _error(f"Step failed: {str(e)}")


@mcp_server.tool(name="think_branch", description="Create parallel reasoning branch for exploring alternative hypotheses.")
def think_branch(
    session_id: str,
    branch_name: str,
    hypothesis: str,
    parent_step: int = -1
) -> str:
    """
    Tworzy równoległą gałąź rozumowania.
    
    Args:
        session_id: ID sesji
        branch_name: Nazwa nowej gałęzi
        hypothesis: Hipoteza do eksploracji
        parent_step: Od którego kroku rozgałęzić (-1 = current)
    """
    try:
        with _thinking_lock:
            if session_id not in _thinking_sessions:
                return _error(f"Session '{session_id}' not found")
            
            session = _thinking_sessions[session_id]
            
            if branch_name in session["branches"]:
                return _error(f"Branch '{branch_name}' already exists")
            
            parent = parent_step if parent_step > 0 else session["current_step"]
            session["branches"][branch_name] = []
            
            branch_start = {
                "step": 0,
                "thought": f"BRANCH START: {hypothesis}",
                "timestamp": _now_iso(),
                "branch": branch_name,
                "parent_step": parent,
                "cbms_hits": [],
                "suggested_tools": [],
                "needs_more": True
            }
            session["branches"][branch_name].append(branch_start)
        
        return _success({
            "session_id": session_id,
            "branch_created": branch_name,
            "hypothesis": hypothesis,
            "forked_from_step": parent,
            "total_branches": len(session["branches"]),
            "branches": list(session["branches"].keys()),
            "message": f"Use think_step(branch_id='{branch_name}') to continue this branch"
        })
        
    except Exception as e:
        log(f"think_branch error: {e}")
        return _error(f"Branch failed: {str(e)}")


@mcp_server.tool(name="think_finish", description="Complete thinking chain, generate summary report, optionally store to ChromaDB memory.")
@auto_logged
def think_finish(
    session_id: str,
    conclusion: str,
    confidence: float = 0.8,
    store_to_memory: bool = True,
    memory_session: str = "thinking_conclusions"
) -> str:
    """
    Kończy łańcuch myślowy i generuje raport.
    
    Args:
        session_id: ID sesji
        conclusion: Końcowy wniosek
        confidence: Pewność wniosku (0.0 - 1.0)
        store_to_memory: Czy zapisać do ChromaDB
        memory_session: Nazwa sesji ChromaDB
    """
    try:
        with _thinking_lock:
            if session_id not in _thinking_sessions:
                return _error(f"Session '{session_id}' not found")
            
            session = _thinking_sessions[session_id]
            session["status"] = "completed"
            session["conclusion"] = conclusion
            session["confidence"] = confidence
            session["completed_at"] = _now_iso()
        
        report = {
            "session_id": session_id,
            "goal": session["goal"],
            "total_steps": len(session["steps"]),
            "branches_explored": len(session["branches"]),
            "duration": None,
            "conclusion": conclusion,
            "confidence": confidence,
            "thinking_chain": []
        }
        
        try:
            start = datetime.fromisoformat(session["created"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(session["completed_at"].replace("Z", "+00:00"))
            report["duration"] = str(end - start)
        except:
            report["duration"] = "unknown"
        
        for step in session["steps"]:
            report["thinking_chain"].append({
                "step": step["step"],
                "branch": step["branch"],
                "thought": step["thought"][:200] + "..." if len(step["thought"]) > 200 else step["thought"],
                "tools_suggested": step.get("suggested_tools", [])
            })
        
        memory_result = None
        if store_to_memory:
            try:
                memory_text = f"""THINKING SESSION: {session_id}
GOAL: {session['goal']}
CONCLUSION: {conclusion}
CONFIDENCE: {confidence}
STEPS: {len(session['steps'])}
BRANCHES: {', '.join(session['branches'].keys())}

THINKING CHAIN:
"""
                for i, step in enumerate(session["steps"], 1):
                    memory_text += f"\n{i}. [{step['branch']}] {step['thought'][:300]}"
                
                store_result = memory_store(
                    session_id=memory_session,
                    text=memory_text[:4000],
                    ttl_days=90
                )
                memory_result = json.loads(store_result)
            except Exception as e:
                memory_result = {"status": "error", "error": str(e)}
        
        return _success({
            "status": "completed",
            "report": report,
            "stored_to_memory": memory_result.get("status") == "ok" if memory_result else False,
            "memory_doc_id": memory_result.get("doc_id") if memory_result else None,
            "message": "Thinking session completed successfully."
        }, guard=False)
        
    except Exception as e:
        log(f"think_finish error: {e}")
        return _error(f"Finish failed: {str(e)}")


@mcp_server.tool(name="think_status", description="Get status of thinking sessions - active, completed, or specific session details.")
def think_status(
    session_id: str = "",
    include_history: bool = False
) -> str:
    """
    Zwraca status sesji thinking.
    
    Args:
        session_id: ID konkretnej sesji (puste = wszystkie)
        include_history: Czy włączyć pełną historię kroków
    """
    try:
        with _thinking_lock:
            if session_id:
                if session_id not in _thinking_sessions:
                    return _error(f"Session '{session_id}' not found")
                
                session = _thinking_sessions[session_id]
                result = {
                    "session_id": session_id,
                    "goal": session["goal"],
                    "status": session["status"],
                    "current_step": session["current_step"],
                    "max_steps": session["max_steps"],
                    "branches": list(session["branches"].keys()),
                    "active_branch": session["active_branch"],
                    "created": session["created"]
                }
                
                if include_history:
                    result["steps"] = session["steps"]
                    result["conclusion"] = session.get("conclusion")
                
                return _success(result)
            else:
                sessions_summary = []
                for sid, data in _thinking_sessions.items():
                    sessions_summary.append({
                        "session_id": sid,
                        "goal": data["goal"][:50] + "..." if len(data["goal"]) > 50 else data["goal"],
                        "status": data["status"],
                        "steps": len(data["steps"]),
                        "branches": len(data["branches"])
                    })
                
                return _success({
                    "active_sessions": len([s for s in _thinking_sessions.values() if s["status"] == "active"]),
                    "total_sessions": len(_thinking_sessions),
                    "sessions": sessions_summary
                })
                
    except Exception as e:
        log(f"think_status error: {e}")
        return _error(f"Status failed: {str(e)}")


# =============================================================================
# END OF SEQUENTIAL THINKING ENGINE
# =============================================================================


# =============================================================================
# AIONS MOUTH — Qwen via Ollama (translator / intent only; AIONS decides)
# =============================================================================
try:
    from . import llm_mouth
except ImportError:
    import llm_mouth  # type: ignore


@mcp_server.tool(
    name="llm_understand",
    description="Parse user text into intent JSON (lang, need, remember, summary) via local mouth (llamacpp/GGUF or Ollama). AIONS decides next tools.",
)
@auto_logged
def llm_understand(text: str) -> str:
    try:
        result = llm_mouth.understand(text)
        if not result.get("ok"):
            return _error(result.get("error", "llm_understand failed"))
        return _success({
            "intent": result["intent"],
            "model": result.get("model"),
            "host": result.get("host"),
            "backend": result.get("backend") or llm_mouth.mouth_backend(),
            "mode": result.get("mode"),
            "fallback_from": result.get("fallback_from"),
        })
    except Exception as e:
        return _error(str(e))


@mcp_server.tool(
    name="llm_speak",
    description="Short PL/EN reply from provided CONTEXT only via local mouth (llamacpp/GGUF or Ollama). Does not invent facts.",
)
@auto_logged
def llm_speak(context: str, user_lang: str = "pl") -> str:
    try:
        result = llm_mouth.speak(context, user_lang=user_lang or "pl")
        if not result.get("ok"):
            return _error(result.get("error", "llm_speak failed"))
        return _success({
            "reply": result["reply"],
            "user_lang": result.get("user_lang"),
            "model": result.get("model"),
            "host": result.get("host"),
            "backend": result.get("backend") or llm_mouth.mouth_backend(),
            "mode": result.get("mode"),
            "fallback_from": result.get("fallback_from"),
        })
    except Exception as e:
        return _error(str(e))


server = mcp_server

# =============================================================================
# EAGER PRELOAD - FIX COLD START!
# =============================================================================
def _warmup():
    """Preload heavy components to avoid cold start delays"""
    try:
        log("Warmup: loading ChromaDB...")
        vs = get_vector_store()
        if vs:
            log(f"Warmup: ChromaDB ready ({vs.sessions_count()} sessions)")
    except Exception as e:
        log(f"Warmup: ChromaDB failed: {e}")

    try:
        log("Warmup: loading CBMS...")
        cbms = get_cbms()
        if cbms:
            stats = cbms.get_memory_stats()
            log(f"Warmup: CBMS ready ({stats.get('total_chunks', 0)} chunks)")
    except Exception as e:
        log(f"Warmup: CBMS failed: {e}")

# Run warmup in background thread to not block server start
_warmup_thread = threading.Thread(target=_warmup, daemon=True)
_warmup_thread.start()

log("Server v8 DEBILOODPORNE + PRELOAD ready!")


# =============================================================================
# Faza 3 — Control Plane MCP tools
# =============================================================================
def _cp_tool_runner(tool: str, args: dict) -> str:
    """Execute whitelisted MCP tool from control plane executor."""
    mapping = {
        "system_health": lambda a: system_health(),
        "cbms_search": lambda a: cbms_search(a.get("query", "")),
        "memory_recall": lambda a: memory_recall(
            a.get("session_id", "claude_marcin_main"),
            a.get("query", ""),
            a.get("top_k", 3),
        ),
        "fast_search": lambda a: fast_search(a.get("query", "")),
    }
    fn = mapping.get(tool)
    if not fn:
        return _error(f"control plane cannot run tool: {tool}")
    return fn(args)


@mcp_server.tool(name="aions_plan", description="Create execution plan from user intent (Control Plane).")
def aions_plan(intent: str) -> str:
    try:
        # FIX (blind fallback): previously this always used control_plane.planner
        # .create_plan(), a 4-branch regex classifier that defaults to
        # system_health for anything it does not recognize -- completely
        # disconnected from the real skill registry. Now wired to the actual
        # skill-registry planner (control_plane/skills/goal_planner.py::plan_goal),
        # which does recipe replay / CBMS-cache / LLM-composed selection from the
        # live skills_lib registry with hallucination validation (every returned
        # skill id must exist in the registry).
        from control_plane.models import Plan, PlanStep, new_plan_id, new_step_id
        from control_plane.executor import store_plan
        from control_plane.skills.goal_planner import plan_goal
        from control_plane.skills.registry import SkillRegistry

        registry = SkillRegistry()
        registry.discover()
        result = plan_goal(intent, registry)

        if result.get("status") != "planned" or not result.get("steps"):
            # Honest failure: no capability found -> say so explicitly instead
            # of returning an unrelated generic action that looks like a plan.
            payload = {
                "plan_id": None,
                "intent": intent,
                "steps": [],
                "cbms_context": [],
                "status": "no_plan",
                "reason": result.get("reason") or result.get("status") or "planner_returned_no_steps",
                "source": result.get("source"),
                "why": result.get("why"),
            }
            return _guard(json.dumps(payload, indent=2, default=str))

        steps = []
        for s in result["steps"]:
            skill_id = s.get("skill")
            obj = registry.get(skill_id)
            desc = obj.description if obj is not None else skill_id
            steps.append(PlanStep(new_step_id(), desc, skill_id, s.get("inputs", {})))

        plan = store_plan(Plan(
            id=new_plan_id(),
            intent=intent,
            steps=steps,
            cbms_context=[result.get("cache", {})],
        ))
        payload = {
            "plan_id": plan.id,
            "intent": plan.intent,
            "steps": [
                {"id": s.id, "description": s.description, "tool": s.tool, "args": s.args}
                for s in plan.steps
            ],
            "cbms_context": plan.cbms_context,
            "status": "planned",
            "source": result.get("source"),
            "why": result.get("why"),
        }
        return _guard(json.dumps(payload, indent=2, default=str))
    except Exception as exc:
        return _error(f"aions_plan failed: {exc}")


@mcp_server.tool(name="aions_execute_step", description="Execute one step of a control plane plan.")
def aions_execute_step(plan_id: str, step_id: str) -> str:
    try:
        from control_plane.executor import execute_step

        result = execute_step(plan_id, step_id, _cp_tool_runner)
        payload = {
            "step_id": result.step_id,
            "status": result.status,
            "output": result.output,
            "error": result.error,
            "duration_ms": result.duration_ms,
        }
        return _guard(json.dumps(payload, indent=2, default=str))
    except Exception as exc:
        return _error(f"aions_execute_step failed: {exc}")


@mcp_server.tool(name="aions_execution_status", description="Get control plane execution status for a plan.")
def aions_execution_status(plan_id: str) -> str:
    try:
        from control_plane.executor import get_execution, get_plan

        state = get_execution(plan_id)
        plan = get_plan(plan_id)
        if not state or not plan:
            return _error(f"plan not found: {plan_id}")
        payload = {
            "plan_id": plan_id,
            "status": state.status,
            "current_step": state.current_step,
            "total_steps": len(plan.steps),
            "results": [
                {"step_id": r.step_id, "status": r.status, "error": r.error}
                for r in state.results
            ],
        }
        return _guard(json.dumps(payload, indent=2))
    except Exception as exc:
        return _error(f"aions_execution_status failed: {exc}")


@mcp_server.tool(name="skill_list", description="AIONS Skill Engine: list available skill/recipe blocks (plug-and-play from skills_lib/).")
def skill_list() -> str:
    try:
        from control_plane.skills import mcp_bridge
        return _success(mcp_bridge.list_skills())
    except Exception as exc:
        return _error(f"skill_list failed: {exc}")


@mcp_server.tool(name="skill_search", description="AIONS Skill Engine: find skill blocks matching an intent.")
def skill_search(query: str, top_k: int = 5) -> str:
    try:
        from control_plane.skills import mcp_bridge
        return _success(mcp_bridge.search_skills(query, top_k))
    except Exception as exc:
        return _error(f"skill_search failed: {exc}")


@mcp_server.tool(name="skill_run", description="AIONS Skill Engine: run one skill block by id with JSON inputs, e.g. inputs_json='{\"name\":\"notepad.exe\"}'.")
def skill_run(skill_id: str, inputs_json: str = "{}") -> str:
    try:
        import json as _json
        from control_plane.skills import mcp_bridge
        inputs = _json.loads(inputs_json or "{}")
        return _success(mcp_bridge.run_skill(skill_id, inputs))
    except Exception as exc:
        return _error(f"skill_run failed: {exc}")


@mcp_server.tool(name="task_run", description="AIONS Skill Engine: run a task by intent. Replays a learned recipe if present, else returns candidate skills to compose.")
def task_run(intent: str) -> str:
    try:
        from control_plane.skills import mcp_bridge
        return _success(mcp_bridge.run_task(intent))
    except Exception as exc:
        return _error(f"task_run failed: {exc}")


@mcp_server.tool(name="recipe_list", description="AIONS Skill Engine: list learned success recipes.")
def recipe_list() -> str:
    try:
        from control_plane.skills import mcp_bridge
        return _success(mcp_bridge.list_recipes())
    except Exception as exc:
        return _error(f"recipe_list failed: {exc}")


@mcp_server.tool(name="forge_request", description="AIONS forge: file a request for a NEW skill block that AIONS lacks (queued for the big model to build).")
def forge_request(name: str, description: str = "", why: str = "") -> str:
    try:
        from control_plane.skills import forge
        return _success(forge.request_skill(name, description, why=why, requested_by="mcp"))
    except Exception as exc:
        return _error(f"forge_request failed: {exc}")


@mcp_server.tool(name="forge_list", description="AIONS forge: list pending skill requests waiting to be built.")
def forge_list() -> str:
    try:
        from control_plane.skills import forge
        return _success({"pending": forge.list_requests("requested")})
    except Exception as exc:
        return _error(f"forge_list failed: {exc}")


@mcp_server.tool(name="forge_promote", description="AIONS forge: verify a built block (skills_requests/built/<name>) and promote it into skills_lib. Verify-before-trust.")
def forge_promote(name: str) -> str:
    try:
        from control_plane.skills import forge
        return _success(forge.promote(name))
    except Exception as exc:
        return _error(f"forge_promote failed: {exc}")


@mcp_server.tool(name="offload_get", description="Retrieve full content from offloaded response by ref_id (OFF_xxx).")
def offload_get(ref_id: str) -> str:
    if ref_id in _offload_cache:
        return _offload_cache[ref_id]  # Return raw, no re-guard
    return _error(f"Offload '{ref_id}' not found or expired")

if __name__ == "__main__":
    mcp_server.run(transport="stdio")


