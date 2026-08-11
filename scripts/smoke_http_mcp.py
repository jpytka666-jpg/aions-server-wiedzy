"""Smoke test: prove the AIONS MCP streamable-http endpoint answers a real handshake.

Usage:
    python scripts/smoke_http_mcp.py [base_url]
Default base_url comes from AIONS_SMOKE_URL, else http://127.0.0.1:8787/mcp
Exit 0 = initialize + tools/list both succeeded.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request

DEFAULT_URL = os.environ.get("AIONS_SMOKE_URL", "http://127.0.0.1:8787/mcp")
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


def post(url: str, payload: dict, session: str | None = None):
    headers = dict(HEADERS)
    if session:
        headers["mcp-session-id"] = session
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.headers.get("mcp-session-id"), resp.read().decode("utf-8", "replace")


def parse_sse(body: str) -> dict:
    for line in body.splitlines():
        if line.startswith("data:"):
            return json.loads(line[5:].strip())
    return json.loads(body)


def main() -> int:
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    print(f"target: {url}")

    sid, body = post(
        url,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "aions-smoke", "version": "1.0"},
            },
        },
    )
    init = parse_sse(body)
    server_name = init["result"]["serverInfo"]["name"]
    print(f"initialize OK -> serverInfo.name={server_name} session={sid}")

    post(url, {"jsonrpc": "2.0", "method": "notifications/initialized"}, session=sid)

    _, body = post(url, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, session=sid)
    tools = parse_sse(body)["result"]["tools"]
    names = sorted(t["name"] for t in tools)
    print(f"tools/list OK -> {len(names)} tools")
    print("sample:", ", ".join(names[:8]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
