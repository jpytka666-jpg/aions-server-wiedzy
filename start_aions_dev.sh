#!/usr/bin/env bash
set -euo pipefail

AIONS_DEV_ROOT="/mnt/d/AIONS_DEV"
REPO_ROOT="${AIONS_DEV_ROOT}/repo/server-wiedzy"
CACHE_ENV="${REPO_ROOT}/scripts/set_aions_cache_env.sh"
if [[ -f "${CACHE_ENV}" ]]; then
  # shellcheck source=/dev/null
  source "${CACHE_ENV}"
fi
AIONS_PY="${REPO_ROOT}/scripts/aions_python.sh"
AIONS_CTL="${REPO_ROOT}/scripts/aions-ctl"

export CHROMA_PATH="${AIONS_DEV_ROOT}/data/chroma"
export AIONS_PATH="/mnt/d/AIONS-INTEGRATION/aions_core"
export AIONS_SEARCH_PROVIDER="${AIONS_SEARCH_PROVIDER:-aions-linux-index}"
export AIONS_SEARCH_INDEX_PATH="${AIONS_DEV_ROOT}/state/search/aions_search_index.json"
export AIONS_SEARCH_AUTO_REFRESH_SECONDS="${AIONS_SEARCH_AUTO_REFRESH_SECONDS:-900}"
export PYTHONPATH="${REPO_ROOT}:${REPO_ROOT}/server:${REPO_ROOT}/mcpServers/VS_CODE_MCP_CODEX"

usage() {
  cat <<'EOF'
Usage: start_aions_dev.sh [command] [args]

Runtime daily-use:
  up
  down
  restart
  status [health|mcp|all]
  logs [health|mcp|all]
  mcp

Diagnostics / helpers:
  shell
  test-imports
  test-server
  verify-python
EOF
}

require_repo_file() {
  local path="$1"
  local label="$2"
  if [[ ! -e "${path}" ]]; then
    echo "[AIONS_DEV] Brak ${label}: ${path}" >&2
    echo "[AIONS_DEV] Zsynchronizuj mirror E: -> D: przed uruchomieniem." >&2
    exit 1
  fi
}

run_ctl() {
  require_repo_file "${AIONS_CTL}" "aions-ctl"
  chmod +x "${AIONS_CTL}" "${AIONS_PY}" 2>/dev/null || true
  exec "${AIONS_CTL}" "$@"
}

require_repo_file "${AIONS_PY}" "aions_python.sh"

"${AIONS_PY}" --ensure-venv >/dev/null
PY="$("${AIONS_PY}" --resolve)"
VENV_DIR="${AIONS_DEV_ROOT}/venv"
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

cd "${REPO_ROOT}"

COMMAND="${1:-shell}"
shift || true

case "${COMMAND}" in
  up|down|restart)
    run_ctl "${COMMAND}" "$@"
    ;;
  status)
    run_ctl status "${1:-all}"
    ;;
  logs)
    run_ctl logs "${1:-all}"
    ;;
  shell)
    echo "[AIONS_DEV] Env ready. REPO=${REPO_ROOT}"
    echo "  Python: ${PY}"
    echo "  CHROMA_PATH=${CHROMA_PATH}"
    echo "  AIONS_PATH=${AIONS_PATH}"
    ;;
  test-imports)
    "${AIONS_PY}" -c "import chromadb; import mcp; print('OK: chromadb', chromadb.__version__, 'mcp import ok')"
    ;;
  test-server)
    "${AIONS_PY}" -c "
import json, os, sys
sys.path.insert(0, os.path.join('${REPO_ROOT}', 'mcpServers', 'VS_CODE_MCP_CODEX'))
os.environ.setdefault('CHROMA_PATH', '${CHROMA_PATH}')
os.environ.setdefault('AIONS_PATH', '${AIONS_PATH}')
from src.server import system_health
print(json.dumps(json.loads(system_health()) if isinstance(system_health(), str) else system_health(), indent=2))
"
    ;;
  mcp)
    exec "${AIONS_PY}" "${REPO_ROOT}/mcpServers/VS_CODE_MCP_CODEX/src/__main__.py" stdio 2>/dev/null || \
      "${AIONS_PY}" -c "
import sys, os
sys.path.insert(0, '${REPO_ROOT}/mcpServers/VS_CODE_MCP_CODEX')
os.chdir('${REPO_ROOT}/mcpServers/VS_CODE_MCP_CODEX')
from src.server import mcp_server, log
import anyio
from mcp.server.stdio import stdio_server
log('AIONS dev MCP starting (Linux stdio)')
async def run():
    async with stdio_server() as (r, w):
        await mcp_server._mcp_server.run(r, w, mcp_server._mcp_server.create_initialization_options())
anyio.run(run)
"
    ;;
  verify-python)
    "${AIONS_PY}" "${REPO_ROOT}/scripts/verify_python_env.py"
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    usage >&2
    exit 1
    ;;
esac
