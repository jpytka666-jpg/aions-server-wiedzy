#!/usr/bin/env bash
# AIONS Host Installer v1 — Milestone B
# Idempotentny bootstrap hosta Linux (Oracle ARM, Ubuntu, WSL staging).
#
# Usage:
#   sudo ./install_aions_host.sh [OPTIONS] [ROOT_PREFIX]
#
# Options:
#   --dry-run              Pokaż kroki bez wykonania
#   --skip-runtime-up      Pomiń aions-ctl up (testy layoutu)
#   --source-repo PATH     Źródło repo (domyślnie: katalog nad runtime/host)
#   --install-root opt|srv /opt/aions lub /srv/aions (domyślnie: opt)
#   --allow-user-install   Instalacja bez root w ROOT_PREFIX (np. /tmp) — tylko testy
#   -h, --help             Pomoc
#
#   --prefix PATH          Prefiks ścieżek (np. /tmp/aions-host-test)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_SOURCE_REPO="$(cd "${SCRIPT_DIR}/../.." && pwd)"

DRY_RUN=false
SKIP_RUNTIME_UP=false
ALLOW_USER_INSTALL=false
SOURCE_REPO="${DEFAULT_SOURCE_REPO}"
INSTALL_ROOT_KIND="opt"
AIONS_USER="${AIONS_USER:-aions}"
AIONS_GROUP="${AIONS_GROUP:-aions}"
ROOT_PREFIX="${ROOT_PREFIX:-/}"

usage() {
  sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

log() {
  echo "[AIONS][install] $*"
}

die() {
  echo "[AIONS][install][ERROR] $*" >&2
  exit 1
}

run() {
  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "[DRY-RUN] $*"
  else
    "$@"
  fi
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --dry-run)
        DRY_RUN=true
        shift
        ;;
      --skip-runtime-up)
        SKIP_RUNTIME_UP=true
        shift
        ;;
      --prefix)
        [[ $# -ge 2 ]] || die "--prefix wymaga ścieżki"
        ROOT_PREFIX="$2"
        shift 2
        ;;
      --source-repo)
        [[ $# -ge 2 ]] || die "--source-repo wymaga ścieżki"
        SOURCE_REPO="$2"
        shift 2
        ;;
      --install-root)
        [[ $# -ge 2 ]] || die "--install-root wymaga opt lub srv"
        INSTALL_ROOT_KIND="$2"
        shift 2
        ;;
      --allow-user-install)
        ALLOW_USER_INSTALL=true
        shift
        ;;
      --user)
        [[ $# -ge 2 ]] || die "--user wymaga nazwy"
        AIONS_USER="$2"
        AIONS_GROUP="$2"
        shift 2
        ;;
      -h|--help)
        usage 0
        ;;
      --)
        shift
        break
        ;;
      -*)
        die "Nieznana opcja: $1"
        ;;
      *)
        ROOT_PREFIX="$1"
        shift
        ;;
    esac
  done
}

prefix_path() {
  local suffix="$1"
  suffix="${suffix#/}"
  if [[ "${ROOT_PREFIX}" == "/" ]]; then
    echo "/${suffix}"
  else
    echo "${ROOT_PREFIX}/${suffix}"
  fi
}

normalize_paths() {
  ROOT_PREFIX="${ROOT_PREFIX%/}"
  [[ -z "${ROOT_PREFIX}" ]] && ROOT_PREFIX="/"

  case "${INSTALL_ROOT_KIND}" in
    opt) AIONS_INSTALL_ROOT="$(prefix_path opt/aions)" ;;
    srv) AIONS_INSTALL_ROOT="$(prefix_path srv/aions)" ;;
    *) die "--install-root musi być opt lub srv" ;;
  esac

  AIONS_STATE_ROOT="$(prefix_path var/lib/aions)"
  AIONS_LOG_ROOT="$(prefix_path var/log/aions)"
  AIONS_ETC_ROOT="$(prefix_path etc/aions)"
  AIONS_VENV="${AIONS_INSTALL_ROOT}/venv"
  AIONS_REPO_DEST="${AIONS_INSTALL_ROOT}/repo"
  AIONS_MANIFEST="${AIONS_STATE_ROOT}/install-manifest.json"
  AIONS_HOME="${AIONS_HOME:-${ROOT_PREFIX}/home/${AIONS_USER}}"
  COMPAT_REPO_LINK="$(prefix_path mnt/e/aions-repo)"
}

