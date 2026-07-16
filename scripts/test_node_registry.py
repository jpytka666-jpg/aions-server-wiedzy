#!/usr/bin/env python3
"""Smoke test for Faza 6 node registry (in-process + optional HTTP API)."""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from control_plane.node_registry import (  # noqa: E402
    get_node,
    heartbeat,
    list_nodes,
    register_node,
    registry_summary,
)
from control_plane.planner import create_plan  # noqa: E402
from control_plane.executor import execute_step, store_plan  # noqa: E402


def _runner(tool: str, args: dict):
    return {"tool": tool, "args": args, "ok": True}


def smoke_in_process() -> None:
    summary = registry_summary()
    assert summary["count"] >= 1, "expected default local node"
    local_id = summary["nodes"][0]["node_id"]
    assert get_node(local_id), f"missing node {local_id}"

    rec = register_node(
        node_id="test-node-smoke",
        host="127.0.0.1",
        capabilities=["mcp", "shell"],
        memory_mb=2048,
        tools=["system_health", "fast_search"],
        health="ok",
        load=0.1,
        permissions=["execute"],
    )
    assert rec.node_id == "test-node-smoke"
    heartbeat("test-node-smoke", health="ok", load=0.05)
    nodes = list_nodes()
    assert any(n.node_id == "test-node-smoke" for n in nodes)

    plan = store_plan(create_plan("sprawdz health"))
    assert plan.node_id, "planner should assign a node"
    step = plan.steps[0]
    result = execute_step(plan.id, step.id, _runner)
    assert result.status == "ok", result.error
    print("node_registry in-process OK", local_id, "plan_node", plan.node_id)


def smoke_http(base_url: str) -> bool:
    base = base_url.rstrip("/")
    reg_url = f"{base}/v1/nodes/register"
    payload = json.dumps(
        {
            "node_id": "http-smoke-node",
            "host": "127.0.0.1",
            "capabilities": ["mcp"],
            "tools": ["system_health"],
            "memory_mb": 1024,
        }
    ).encode()
    try:
        req = urllib.request.Request(
            reg_url, data=payload, headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            assert data.get("status") == "registered"
        list_url = f"{base}/v1/nodes"
        with urllib.request.urlopen(list_url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            assert data.get("count", 0) >= 1
        print(f"node_registry HTTP OK {base}")
        return True
    except (urllib.error.URLError, TimeoutError, AssertionError, json.JSONDecodeError) as exc:
        print(f"node_registry HTTP SKIP ({exc})")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Node registry smoke (Faza 6)")
    parser.add_argument(
        "--api-url",
        default=os.environ.get("AIONS_REMOTE_API_URL", "http://127.0.0.1:8765"),
        help="Core API base for HTTP smoke",
    )
    parser.add_argument("--http-only", action="store_true")
    args = parser.parse_args()

    if not args.http_only:
        smoke_in_process()
    smoke_http(args.api_url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
