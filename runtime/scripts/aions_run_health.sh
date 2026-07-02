#!/usr/bin/env bash
# systemd launcher for AIONS health check — no hardcoded repo paths.
set -euo pipefail

AIONS_REPO="${AIONS_REPO:-/mnt/e/aions-repo}"
AIONS_LOG_DIR="${AIONS_LOG_DIR:-${HOME}/aions/logs}"
AIONS_DEV_ROOT="${AIONS_DEV_ROOT:-/mnt/d/AIONS_DEV}"

_resolve_health_script() {
  local candidate="${AIONS_REPO}/scripts/aions_healthcheck.sh"
  if [[ -f "${candidate}" ]]; then
    echo "${candidate}"
    return 0
  fi
  candidate="${AIONS_DEV_ROOT}/repo/server-wiedzy/scripts/aions_healthcheck.sh"
  if [[ -f "${candidate}" ]]; then
    echo "${candidate}"
    return 0
  fi
  echo "[AIONS] Brak aions_healthcheck.sh (AIONS_REPO=${AIONS_REPO})" >&2
  return 1
}

HEALTH_SCRIPT="$(_resolve_health_script)"

export AIONS_LOG_DIR
export CHROMA_PATH="${CHROMA_PATH:-${AIONS_DEV_ROOT}/data/chroma}"
export AIONS_PATH="${AIONS_PATH:-/mnt/d/AIONS-INTEGRATION/aions_core}"
export AIONS_SEARCH_INDEX_PATH="${AIONS_SEARCH_INDEX_PATH:-${HOME}/aions/state/search/aions_search_index.json}"
export AIONS_SEARCH_PROVIDER="${AIONS_SEARCH_PROVIDER:-aions-linux-index}"
export AIONS_DEPLOYMENT_PROFILE="${AIONS_DEPLOYMENT_PROFILE:-wsl-dev}"

exec bash "${HEALTH_SCRIPT}"
