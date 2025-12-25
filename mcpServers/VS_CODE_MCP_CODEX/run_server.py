#!/usr/bin/env python
"""
MCP Server wrapper for Claude Code
Fixes cwd issue where Claude Code ignores the cwd config parameter on Windows
"""
import os
import sys

# Change to the correct directory for module imports
os.chdir("E:/server wiedzy/mcpServers/VS_CODE_MCP_CODEX")

# Run the MCP server
from src.server import mcp_server
mcp_server.run(transport="stdio")
