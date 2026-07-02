#!/usr/bin/env bash
# systemd/manual launcher for AIONS localhost-only API control plane.
set -euo pipefail

AIONS_REPO="${AIONS_REPO:-/mnt/e/aions-repo}"
AIONS_LOG_DIR="${AIONS_LOG_DIR:-${HOME}/aions/logs}"
AIONS_API_PORT="${AIONS_API_PORT:-8765}"
AIONS_PY="${AIONS_REPO}/scripts/aions_python.sh"

mkdir -p "${AIONS_LOG_DIR}"

export PYTHONPATH="${AIONS_REPO}:${AIONS_REPO}/server"
export CHROMA_PATH="${CHROMA_PATH:-${AIONS_REPO}/data/chroma}"
export AIONS_PATH="${AIONS_PATH:-/mnt/d/AIONS-INTEGRATION/aions_core}"
export AIONS_DEPLOYMENT_PROFILE="${AIONS_DEPLOYMENT_PROFILE:-wsl-dev}"
export AIONS_SEARCH_ROOTS="${AIONS_SEARCH_ROOTS:-${AIONS_REPO}}"
export AIONS_SEARCH_PROVIDER="${AIONS_SEARCH_PROVIDER:-aions-linux-index}"
export AIONS_SEARCH_INDEX_PATH="${AIONS_SEARCH_INDEX_PATH:-${HOME}/aions/state/search/aions_search_index.json}"
export AIONS_SEARCH_AUTO_REFRESH_SECONDS="${AIONS_SEARCH_AUTO_REFRESH_SECONDS:-900}"
export AIONS_VECTOR_BACKEND="${AIONS_VECTOR_BACKEND:-embedded}"
export CHROMA_TELEMETRY_ENABLED="${CHROMA_TELEMETRY_ENABLED:-false}"
export PYTHONIOENCODING="${PYTHONIOENCODING:-utf-8}"
export PYTHONUNBUFFERED="${PYTHONUNBUFFERED:-1}"
export PYTHONUTF8="${PYTHONUTF8:-1}"
export DESKTOP_ENABLED="${DESKTOP_ENABLED:-false}"

cd "${AIONS_REPO}"
"${AIONS_PY}" --ensure-venv >/dev/null

exec "${AIONS_PY}" -m uvicorn server.app:app \
  --host 127.0.0.1 \
  --port "${AIONS_API_PORT}" \
  --log-level info
