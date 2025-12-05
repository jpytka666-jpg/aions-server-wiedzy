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
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

# =============================================================================
# STDERR LOGGING
# =============================================================================

def log(msg: str):
    print(f"[AIONS] {datetime.now().isoformat()} - {msg}", file=sys.stderr, flush=True)

log("Server v6 loading (DEBILOODPORNE)...")

# =============================================================================
# PATH SETUP
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parents[3]
AIONS_V10 = Path("E:/AIONS_V10/AIONS_CBMS_RELEASE_V3")
DUMPS_DIR = REPO_ROOT / "logs" / "conversation_dumps"
SCAN_RESULTS_DIR = REPO_ROOT / "scan_results"
SCANNER_SCRIPT = REPO_ROOT / "scripts" / "project_scanner.py"
TURBO_SCANNER_SCRIPT = REPO_ROOT / "scripts" / "turbo_scanner.py"
PYTHON_EXE = REPO_ROOT / "venv" / "Scripts" / "python.exe"

EVERYTHING_CLI = Path("C:/Program Files/Everything/es.exe")
DOCKER_EXE = shutil.which("docker") or "docker"
WSL_EXE = shutil.which("wsl") or "wsl"
# Git - use full path to avoid issues
GIT_EXE = Path("C:/Program Files/Git/bin/git.exe")
if not GIT_EXE.exists():
    GIT_EXE = shutil.which("git") or "git"
else:
    GIT_EXE = str(GIT_EXE)
GH_EXE = shutil.which("gh") or "gh"
NMAP_EXE = Path("C:/Program Files (x86)/Nmap/nmap.exe")

DUMPS_DIR.mkdir(parents=True, exist_ok=True)
SCAN_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

server_pkg_path = REPO_ROOT / "server"

for p in [AIONS_V10, AIONS_V10 / "server"]:
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

def _success(payload: Dict[str, Any]) -> str:
    return json.dumps({"status": "ok", "timestamp": _now_iso(), **payload}, ensure_ascii=False)

def _error(message: str) -> str:
    return json.dumps({"status": "error", "message": message, "timestamp": _now_iso()}, ensure_ascii=False)

def _generate_id() -> str:
    return str(uuid.uuid4())[:12]

def _run_command(cmd: List[str], timeout: int = 30) -> Dict[str, Any]:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=False)
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

# Tools to SKIP logging (to avoid infinite loops)
SKIP_LOG_TOOLS = {"conv_log", "conv_dump", "conv_status", "conv_set_threshold", "conv_history"}

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
            metadata = {
                "type": "auto_log",
                "entry_count": len(_auto_log_buffer),
                "tools_used": ",".join(set(e["tool"] for e in _auto_log_buffer)),
                "timestamp": _now_iso()
            }
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
                        preview = parsed.get("status", "") + ": " + str(list(parsed.keys()))[:100]
                    except:
                        preview = result[:100]
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

def get_vector_store():
    global _vector_store
    if _vector_store is None:
        try:
            context_schema_path = server_pkg_path / "context_schema.py"
            store_path = server_pkg_path / "store.py"
            
            if not context_schema_path.exists() or not store_path.exists():
                raise FileNotFoundError("Store files not found")
            
            spec_cs = importlib.util.spec_from_file_location("aions_context_schema", context_schema_path)
            context_schema_module = importlib.util.module_from_spec(spec_cs)
            sys.modules["aions_context_schema"] = context_schema_module
            spec_cs.loader.exec_module(context_schema_module)
            
            sys.modules["server"] = type(sys)("server")
            sys.modules["server"].__path__ = [str(server_pkg_path)]
            sys.modules["server.context_schema"] = context_schema_module
            
            spec_store = importlib.util.spec_from_file_location("server.store", store_path, submodule_search_locations=[str(server_pkg_path)])
            store_module = importlib.util.module_from_spec(spec_store)
            sys.modules["server.store"] = store_module
            spec_store.loader.exec_module(store_module)
            
            VectorStore = store_module.VectorStore
            _vector_store = VectorStore(persist_path=os.environ.get("CHROMA_PATH"))
            log(f"VectorStore loaded")
        except Exception as e:
            log(f"VectorStore failed: {e}")
            _vector_store = "FAILED"
    return _vector_store if _vector_store != "FAILED" else None

def get_cbms():
    global _cbms_memory
    if _cbms_memory is None:
        try:
            from cbms_memory import CBMSMemory
            cbms_dir = AIONS_V10 / "memory" if AIONS_V10.exists() else None
            _cbms_memory = CBMSMemory(memory_dir=str(cbms_dir) if cbms_dir else None)
            log(f"CBMS loaded")
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

# =============================================================================
# EVERYTHING SEARCH TOOLS (AUTO-LOGGED)
# =============================================================================

