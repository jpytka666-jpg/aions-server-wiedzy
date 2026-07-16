"""Minimal cross-host step dispatch (Faza 6 stub).

Path: executor.execute_step → dispatch_step_to_node(node_id, tool, args)
  - local node  → in-process tool_runner (MCP / API smoke)
  - remote node → returns stub with target URL (live agent on guest TBD)

Future: POST http://{node.host}:8765/v1/dispatch with signed step payload.
"""

from __future__ import annotations

from typing import Any, Callable

from .node_registry import NodeRecord, get_node

LOCAL_NODE_IDS = frozenset({"windows-primary", "linux-primary"})
_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def is_local_node(node: NodeRecord) -> bool:
    if node.node_id in LOCAL_NODE_IDS:
        return True
    host = (node.host or "").lower()
    return host in _LOCAL_HOSTS or host.startswith("127.")


def remote_dispatch_url(node: NodeRecord) -> str:
    return f"http://{node.host}:8765/v1/dispatch"


def dispatch_step_to_node(
    node_id: str,
    tool: str,
    args: dict[str, Any] | None = None,
    *,
    local_runner: Callable[[str, dict[str, Any]], Any] | None = None,
) -> dict[str, Any]:
    """Send one tool step to node_id. Local nodes run in-process; remote returns stub."""
    node = get_node(node_id)
    if not node:
        raise KeyError(f"unknown node: {node_id}")

    payload_args = args or {}

    if is_local_node(node):
        if local_runner is None:
            return {
                "mode": "local",
                "status": "no_runner",
                "node_id": node_id,
                "tool": tool,
            }
        output = local_runner(tool, payload_args)
        return {
            "mode": "local",
            "status": "ok",
            "node_id": node_id,
            "tool": tool,
            "output": output,
        }

    return {
        "mode": "remote",
        "status": "stub",
        "node_id": node_id,
        "host": node.host,
        "target_url": remote_dispatch_url(node),
        "tool": tool,
        "args": payload_args,
        "message": "Cross-host dispatch not live; enroll node agent on guest first",
    }
