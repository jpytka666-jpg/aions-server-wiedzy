import sys
import os

sys.path.insert(0, r"E:\server wiedzy")
sys.path.insert(0, r"E:\server wiedzy\server")
sys.path.insert(0, r"E:\server wiedzy\mcpServers\VS_CODE_MCP_CODEX")
os.chdir(r"E:\server wiedzy")

print("=" * 60)
print("AIONS MCP SERVER - FULL DIAGNOSTIC")
print("=" * 60)

# Test FastMCP server
from src.server import mcp_server

print(f"\n📦 MCP Server type: {type(mcp_server)}")
print(f"   Name: {mcp_server.name if hasattr(mcp_server, 'name') else 'N/A'}")

# Get tools via FastMCP internals
if hasattr(mcp_server, '_mcp_server'):
    internal = mcp_server._mcp_server
    print(f"\n🔧 Internal server: {type(internal)}")
    
    # Try to get tool info
    if hasattr(internal, '_tool_manager'):
        tm = internal._tool_manager
        if hasattr(tm, '_tools'):
            tools = list(tm._tools.keys())
            print(f"\n✅ TOOLS FOUND: {len(tools)}")
            for i, t in enumerate(sorted(tools), 1):
                print(f"   {i:2}. {t}")

# Direct check of registered decorators
print("\n" + "=" * 60)
print("CHECKING src/server.py FOR @mcp_server.tool DECORATORS...")
print("=" * 60)

import re
with open(r"E:\server wiedzy\mcpServers\VS_CODE_MCP_CODEX\src\server.py", "r", encoding="utf-8") as f:
    content = f.read()
    
tools = re.findall(r'@mcp_server\.tool\(\)\s*\nasync def (\w+)', content)
print(f"\n✅ Found {len(tools)} tools in source:")
for i, t in enumerate(tools, 1):
    print(f"   {i:2}. {t}")