@mcp_server.tool(name="fast_search", description="Blazing fast file search using Everything.")
@auto_logged
def fast_search(query: str, max_results: int = 50) -> str:
    try:
        if not EVERYTHING_CLI.exists():
            return _error("Everything CLI not found")
        cmd = [str(EVERYTHING_CLI), "-n", str(max_results), query]
        result = _run_command(cmd, timeout=10)
        if result["success"]:
            files = [f for f in result["stdout"].strip().split("\n") if f]
            return _success({"query": query, "files": files[:max_results], "count": len(files)})
        return _error(result.get("error", "Search failed"))
    except Exception as e:
        return _error(str(e))

@mcp_server.tool(name="fast_search_ext", description="Search files by extension.")
@auto_logged
def fast_search_ext(extension: str, folder: str = "", max_results: int = 100) -> str:
    try:
        if not EVERYTHING_CLI.exists():
            return _error("Everything CLI not found")
        query = f"ext:{extension.lstrip('.')}"
        if folder:
            query = f'"{folder}" {query}'
        cmd = [str(EVERYTHING_CLI), "-n", str(max_results), query]
        result = _run_command(cmd, timeout=15)
        if result["success"]:
            files = [f for f in result["stdout"].strip().split("\n") if f]
            return _success({"extension": extension, "files": files, "count": len(files)})
        return _error("Search failed")
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
        if cwd and not Path(cwd).exists():
            return _error(f"Path not found: {cwd}")
        
        result = subprocess.run(
            [git_cmd, "status", "--porcelain", "-b"], 
            capture_output=True, 
            text=True, 
            cwd=cwd, 
            timeout=10,
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

@mcp_server.tool(name="project_scan_turbo", description="TURBO SCAN using Everything - FAST!")
@auto_logged
def project_scan_turbo(output_dir: str = "") -> str:
    global _scan_status
    try:
        if _scan_status.get("state") == "running":
            return _error("Scan already running")
        if not EVERYTHING_CLI.exists():
            return _error("Everything CLI not found")
        
        out_dir = output_dir or str(SCAN_RESULTS_DIR)
        scan_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        _scan_status = {"state": "starting", "scan_id": scan_id, "type": "turbo"}
        
        def run_turbo():
            global _scan_status
            try:
                _scan_status["state"] = "running"
                cmd = [str(PYTHON_EXE), str(TURBO_SCANNER_SCRIPT), "-o", out_dir]
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=600)
                _scan_status["state"] = "completed" if result.returncode == 0 else "error"
                if result.returncode != 0:
                    _scan_status["error"] = result.stderr[:500]
            except Exception as e:
                _scan_status["state"] = "error"
                _scan_status["error"] = str(e)
        
        threading.Thread(target=run_turbo, daemon=True).start()
        return _success({"message": "TURBO scan started!", "scan_id": scan_id})
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