require_root() {
  if [[ "${DRY_RUN}" == "true" || "${ALLOW_USER_INSTALL}" == "true" ]]; then
    return 0
  fi
  if [[ "${EUID}" -ne 0 ]]; then
    die "Uruchom jako root: sudo $0 (lub --allow-user-install z --prefix /tmp/...)"
  fi
}

maybe_force_user_install() {
  if [[ "${ALLOW_USER_INSTALL}" == "true" ]]; then
    AIONS_USER="$(id -un)"
    AIONS_GROUP="$(id -gn)"
    AIONS_HOME="${HOME}"
    log "User-install: ${AIONS_USER} @ ${ROOT_PREFIX}"
  fi
}

require_source_repo() {
  [[ -d "${SOURCE_REPO}" ]] || die "Brak katalogu źródłowego: ${SOURCE_REPO}"
  [[ -f "${SOURCE_REPO}/requirements-linux.txt" || -f "${SOURCE_REPO}/requirements.txt" ]] \
    || die "Brak requirements-linux.txt / requirements.txt w ${SOURCE_REPO}"
  [[ -x "${SOURCE_REPO}/scripts/aions-ctl" || -f "${SOURCE_REPO}/scripts/aions-ctl" ]] \
    || die "Brak scripts/aions-ctl w ${SOURCE_REPO}"
}

ensure_python311() {
  if command -v python3.11 >/dev/null 2>&1; then
    PYTHON_BIN="python3.11"
  elif [[ "${DRY_RUN}" == "true" ]]; then
    PYTHON_BIN="python3.11"
    log "DRY-RUN: zakładam python3.11 w PATH"
    return 0
  else
    die "Brak python3.11 — zainstaluj: apt install python3.11 python3.11-venv"
  fi
}

ensure_user() {
  if [[ "${ALLOW_USER_INSTALL}" == "true" ]]; then
    log "User-install: pomijam useradd (bieżący: ${AIONS_USER})"
    return 0
  fi
  if id "${AIONS_USER}" >/dev/null 2>&1; then
    log "Użytkownik ${AIONS_USER} już istnieje"
    return 0
  fi
  log "Tworzenie użytkownika ${AIONS_USER}"
  if [[ "${ROOT_PREFIX}" == "/" ]]; then
    run useradd -m -s /bin/bash -U "${AIONS_USER}"
    AIONS_HOME="/home/${AIONS_USER}"
  else
    run mkdir -p "${AIONS_HOME}"
    if [[ "${DRY_RUN}" != "true" ]]; then
      if ! grep -q "^${AIONS_USER}:" /etc/passwd 2>/dev/null; then
        run useradd -M -d "${AIONS_HOME}" -s /bin/bash "${AIONS_USER}" || true
      fi
    fi
  fi
}

create_layout() {
  log "Tworzenie layoutu hosta"
  AIONS_CACHE_ROOT="${AIONS_CACHE_ROOT:-${AIONS_STATE_ROOT}/cache}"
  run mkdir -p \
    "${AIONS_INSTALL_ROOT}" \
    "${AIONS_REPO_DEST}" \
    "${AIONS_STATE_ROOT}/data/chroma" \
    "${AIONS_STATE_ROOT}/data/cbms" \
    "${AIONS_STATE_ROOT}/state/search" \
    "${AIONS_LOG_ROOT}" \
    "${AIONS_ETC_ROOT}" \
    "${AIONS_CACHE_ROOT}/pip" \
    "${AIONS_CACHE_ROOT}/temp" \
    "${AIONS_CACHE_ROOT}/torch" \
    "${AIONS_CACHE_ROOT}/hf/hub" \
    "${AIONS_CACHE_ROOT}/hf/transformers" \
    "${AIONS_CACHE_ROOT}/docker/config"
}

copy_repo() {
  log "Kopiowanie repo: ${SOURCE_REPO} -> ${AIONS_REPO_DEST}"
  if command -v rsync >/dev/null 2>&1; then
    run rsync -a --delete \
      --exclude 'venv/' \
      --exclude '.venv/' \
      --exclude '__pycache__/' \
      --exclude '*.pyc' \
      --exclude '.git/objects/' \
      --exclude 'tools/ChromaFlowStudio/venv/' \
      "${SOURCE_REPO}/" "${AIONS_REPO_DEST}/"
  else
    run mkdir -p "${AIONS_REPO_DEST}"
    run cp -a "${SOURCE_REPO}/." "${AIONS_REPO_DEST}/"
  fi
}

