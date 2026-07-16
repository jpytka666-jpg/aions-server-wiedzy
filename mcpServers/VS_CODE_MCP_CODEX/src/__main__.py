"""
AIONS Context MCP Server - Entry Point
PATCHED for Windows stdio buffering issues
"""

import sys
import os
from pathlib import Path


def _expected_venv_roots() -> list[Path]:
    repo_root = Path(__file__).resolve().parents[3]
    roots = [repo_root / "venv", repo_root.parent.parent / "venv"]
    for env_key in ("AIONS_VENV_LINUX", "AIONS_VENV_WIN"):
        venv_base = os.environ.get(env_key)
        if venv_base:
            roots.append(Path(venv_base))
    return roots


def _in_project_venv() -> bool:
    """Accept prod Windows venv, Linux bin, and AIONS_DEV sibling venv layout."""
    prefix = Path(sys.prefix)
    for root in _expected_venv_roots():
        try:
            if prefix.resolve() == root.resolve():
                return True
        except OSError:
            continue

    # Fallback when prefix check is inconclusive (direct python.exe path on Windows).
    exe = Path(sys.executable)
    for root in _expected_venv_roots():
        for sub in ("Scripts", "bin"):
            marker = root / sub
            try:
                resolved_marker = marker.resolve()
                if resolved_marker.exists() and resolved_marker in exe.resolve().parents:
                    return True
            except OSError:
                continue

    return False


if not _in_project_venv():
    print(
        f"[AIONS] Refusing to start outside venv (got {sys.executable})",
        file=sys.stderr,
        flush=True,
    )
    sys.exit(1)

# WINDOWS FIX: Prevent binary mode issues
if sys.platform == "win32":
    # Don't use binary mode - it breaks JSON-RPC
    pass

# Ensure src package is importable
parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent not in sys.path:
    sys.path.insert(0, parent)


def main():
    from src.server import mcp_server, log
    import anyio

    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    log(f"Starting with transport: {transport} (PATCHED)")

    if transport == "stdio":
        if sys.platform == "win32":
            from src.patched_stdio import patched_stdio_server

            async def run_stdio():
                async with patched_stdio_server() as (read_stream, write_stream):
                    await mcp_server._mcp_server.run(
                        read_stream,
                        write_stream,
                        mcp_server._mcp_server.create_initialization_options(),
                    )
        else:
            from mcp.server.stdio import stdio_server

            async def run_stdio():
                async with stdio_server() as (read_stream, write_stream):
                    await mcp_server._mcp_server.run(
                        read_stream,
                        write_stream,
                        mcp_server._mcp_server.create_initialization_options(),
                    )

        anyio.run(run_stdio)
    else:
        print(f"Unsupported transport: {transport}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
