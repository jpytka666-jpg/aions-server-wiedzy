"""Quick validation of AIONS MCP tool functions (run after server.py changes)."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MCP = os.path.join(ROOT, "mcpServers", "VS_CODE_MCP_CODEX")
sys.path.insert(0, MCP)
os.environ.setdefault("CHROMA_PATH", os.path.join(ROOT, "data", "chroma"))

from src.server import (  # noqa: E402
    fast_search,
    fast_search_ext,
    system_health,
    cbms_search,
    memory_recall,
    git_status,
    wsl_list,
    docker_ps,
    project_scan_status,
    conv_status,
    mcp_list,
    think_status,
    _build_everything_ext_query,
)

def ok(name, raw):
    data = json.loads(raw) if isinstance(raw, str) else raw
    status = data.get("status") == "ok" or data.get("status") == "completed"
    print(f"{'OK' if status else 'FAIL':4} {name}: {str(data)[:120]}")
    return status

def main():
    print("QUERY BUILD:", _build_everything_ext_query("py", r"E:\server wiedzy"))
    tests = [
        ("fast_search_ext(spaced path)", fast_search_ext("py", folder=r"E:\server wiedzy", max_results=5)),
        ("fast_search_ext(scripts)", fast_search_ext("py", folder=r"E:\server wiedzy\scripts", max_results=5)),
        ("fast_search+folder", fast_search("turbo_scanner", folder=r"E:\server wiedzy", max_results=3)),
        ("system_health", system_health()),
        ("cbms_search", cbms_search("AIONS")),
        ("memory_recall", memory_recall("claude_marcin_main", "bootstrap", 2)),
        ("git_status", git_status(r"E:\server wiedzy")),
        ("wsl_list", wsl_list()),
        ("docker_ps", docker_ps()),
        ("project_scan_status", project_scan_status()),
        ("conv_status", conv_status()),
        ("mcp_list", mcp_list()),
        ("think_status", think_status()),
    ]
    passed = sum(ok(n, r) for n, r in tests)
    print(f"\n{passed}/{len(tests)} passed")
    return 0 if passed == len(tests) else 1

if __name__ == "__main__":
    raise SystemExit(main())