setup_venv() {
  log "Python 3.11 venv: ${AIONS_VENV}"
  if [[ -x "${AIONS_VENV}/bin/python" ]]; then
    log "Venv już istnieje — pomijam tworzenie"
  else
    run "${PYTHON_BIN}" -m venv "${AIONS_VENV}"
  fi

  local req_base="${AIONS_REPO_DEST}"
  [[ "${DRY_RUN}" == "true" && ! -f "${AIONS_REPO_DEST}/requirements-linux.txt" ]] && req_base="${SOURCE_REPO}"
  local req="${req_base}/requirements-linux.txt"
  [[ -f "${req}" ]] || req="${req_base}/requirements.txt"
  log "pip install -r ${req}"
  if [[ "${DRY_RUN}" != "true" ]]; then
    AIONS_CACHE_ROOT="${AIONS_CACHE_ROOT:-${AIONS_STATE_ROOT}/cache}"
    export PIP_CACHE_DIR="${PIP_CACHE_DIR:-${AIONS_CACHE_ROOT}/pip}"
    export TEMP="${TEMP:-${AIONS_CACHE_ROOT}/temp}"
    export TMP="${TMP:-${AIONS_CACHE_ROOT}/temp}"
    export HF_HOME="${HF_HOME:-${AIONS_CACHE_ROOT}/hf}"
    export TORCH_HOME="${TORCH_HOME:-${AIONS_CACHE_ROOT}/torch}"
    "${AIONS_VENV}/bin/python" -m pip install --upgrade pip wheel
    "${AIONS_VENV}/bin/python" -m pip install -r "${req}"
  fi
}

write_python_env() {
  log "Zapis .aions/python.env (profil host-linux)"
  local cfg_dir="${AIONS_REPO_DEST}/.aions"
  run mkdir -p "${cfg_dir}"
  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "[DRY-RUN] write ${cfg_dir}/python.env"
    return 0
  fi
  cat > "${cfg_dir}/python.env" <<EOF
# Generated by install_aions_host.sh — host-linux profile
AIONS_PYTHON_VERSION=3.11
AIONS_VENV_LINUX=${AIONS_VENV}
AIONS_REPO_LINUX=${AIONS_REPO_DEST}
AIONS_VENV_WIN=n/a
AIONS_REPO_WIN=n/a
EOF
}

