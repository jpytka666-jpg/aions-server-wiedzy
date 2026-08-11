"""Proof: every memory write carries provenance (agent/host/surface/run_id).

Writes one record through the live MCP HTTP endpoint, then reads the metadata
straight back out of ChromaDB. Exit 0 only if all provenance keys are present.

Usage:
    python scripts/proof_provenance.py [mcp_url]
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

MCP_URL = os.environ.get("AIONS_SMOKE_URL", "http://127.0.0.1:8787/mcp")
SESSION = "provenance_proof"
REQUIRED = ("agent", "host", "surface", "run_id", "os", "era")
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


def post(url, payload, session=None):
    headers = dict(HEADERS)
    if session:
        headers["mcp-session-id"] = session
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.headers.get("mcp-session-id"), resp.read().decode("utf-8", "replace")


def parse_sse(body):
    for line in body.splitlines():
        if line.startswith("data:"):
            return json.loads(line[5:].strip())
    return json.loads(body)


def main() -> int:
    url = sys.argv[1] if len(sys.argv) > 1 else MCP_URL
    stamp = datetime.now(timezone.utc).isoformat()
    print(f"target: {url}")

    sid, body = post(url, {
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                   "clientInfo": {"name": "provenance-proof", "version": "1"}},
    })
    parse_sse(body)
    post(url, {"jsonrpc": "2.0", "method": "notifications/initialized"}, session=sid)

    _, body = post(url, {
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": "memory_store", "arguments": {
            "session_id": SESSION,
            "text": f"provenance proof write at {stamp}",
            "ttl_days": 1,
        }},
    }, session=sid)
    print("memory_store ->", parse_sse(body)["result"]["content"][0]["text"][:160])

    import chromadb

    client = chromadb.HttpClient(host="127.0.0.1", port=8000)
    coll = client.get_collection(f"session_{SESSION}")
    data = coll.get(include=["metadatas"])
    metas = data.get("metadatas") or []
    if not metas:
        print("FAIL: no records in collection")
        return 1

    latest = metas[-1]
    print("metadata:", json.dumps(latest, ensure_ascii=False, indent=2, sort_keys=True))

    missing = [k for k in REQUIRED if not latest.get(k)]
    if missing:
        print(f"FAIL: missing provenance keys: {missing}")
        return 1

    print(f"OK: all provenance keys present ({len(metas)} records in session)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
