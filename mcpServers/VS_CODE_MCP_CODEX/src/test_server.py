"""
AIONS MCP Server - Minimal Test Version
========================================
Najprostsza wersja do testowania czy MCP działa.
"""

import json
import sys
from datetime import datetime, timezone

print("[TEST] Server loading...", file=sys.stderr, flush=True)

try:
    from mcp.server.fastmcp import FastMCP
    print("[TEST] FastMCP imported OK", file=sys.stderr, flush=True)
except Exception as e:
    print(f"[TEST] FastMCP import FAILED: {e}", file=sys.stderr, flush=True)
    raise

# Create server
server = FastMCP("aions_test_server")
print("[TEST] Server created", file=sys.stderr, flush=True)

def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

@server.tool(name="ping", description="Test tool - returns pong")
def ping() -> str:
    print("[TEST] ping called", file=sys.stderr, flush=True)
    return json.dumps({"status": "pong", "timestamp": _now()})

@server.tool(name="echo", description="Echo back the message")
def echo(message: str) -> str:
    print(f"[TEST] echo called: {message}", file=sys.stderr, flush=True)
    return json.dumps({"echo": message, "timestamp": _now()})

@server.tool(name="health", description="Health check")
def health() -> str:
    print("[TEST] health called", file=sys.stderr, flush=True)
    return json.dumps({
        "status": "healthy",
        "server": "aions_test_server",
        "timestamp": _now(),
        "python": sys.version,
    })

print("[TEST] Tools registered, ready", file=sys.stderr, flush=True)

if __name__ == "__main__":
    print("[TEST] Running server...", file=sys.stderr, flush=True)
    server.run(transport="stdio")