write_host_env() {
  log "Zapis /etc/aions env files"
  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "[DRY-RUN] write ${AIONS_ETC_ROOT}/aions-runtime.env"
    echo "[DRY-RUN] write ${AIONS_ETC_ROOT}/aions-mcp.env"
    return 0
  fi

  AIONS_CACHE_ROOT="${AIONS_CACHE_ROOT:-${AIONS_STATE_ROOT}/cache}"
  cat > "${AIONS_ETC_ROOT}/aions-runtime.env" <<EOF
AIONS_DEPLOYMENT_PROFILE=host-linux
AIONS_CACHE_ROOT=${AIONS_CACHE_ROOT}
PIP_CACHE_DIR=${AIONS_CACHE_ROOT}/pip
TEMP=${AIONS_CACHE_ROOT}/temp
TMP=${AIONS_CACHE_ROOT}/temp
HF_HOME=${AIONS_CACHE_ROOT}/hf
HUGGINGFACE_HUB_CACHE=${AIONS_CACHE_ROOT}/hf/hub
TRANSFORMERS_CACHE=${AIONS_CACHE_ROOT}/hf/transformers
TORCH_HOME=${AIONS_CACHE_ROOT}/torch
XDG_CACHE_HOME=${AIONS_CACHE_ROOT}
DOCKER_CONFIG=${AIONS_CACHE_ROOT}/docker/config
AIONS_REPO=${AIONS_REPO_DEST}
AIONS_LOG_DIR=${AIONS_LOG_ROOT}
AIONS_SEARCH_ROOTS=${AIONS_REPO_DEST}
AIONS_SEARCH_PROVIDER=aions-linux-index
AIONS_SEARCH_INDEX_PATH=${AIONS_STATE_ROOT}/state/search/aions_search_index.json
AIONS_SEARCH_AUTO_REFRESH_SECONDS=900
AIONS_API_PORT=8765
AIONS_API_BASE_URL=http://127.0.0.1:8765
AIONS_VECTOR_BACKEND=embedded
CHROMA_USE_HTTP=false
CHROMA_HOST=127.0.0.1
CHROMA_PORT=8000
CHROMA_PATH=${AIONS_STATE_ROOT}/data/chroma
AIONS_PATH=${AIONS_STATE_ROOT}/data/cbms
DESKTOP_ENABLED=false
AIONS_SCAN_PATH=${AIONS_REPO_DEST}
PYTHONIOENCODING=utf-8
PYTHONUNBUFFERED=1
PYTHONUTF8=1
ANONYMIZED_TELEMETRY=False
CHROMA_TELEMETRY_ENABLED=false
EOF

  cat > "${AIONS_ETC_ROOT}/aions-mcp.env" <<EOF
AIONS_REPO=${AIONS_REPO_DEST}
AIONS_DEPLOYMENT_PROFILE=host-linux
AIONS_LOG_DIR=${AIONS_HOME}/aions/logs
AIONS_SEARCH_ROOTS=${AIONS_REPO_DEST}
AIONS_VECTOR_BACKEND=embedded
AIONS_API_BASE_URL=http://127.0.0.1:8765
DESKTOP_ENABLED=false
CHROMA_PATH=${AIONS_STATE_ROOT}/data/chroma
AIONS_PATH=${AIONS_STATE_ROOT}/data/cbms
PYTHONIOENCODING=utf-8
PYTHONUNBUFFERED=1
PYTHONUTF8=1
ANONYMIZED_TELEMETRY=False
CHROMA_TELEMETRY_ENABLED=false
EOF

  chmod 640 "${AIONS_ETC_ROOT}/aions-runtime.env" "${AIONS_ETC_ROOT}/aions-mcp.env" || true
}

write_systemd_units() {
  log "Generowanie host-specific systemd user units w repo"
  local unit_dir="${AIONS_REPO_DEST}/runtime/systemd/user"
  run mkdir -p "${unit_dir}"

  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "[DRY-RUN] write units to ${unit_dir}"
    return 0
  fi

  cat > "${unit_dir}/aions-health.service" <<EOF
[Unit]
Description=AIONS host health check
After=default.target

[Service]
Type=oneshot
WorkingDirectory=%h
EnvironmentFile=%h/aions/config/aions-runtime.env
ExecStart=/usr/bin/env bash -lc 'bash "${AIONS_REPO_DEST}/scripts/aions_healthcheck.sh"'

[Install]
WantedBy=default.target
EOF

  cat > "${unit_dir}/aions-health.timer" <<'EOF'
[Unit]
Description=Run AIONS health check periodically

[Timer]
OnBootSec=2m
OnUnitActiveSec=15m
Unit=aions-health.service

[Install]
WantedBy=timers.target
EOF

  cat > "${unit_dir}/aions-mcp.service" <<'EOF'
[Unit]
Description=AIONS MCP server (host-linux)
After=default.target

[Service]
Type=simple
WorkingDirectory=%h
EnvironmentFile=%h/aions/config/aions-mcp.env
ExecStart=%h/aions/bin/start_aions_mcp.sh
Restart=on-failure
RestartSec=10
StandardInput=null
StandardOutput=append:%h/aions/logs/mcp.log
StandardError=append:%h/aions/logs/mcp.log

[Install]
WantedBy=default.target
EOF

  sed "s|@HOME@|${AIONS_HOME}|g" "${AIONS_REPO_DEST}/runtime/systemd/user/aions-mcp.env" \
    > "${unit_dir}/aions-mcp.env.template" 2>/dev/null || true

  cat > "${unit_dir}/aions-mcp.env" <<EOF
AIONS_REPO=${AIONS_REPO_DEST}
AIONS_DEPLOYMENT_PROFILE=host-linux
AIONS_LOG_DIR=${AIONS_HOME}/aions/logs
AIONS_SEARCH_ROOTS=${AIONS_REPO_DEST}
AIONS_VECTOR_BACKEND=embedded
AIONS_API_BASE_URL=http://127.0.0.1:8765
DESKTOP_ENABLED=false
CHROMA_PATH=${AIONS_STATE_ROOT}/data/chroma
AIONS_PATH=${AIONS_STATE_ROOT}/data/cbms
PYTHONIOENCODING=utf-8
PYTHONUNBUFFERED=1
PYTHONUTF8=1
ANONYMIZED_TELEMETRY=False
CHROMA_TELEMETRY_ENABLED=false
EOF
}

