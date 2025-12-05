"""
AIONS Context MCP Server - Entry Point
PATCHED for Windows stdio buffering issues
"""

import sys
import os

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
        # Use patched stdio with Windows buffering fix
        from src.patched_stdio import patched_stdio_server
        
        async def run_patched():
            async with patched_stdio_server() as (read_stream, write_stream):
                await mcp_server._mcp_server.run(
                    read_stream,
                    write_stream,
                    mcp_server._mcp_server.create_initialization_options(),
                )
        
        anyio.run(run_patched)
    else:
        print(f"Unsupported transport: {transport}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
