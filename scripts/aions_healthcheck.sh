#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_DIR="${AIONS_LOG_DIR:-${HOME}/aions/logs}"
TIMESTAMP="$(date --iso-8601=seconds)"

export CHROMA_PATH="${CHROMA_PATH:-${REPO_ROOT}/data/chroma}"
export PYTHONPATH="${PYTHONPATH:-${REPO_ROOT}:${REPO_ROOT}/server:${REPO_ROOT}/mcpServers/VS_CODE_MCP_CODEX}"

mkdir -p "${LOG_DIR}"

log() {
  echo "[AIONS][health][${TIMESTAMP}] $*"
}

{
  log "repo=${REPO_ROOT}"
  log "systemd_user_state=$(systemctl --user is-system-running 2>/dev/null || true)"

  "${REPO_ROOT}/scripts/aions_python.sh" "${REPO_ROOT}/scripts/verify_python_env.py"

  "${REPO_ROOT}/scripts/aions_python.sh" -c \
    "import chromadb; import sys; print(f'chromadb={getattr(chromadb, \"__version__\", \"unknown\")} python={sys.version.split()[0]}')"

  if [[ "$(uname -s 2>/dev/null || echo unknown)" == "Linux" ]]; then
    export AIONS_SEARCH_INDEX_PATH="${AIONS_SEARCH_INDEX_PATH:-${HOME}/aions/state/search/aions_search_index.json}"
    export AIONS_SEARCH_PROVIDER="${AIONS_SEARCH_PROVIDER:-aions-linux-index}"
    "${REPO_ROOT}/scripts/aions_python.sh" "${REPO_ROOT}/scripts/aions_indexer.py" status \
      || log "index_status=warn (run: aions-ctl index-refresh)"
    if [[ -n "${AIONS_API_BASE_URL:-}" ]] && command -v curl >/dev/null 2>&1; then
      if curl -sf --max-time 3 "${AIONS_API_BASE_URL}/health" >/dev/null; then
        log "api_health=ok url=${AIONS_API_BASE_URL}"
      else
        log "api_health=down (optional) url=${AIONS_API_BASE_URL}"
      fi
    fi
  fi

  log "healthcheck=GREEN"
} 2>&1 | tee -a "${LOG_DIR}/health.log"