write_manifest() {
  log "Manifest instalacji: ${AIONS_MANIFEST}"
  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "[DRY-RUN] write manifest"
    return 0
  fi
  cat > "${AIONS_MANIFEST}" <<EOF
{
  "layout_version": 1,
  "install_profile": "host-linux-v1",
  "install_root": "${AIONS_INSTALL_ROOT}",
  "state_root": "${AIONS_STATE_ROOT}",
  "log_root": "${AIONS_LOG_ROOT}",
  "etc_root": "${AIONS_ETC_ROOT}",
  "venv": "${AIONS_VENV}",
  "repo": "${AIONS_REPO_DEST}",
  "runtime_user": "${AIONS_USER}",
  "runtime_group": "${AIONS_GROUP}",
  "runtime_home": "${AIONS_HOME}",
  "artifacts": [
    "repo",
    "venv",
    "data/chroma",
    "data/cbms",
    "state/search",
    "logs",
    "env",
    "systemd-user"
  ]
}
EOF
}

install_compat_symlink() {
  # aions-ctl (bez zmian core) oczekuje /mnt/e/aions-repo — shim dla host-linux.
  log "Compat symlink dla aions-ctl: ${COMPAT_REPO_LINK} -> ${AIONS_REPO_DEST}"
  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "[DRY-RUN] ln -sfn ${AIONS_REPO_DEST} ${COMPAT_REPO_LINK}"
    return 0
  fi
  run mkdir -p "$(dirname "${COMPAT_REPO_LINK}")"
  if [[ -e "${COMPAT_REPO_LINK}" && ! -L "${COMPAT_REPO_LINK}" ]]; then
    log "UWAGA: ${COMPAT_REPO_LINK} istnieje i nie jest symlinkiem — pomijam"
    return 0
  fi
  run ln -sfn "${AIONS_REPO_DEST}" "${COMPAT_REPO_LINK}"
}

fix_ownership() {
  if [[ "${ALLOW_USER_INSTALL}" == "true" ]]; then
    log "User-install: pomijam chown"
    return 0
  fi
  log "Ustawianie właścicieli (${AIONS_USER}:${AIONS_GROUP})"
  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "[DRY-RUN] chown -R ${AIONS_USER}:${AIONS_GROUP} ..."
    return 0
  fi
  chown -R "${AIONS_USER}:${AIONS_GROUP}" \
    "${AIONS_INSTALL_ROOT}" \
    "${AIONS_STATE_ROOT}" \
    "${AIONS_LOG_ROOT}" 2>/dev/null || true
  chown root:"${AIONS_GROUP}" "${AIONS_ETC_ROOT}" 2>/dev/null || true
  chown root:"${AIONS_GROUP}" "${AIONS_ETC_ROOT}/"*.env 2>/dev/null || true
  chown -R "${AIONS_USER}:${AIONS_GROUP}" "${AIONS_HOME}/aions" 2>/dev/null || true
}

run_first_boot() {
  log "First-boot jako ${AIONS_USER}"
  local fb="${AIONS_REPO_DEST}/runtime/host/first_boot_setup.sh"
  [[ -f "${fb}" ]] || fb="${SOURCE_REPO}/runtime/host/first_boot_setup.sh"
  [[ -f "${fb}" ]] || die "Brak first_boot_setup.sh w repo"

  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "[DRY-RUN] sudo -u ${AIONS_USER} AIONS_HOST_ENV=... ${fb}"
    return 0
  fi

  if [[ "${ALLOW_USER_INSTALL}" == "true" ]]; then
    AIONS_HOST_ENV="${AIONS_ETC_ROOT}/aions-runtime.env" \
    AIONS_HOST_MCP_ENV="${AIONS_ETC_ROOT}/aions-mcp.env" \
    AIONS_REPO="${AIONS_REPO_DEST}" \
    AIONS_STATE_ROOT="${AIONS_STATE_ROOT}" \
    AIONS_LOG_ROOT="${AIONS_LOG_ROOT}" \
    bash "${fb}"
    return 0
  fi

  run sudo -u "${AIONS_USER}" \
    AIONS_USER="${AIONS_USER}" \
    AIONS_HOME="${AIONS_HOME}" \
    AIONS_HOST_ENV="${AIONS_ETC_ROOT}/aions-runtime.env" \
    AIONS_HOST_MCP_ENV="${AIONS_ETC_ROOT}/aions-mcp.env" \
    AIONS_REPO="${AIONS_REPO_DEST}" \
    AIONS_STATE_ROOT="${AIONS_STATE_ROOT}" \
    AIONS_LOG_ROOT="${AIONS_LOG_ROOT}" \
    bash "${fb}"
}

