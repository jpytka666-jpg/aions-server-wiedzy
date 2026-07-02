#!/usr/bin/env bash
# systemd launcher for AIONS MCP — paths without spaces (AIONS_REPO via symlink).
set -euo pipefail

AIONS_REPO="${AIONS_REPO:-/mnt/e/aions-repo}"
AIONS_LOG_DIR="${AIONS_LOG_DIR:-${HOME}/aions/logs}"
MCP_DIR="${AIONS_REPO}/mcpServers/VS_CODE_MCP_CODEX"
AIONS_PY="${AIONS_REPO}/scripts/aions_python.sh"

mkdir -p "${AIONS_LOG_DIR}"

export PYTHONPATH="${AIONS_REPO}:${AIONS_REPO}/server:${AIONS_REPO}/mcpServers/VS_CODE_MCP_CODEX"
export CHROMA_PATH="${CHROMA_PATH:-${AIONS_REPO}/data/chroma}"
export AIONS_PATH="${AIONS_PATH:-/mnt/d/AIONS-INTEGRATION/aions_core}"
export AIONS_DEPLOYMENT_PROFILE="${AIONS_DEPLOYMENT_PROFILE:-wsl-dev}"
export AIONS_SEARCH_ROOTS="${AIONS_SEARCH_ROOTS:-${AIONS_REPO}}"
export AIONS_VECTOR_BACKEND="${AIONS_VECTOR_BACKEND:-embedded}"
export AIONS_API_BASE_URL="${AIONS_API_BASE_URL:-http://127.0.0.1:${AIONS_API_PORT:-8765}}"
export DESKTOP_ENABLED="${DESKTOP_ENABLED:-false}"

cd "${MCP_DIR}"
"${AIONS_PY}" --ensure-venv >/dev/null

# __main__.py venv guard targets Windows Scripts/; Linux systemd uses server module directly.
exec "${AIONS_PY}" -c "
import os, sys
sys.path.insert(0, '${MCP_DIR}')
os.chdir('${MCP_DIR}')
from src.server import mcp_server, log
import anyio
from mcp.server.stdio import stdio_server
log('AIONS MCP starting (Linux systemd)')
async def run():
    async with stdio_server() as (r, w):
        await mcp_server._mcp_server.run(r, w, mcp_server._mcp_server.create_initialization_options())
anyio.run(run)
"
