#!/usr/bin/env bash
# AIONS first-boot — user-space setup po install_aions_host.sh
# Uruchamiany jako użytkownik runtime (aions), nie jako root.
set -euo pipefail

AIONS_USER="${AIONS_USER:-aions}"
AIONS_HOME="${AIONS_HOME:-/home/${AIONS_USER}}"
AIONS_HOST_ENV="${AIONS_HOST_ENV:-/etc/aions/aions-runtime.env}"
AIONS_HOST_MCP_ENV="${AIONS_HOST_MCP_ENV:-/etc/aions/aions-mcp.env}"
AIONS_REPO="${AIONS_REPO:-}"
AIONS_STATE_ROOT="${AIONS_STATE_ROOT:-/var/lib/aions}"
AIONS_LOG_ROOT="${AIONS_LOG_ROOT:-/var/log/aions}"

AIONS_USER_ROOT="${AIONS_HOME}/aions"
AIONS_USER_CONFIG="${AIONS_USER_ROOT}/config"
AIONS_USER_LOG_DIR="${AIONS_USER_ROOT}/logs"
AIONS_USER_BIN_DIR="${AIONS_USER_ROOT}/bin"
AIONS_USER_STATE="${AIONS_USER_ROOT}/state/search"
AIONS_USER_ENV="${AIONS_USER_CONFIG}/aions-runtime.env"
AIONS_USER_MCP_ENV="${AIONS_USER_CONFIG}/aions-mcp.env"
SYSTEMD_USER_DIR="${AIONS_HOME}/.config/systemd/user"
MANIFEST="${AIONS_STATE_ROOT}/install-manifest.json"

log() {
  echo "[AIONS][first-boot] $*"
}

load_manifest() {
  [[ -f "${MANIFEST}" ]] || return 0
  if command -v python3 >/dev/null 2>&1; then
    AIONS_REPO="${AIONS_REPO:-$(python3 -c "import json; print(json.load(open('${MANIFEST}'))['repo'])" 2>/dev/null || true)}"
    AIONS_STATE_ROOT="${AIONS_STATE_ROOT:-$(python3 -c "import json; print(json.load(open('${MANIFEST}'))['state_root'])" 2>/dev/null || true)}"
  fi
}

render_env_from_host() {
  local src="$1"
  local dst="$2"
  [[ -f "${src}" ]] || return 0
  mkdir -p "$(dirname "${dst}")"
  sed \
    -e "s|@HOME@|${AIONS_HOME}|g" \
    -e "s|AIONS_LOG_DIR=.*|AIONS_LOG_DIR=${AIONS_USER_LOG_DIR}|g" \
    "${src}" > "${dst}"
}

setup_user_dirs() {
  log "Katalogi user-space: ${AIONS_USER_ROOT}"
  mkdir -p \
    "${AIONS_USER_CONFIG}" \
    "${AIONS_USER_LOG_DIR}" \
    "${AIONS_USER_BIN_DIR}" \
    "${AIONS_USER_STATE}" \
    "${SYSTEMD_USER_DIR}"
}

install_user_env() {
  log "Env files: ${AIONS_USER_ENV}"
  if [[ -f "${AIONS_HOST_ENV}" ]]; then
    render_env_from_host "${AIONS_HOST_ENV}" "${AIONS_USER_ENV}"
  elif [[ ! -f "${AIONS_USER_ENV}" ]]; then
    cat > "${AIONS_USER_ENV}" <<EOF
AIONS_DEPLOYMENT_PROFILE=host-linux
AIONS_REPO=${AIONS_REPO}
AIONS_LOG_DIR=${AIONS_USER_LOG_DIR}
AIONS_SEARCH_ROOTS=${AIONS_REPO}
AIONS_SEARCH_PROVIDER=aions-linux-index
AIONS_SEARCH_INDEX_PATH=${AIONS_STATE_ROOT}/state/search/aions_search_index.json
CHROMA_PATH=${AIONS_STATE_ROOT}/data/chroma
AIONS_PATH=${AIONS_STATE_ROOT}/data/cbms
DESKTOP_ENABLED=false
EOF
  fi

  if [[ -f "${AIONS_HOST_MCP_ENV}" ]]; then
    render_env_from_host "${AIONS_HOST_MCP_ENV}" "${AIONS_USER_MCP_ENV}"
  elif [[ -f "${AIONS_REPO}/runtime/systemd/user/aions-mcp.env" ]]; then
    render_env_from_host "${AIONS_REPO}/runtime/systemd/user/aions-mcp.env" "${AIONS_USER_MCP_ENV}"
  fi
}

install_user_bin() {
  [[ -n "${AIONS_REPO}" ]] || return 0
  log "Bin wrappers: ${AIONS_USER_BIN_DIR}"

  if [[ -f "${AIONS_REPO}/runtime/scripts/start_aions_mcp.sh" ]]; then
    cp "${AIONS_REPO}/runtime/scripts/start_aions_mcp.sh" "${AIONS_USER_BIN_DIR}/start_aions_mcp.sh"
    chmod +x "${AIONS_USER_BIN_DIR}/start_aions_mcp.sh"
  fi

  if [[ -f "${AIONS_REPO}/runtime/scripts/start_aions_api.sh" ]]; then
    cp "${AIONS_REPO}/runtime/scripts/start_aions_api.sh" "${AIONS_USER_BIN_DIR}/start_aions_api.sh"
    chmod +x "${AIONS_USER_BIN_DIR}/start_aions_api.sh"
  fi

  if [[ -f "${AIONS_REPO}/scripts/aions-ctl" ]]; then
    ln -sfn "${AIONS_REPO}/scripts/aions-ctl" "${AIONS_USER_BIN_DIR}/aions-ctl"
  fi
}

install_user_systemd_units() {
  [[ -n "${AIONS_REPO}" ]] || return 0
  local src="${AIONS_REPO}/runtime/systemd/user"
  [[ -d "${src}" ]] || return 0

  log "Systemd user units -> ${SYSTEMD_USER_DIR}"
  for unit in aions-health.service aions-health.timer aions-mcp.service; do
    [[ -f "${src}/${unit}" ]] && cp "${src}/${unit}" "${SYSTEMD_USER_DIR}/"
  done

  if command -v systemctl >/dev/null 2>&1; then
    systemctl --user daemon-reload 2>/dev/null || true
  fi
}

enable_linger() {
  if command -v loginctl >/dev/null 2>&1; then
    log "loginctl enable-linger ${AIONS_USER}"
    loginctl enable-linger "${AIONS_USER}" >/dev/null 2>&1 || true
  else
    log "loginctl niedostępny — linger pominięty"
  fi
}

write_first_boot_state() {
  cat > "${AIONS_USER_ROOT}/first-boot.state" <<EOF
first_boot_completed=true
first_boot_timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
runtime_user=${AIONS_USER}
runtime_home=${AIONS_HOME}
runtime_env=${AIONS_USER_ENV}
runtime_repo=${AIONS_REPO}
state_root=${AIONS_STATE_ROOT}
EOF
}

main() {
  load_manifest
  setup_user_dirs
  install_user_env
  install_user_bin
  install_user_systemd_units
  enable_linger
  write_first_boot_state

  log "First-boot zakończony dla ${AIONS_USER}"
  log "User env: ${AIONS_USER_ENV}"
  log "User logs: ${AIONS_USER_LOG_DIR}"
  log "Systemd user: ${SYSTEMD_USER_DIR}"
}

main "$@"
