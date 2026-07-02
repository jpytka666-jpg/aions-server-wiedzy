#!/bin/bash
# MCP Server launcher for Git Bash — używa aions_python (repo scripts)
# Usage: ./run_mcp_server.sh [stdio|http]

TRANSPORT="${1:-stdio}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AIONS_PY="${REPO_ROOT}/scripts/aions_python.sh"

export PYTHONIOENCODING=utf-8
export PYTHONUNBUFFERED=1
export PYTHONUTF8=1
export CHROMA_PATH="${CHROMA_PATH:-$REPO_ROOT/data/chroma}"
export ANONYMIZED_TELEMETRY=False
export CHROMA_TELEMETRY_ENABLED=false
export AIONS_V10_PATH="E:/AIONS_V10/AIONS_CBMS_RELEASE_V3"
export PYTHONPATH="$REPO_ROOT"

SERVER_DIR="$REPO_ROOT/mcpServers/VS_CODE_MCP_CODEX"

if [[ ! -x "${AIONS_PY}" ]]; then
  echo "[AIONS] Brak ${AIONS_PY}" >&2
  exit 1
fi

PYTHON_EXE="$("${AIONS_PY}" --resolve)"
cd "$SERVER_DIR"
exec "${PYTHON_EXE}" -X utf8 -m src "$TRANSPORT"