run_runtime_up() {
  if [[ "${SKIP_RUNTIME_UP}" == "true" ]]; then
    log "Pominięto aions-ctl up (--skip-runtime-up)"
    return 0
  fi

  log "Uruchamianie runtime: aions-ctl up"
  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "[DRY-RUN] sudo -u ${AIONS_USER} ${AIONS_REPO_DEST}/scripts/aions-ctl up"
    return 0
  fi

  if ! sudo -u "${AIONS_USER}" systemctl --user show-environment >/dev/null 2>&1; then
    log "UWAGA: systemd user session niedostępny — pomijam aions-ctl up"
    log "Po zalogowaniu jako ${AIONS_USER}: ${AIONS_REPO_DEST}/scripts/aions-ctl up"
    return 0
  fi

  sudo -u "${AIONS_USER}" \
    AIONS_LOG_DIR="${AIONS_HOME}/aions/logs" \
    CHROMA_PATH="${AIONS_STATE_ROOT}/data/chroma" \
    AIONS_PATH="${AIONS_STATE_ROOT}/data/cbms" \
    bash -lc "cd '${AIONS_REPO_DEST}' && ./scripts/aions-ctl up"
}

verify_health() {
  log "Weryfikacja health"
  if [[ "${DRY_RUN}" == "true" || "${SKIP_RUNTIME_UP}" == "true" ]]; then
    log "Pominięto health verify (dry-run lub skip-runtime-up)"
    return 0
  fi

  if [[ "${DRY_RUN}" != "true" ]]; then
    if sudo -u "${AIONS_USER}" \
      AIONS_LOG_DIR="${AIONS_HOME}/aions/logs" \
      CHROMA_PATH="${AIONS_STATE_ROOT}/data/chroma" \
      AIONS_PATH="${AIONS_STATE_ROOT}/data/cbms" \
      bash -lc "'${AIONS_REPO_DEST}/scripts/aions_healthcheck.sh'" 2>&1 | tee -a "${AIONS_LOG_ROOT}/install-health.log"; then
      log "Health check: GREEN"
    else
      log "Health check: FAILED — sprawdź ${AIONS_LOG_ROOT}/install-health.log"
      return 1
    fi
  fi
}

main() {
  parse_args "$@"
  local _cache_env="${SOURCE_REPO}/scripts/set_aions_cache_env.sh"
  if [[ -f "${_cache_env}" ]]; then
    # shellcheck source=/dev/null
    source "${_cache_env}"
  fi
  normalize_paths
  require_root
  maybe_force_user_install
  require_source_repo
  ensure_python311

  log "=== AIONS Host Installer v1 ==="
  log "ROOT_PREFIX=${ROOT_PREFIX}"
  log "INSTALL_ROOT=${AIONS_INSTALL_ROOT}"
  log "SOURCE_REPO=${SOURCE_REPO}"
  log "USER=${AIONS_USER}"
  [[ "${DRY_RUN}" == "true" ]] && log "TRYB: dry-run"

  ensure_user
  create_layout
  copy_repo
  setup_venv
  write_python_env
  write_host_env
  write_systemd_units
  write_manifest
  install_compat_symlink
  fix_ownership
  run_first_boot
  run_runtime_up
  verify_health

  log "=== Instalacja zakończona ==="
  log "Manifest: ${AIONS_MANIFEST}"
  log "Env: ${AIONS_ETC_ROOT}/aions-runtime.env"
  log "Repo: ${AIONS_REPO_DEST}"
  log "Następny krok: sudo -u ${AIONS_USER} ${AIONS_REPO_DEST}/scripts/aions-ctl status"
}

main "$@"