@mcp_server.tool(name="conv_history", description="Get log history.")
def conv_history(date: str = "") -> str:
    try:
        target = date or _today_str()
        dump_file = DUMPS_DIR / f"autolog_{target}.jsonl"
        if not dump_file.exists():
            return _success({"date": target, "entries": [], "count": 0})
        entries = []
        with open(dump_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
        return _success({"date": target, "entries": entries[-30:], "count": len(entries)})
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
        metadata = {"categories": ",".join(categories), "timestamp": _now_iso()}
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
                for cid in cbms.cbms_think(query).get("chunk_references", [])[:3]:
                    chunk = cbms.retrieve_chunk(cid)
                    if chunk:
                        results.append({"id": f"cbms:{cid}", "text": chunk.get("content", "")[:300], "score": 0.5, "source": "cbms"})
            except:
                pass
        results.sort(key=lambda x: x["score"], reverse=True)
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

# =============================================================================
# SYSTEM HEALTH (AUTO-LOGGED)
# =============================================================================

@mcp_server.tool(name="system_health", description="System health check.")
@auto_logged
def system_health() -> str:
    try:
        health = {
            "server": "v6 DEBILOODPORNE",
            "auto_log_buffer": len(_auto_log_buffer),
            "auto_log_threshold": _auto_log_threshold,
            "scan_status": _scan_status.get("state", "idle"),
            "everything": "ok" if EVERYTHING_CLI.exists() else "missing",
            "docker": "ok" if shutil.which("docker") else "missing",
            "wsl": "ok" if shutil.which("wsl") else "missing",
            "git": "ok" if shutil.which("git") else "missing",
        }
        vs = get_vector_store()
        health["chromadb"] = f"{vs.sessions_count()} sessions" if vs else "failed"
        cbms = get_cbms()
        health["cbms"] = f"{cbms.get_memory_stats().get('total_chunks', 0)} chunks" if cbms else "failed"
        return _success(health)
    except Exception as e:
        return _error(str(e))

# =============================================================================
# PLAYWRIGHT BROWSER TOOLS (AUTO-LOGGED)
# =============================================================================

_browser = None
_browser_context = None
_page = None
_page_snapshot = None

def get_browser():
    """Lazy-load Playwright browser"""
    global _browser, _browser_context, _page
    if _browser is None:
        try:
            from playwright.sync_api import sync_playwright
            pw = sync_playwright().start()
            _browser = pw.chromium.launch(headless=True)
            _browser_context = _browser.new_context(viewport={"width": 1280, "height": 720})
            _page = _browser_context.new_page()
            log("Playwright browser launched")
        except Exception as e:
            log(f"Playwright failed: {e}")
            return None, None
    return _browser, _page

@mcp_server.tool(name="browser_navigate", description="Navigate to URL in browser.")
@auto_logged
def browser_navigate(url: str) -> str:
    try:
        _, page = get_browser()
        if not page:
            return _error("Browser not available")
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        return _success({"url": page.url, "title": page.title()})
    except Exception as e:
        return _error(str(e))

@mcp_server.tool(name="browser_snapshot", description="Get accessibility snapshot of current page.")
@auto_logged
def browser_snapshot() -> str:
    global _page_snapshot
    try:
        _, page = get_browser()
        if not page:
            return _error("Browser not available")
        # Get accessibility tree
        snapshot = page.accessibility.snapshot()
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
        return _success({"url": page.url, "title": page.title(), "elements": elements[:100]})
    except Exception as e:
        return _error(str(e))

@mcp_server.tool(name="browser_click", description="Click element by text or selector.")
@auto_logged
def browser_click(selector: str = "", text: str = "") -> str:
    try:
        _, page = get_browser()
        if not page:
            return _error("Browser not available")
        if text:
            page.get_by_text(text, exact=False).first.click(timeout=5000)
        elif selector:
            page.click(selector, timeout=5000)
        else:
            return _error("Provide selector or text")
        page.wait_for_load_state("domcontentloaded", timeout=5000)
        return _success({"clicked": text or selector, "url": page.url})
    except Exception as e:
        return _error(str(e))

@mcp_server.tool(name="browser_type", description="Type text into input field.")
@auto_logged
def browser_type(selector: str = "", text: str = "", placeholder: str = "", submit: bool = False) -> str:
    try:
        _, page = get_browser()
        if not page:
            return _error("Browser not available")
        if placeholder:
            elem = page.get_by_placeholder(placeholder, exact=False).first
        elif selector:
            elem = page.locator(selector).first
        else:
            return _error("Provide selector or placeholder")
        elem.fill(text)
        if submit:
            elem.press("Enter")
            page.wait_for_load_state("domcontentloaded", timeout=5000)
        return _success({"typed": text[:50], "submitted": submit})
    except Exception as e:
        return _error(str(e))

@mcp_server.tool(name="browser_screenshot", description="Take screenshot of current page.")
@auto_logged
def browser_screenshot(filename: str = "", full_page: bool = False) -> str:
    try:
        _, page = get_browser()
        if not page:
            return _error("Browser not available")
        fname = filename or f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        fpath = DUMPS_DIR / fname
        page.screenshot(path=str(fpath), full_page=full_page)
        return _success({"file": str(fpath), "url": page.url})
    except Exception as e:
        return _error(str(e))

@mcp_server.tool(name="browser_get_text", description="Get text content from page or element.")
@auto_logged
def browser_get_text(selector: str = "") -> str:
    try:
        _, page = get_browser()
        if not page:
            return _error("Browser not available")
        if selector:
            text = page.locator(selector).first.inner_text(timeout=5000)
        else:
            text = page.inner_text("body")
        return _success({"text": text[:5000], "length": len(text)})
    except Exception as e:
        return _error(str(e))

@mcp_server.tool(name="browser_close", description="Close browser.")
@auto_logged
def browser_close() -> str:
    global _browser, _browser_context, _page
    try:
        if _page:
            _page.close()
        if _browser_context:
            _browser_context.close()
        if _browser:
            _browser.close()
        _browser = None
        _browser_context = None
        _page = None
        return _success({"closed": True})
    except Exception as e:
        return _error(str(e))

@mcp_server.tool(name="browser_evaluate", description="Execute JavaScript on page.")
@auto_logged
def browser_evaluate(script: str) -> str:
    try:
        _, page = get_browser()
        if not page:
            return _error("Browser not available")
        result = page.evaluate(script)
        return _success({"result": str(result)[:2000]})
    except Exception as e:
        return _error(str(e))

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
    "aions-context": {"description": "THIS SERVER - ChromaDB + CBMS + Everything", "url": "built-in"},
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

server = mcp_server
log("Server v7 DEBILOODPORNE + PLAYWRIGHT + MCP CATALOG ready!")

if __name__ == "__main__":
    mcp_server.run(transport="stdio")
