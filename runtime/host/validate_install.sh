#!/usr/bin/env bash
# Post-install validation for AIONS host layout (Milestone C).
# Does NOT modify install scripts, aions-ctl, or active systemd units.
#
# Usage:
#   sudo ./validate_install.sh [--root /] [--user aions] [--phase all|layout|reboot|health]
#   ./validate_install.sh --user aions --phase health   # user-space checks only
#
# Phases:
#   layout  - directories, manifest, host env file
#   reboot  - cold-start simulation (re-read manifest/env from disk)
#   health  - first-boot markers + optional runtime health gate
#   all     - layout -> reboot -> health (default)
set -euo pipefail

ROOT_PREFIX="/"
AIONS_USER="${AIONS_USER:-}"
PHASE="all"
WITH_RUNTIME=0
STRICT_HEALTH=0

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

usage() {
  cat <<'EOF'
Usage: validate_install.sh [options]

Options:
  --root PATH          Root prefix for chroot/staging checks (default: /)
  --user NAME          Runtime user for first-boot / health checks (default: from manifest)
  --phase PHASE        layout | reboot | health | all (default: all)
  --with-runtime       Run scripts/aions_healthcheck.sh when repo + venv are present
  --strict-health      Treat missing runtime health gate as FAIL (default: WARN)
  -h, --help           Show this help

Exit codes:
  0  all requested checks passed (warnings allowed unless --strict-health)
  1  one or more checks failed

Examples:
  sudo ./validate_install.sh
  sudo ./validate_install.sh --root /mnt/aions-root --phase layout
  sudo ./validate_install.sh --user aions --with-runtime
EOF
}

log_pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  echo "[PASS] $*"
}

log_warn() {
  WARN_COUNT=$((WARN_COUNT + 1))
  echo "[WARN] $*"
}

log_fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  echo "[FAIL] $*" >&2
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    log_fail "missing required command: $1"
    return 1
  }
}

abs_root() {
  local root="${1:-/}"
  root="${root%/}"
  [[ -n "${root}" ]] || root="/"
  printf '%s\n' "${root}"
}

path_under_root() {
  local rel="$1"
  local root
  root="$(abs_root "${ROOT_PREFIX}")"
  if [[ "${rel}" == /* ]]; then
    printf '%s\n' "${root}${rel}"
  else
    printf '%s/%s\n' "${root}" "${rel#./}"
  fi
}

read_manifest_value() {
  local key="$1"
  local manifest="$2"
  python3 - "$key" "$manifest" <<'PY'
import json
import sys

key, path = sys.argv[1], sys.argv[2]
with open(path, encoding="utf-8") as fh:
    data = json.load(fh)
value = data.get(key)
if value is None:
    raise SystemExit(1)
if isinstance(value, (dict, list)):
    print(json.dumps(value))
else:
    print(value)
PY
}

manifest_path() {
  path_under_root "var/lib/aions/install-manifest.json"
}

load_paths_from_manifest() {
  local manifest="$1"
  INSTALL_ROOT="$(read_manifest_value install_root "${manifest}")"
  STATE_ROOT="$(read_manifest_value state_root "${manifest}")"
  LOG_ROOT="$(read_manifest_value log_root "${manifest}")"
  ETC_ROOT="$(read_manifest_value etc_root "${manifest}")"
  MANIFEST_USER="$(read_manifest_value runtime_user "${manifest}")"
  MANIFEST_HOME="$(read_manifest_value runtime_home "${manifest}")"
  LAYOUT_VERSION="$(read_manifest_value layout_version "${manifest}")"
}

check_dir() {
  local label="$1"
  local dir="$2"
  if [[ -d "${dir}" ]]; then
    log_pass "${label}: ${dir}"
    return 0
  fi
  log_fail "${label} missing: ${dir}"
  return 1
}

check_file() {
  local label="$1"
  local file="$2"
  if [[ -f "${file}" ]]; then
    log_pass "${label}: ${file}"
    return 0
  fi
  log_fail "${label} missing: ${file}"
  return 1
}

check_env_keys() {
  local env_file="$1"
  shift
  local key
  for key in "$@"; do
    if grep -Eq "^[[:space:]]*${key}=" "${env_file}"; then
      log_pass "env key present: ${key}"
    else
      log_fail "env key missing: ${key} in ${env_file}"
    fi
  done
}

phase_layout() {
  echo "=== Phase: layout ==="
  require_cmd python3

  local manifest
  manifest="$(manifest_path)"
  check_file "install manifest" "${manifest}" || return 0

  load_paths_from_manifest "${manifest}"

  if [[ "${LAYOUT_VERSION}" == "1" ]]; then
    log_pass "layout_version=1"
  else
    log_fail "unexpected layout_version: ${LAYOUT_VERSION}"
  fi

  check_dir "install_root" "${INSTALL_ROOT}"
  check_dir "repo" "${INSTALL_ROOT}/repo"
  check_dir "state_root" "${STATE_ROOT}"
  check_dir "chroma data" "${STATE_ROOT}/data/chroma"
  check_dir "cbms data" "${STATE_ROOT}/data/cbms"
  check_dir "search state" "${STATE_ROOT}/state/search"
  check_dir "log_root" "${LOG_ROOT}"
  check_dir "etc_root" "${ETC_ROOT}"

  local host_env="${ETC_ROOT}/aions-runtime.env"
  check_file "host runtime env" "${host_env}"
  if [[ -f "${host_env}" ]]; then
    check_env_keys "${host_env}" \
      AIONS_DEPLOYMENT_PROFILE \
      AIONS_REPO \
      AIONS_LOG_DIR \
      AIONS_SEARCH_PROVIDER \
      AIONS_SEARCH_INDEX_PATH \
      AIONS_API_PORT \
      CHROMA_PATH \
      AIONS_PATH \
      DESKTOP_ENABLED
  fi

  if [[ -z "${AIONS_USER}" && -n "${MANIFEST_USER}" ]]; then
    AIONS_USER="${MANIFEST_USER}"
  fi
}

phase_reboot() {
  echo "=== Phase: reboot simulation ==="

  # Simulate cold boot: drop in-shell AIONS/CHROMA exports before re-reading disk state.
  unset AIONS_REPO AIONS_LOG_DIR CHROMA_PATH AIONS_PATH AIONS_DEPLOYMENT_PROFILE || true

  local manifest
  manifest="$(manifest_path)"
  check_file "manifest after reboot" "${manifest}" || return 0
  load_paths_from_manifest "${manifest}"

  check_dir "install_root after reboot" "${INSTALL_ROOT}"
  check_dir "state_root after reboot" "${STATE_ROOT}"
  check_dir "log_root after reboot" "${LOG_ROOT}"

  local host_env="${ETC_ROOT}/aions-runtime.env"
  if [[ ! -f "${host_env}" ]]; then
    log_fail "host env missing after reboot: ${host_env}"
    return 0
  fi

  # shellcheck disable=SC1090
  source "${host_env}"

  local expected_chroma="${STATE_ROOT}/data/chroma"
  local expected_cbms="${STATE_ROOT}/data/cbms"
  if [[ "${CHROMA_PATH}" == "${expected_chroma}" ]]; then
    log_pass "CHROMA_PATH matches state layout"
  else
    log_fail "CHROMA_PATH=${CHROMA_PATH:-<unset>} expected ${expected_chroma}"
  fi
  if [[ "${AIONS_PATH}" == "${expected_cbms}" ]]; then
    log_pass "AIONS_PATH matches state layout"
  else
    log_fail "AIONS_PATH=${AIONS_PATH:-<unset>} expected ${expected_cbms}"
  fi

  if [[ -n "${AIONS_REPO}" && -d "${AIONS_REPO}" ]]; then
    log_pass "AIONS_REPO directory exists: ${AIONS_REPO}"
  else
    log_warn "AIONS_REPO not populated yet (${AIONS_REPO:-<unset>}) — expected before runtime health"
  fi
}

user_home() {
  if [[ -n "${MANIFEST_HOME:-}" ]]; then
    printf '%s\n' "${MANIFEST_HOME}"
    return 0
  fi
  if [[ -n "${AIONS_USER}" ]]; then
    if command -v getent >/dev/null 2>&1; then
      getent passwd "${AIONS_USER}" | cut -d: -f6
      return 0
    fi
    printf '/home/%s\n' "${AIONS_USER}"
  fi
}

phase_health() {
  echo "=== Phase: health ==="

  if [[ -z "${AIONS_USER}" ]]; then
    log_warn "no --user and no manifest runtime_user; skipping user-space health"
    return 0
  fi

  local home
  home="$(user_home || true)"
  if [[ -z "${home}" ]]; then
    log_fail "cannot resolve home for user ${AIONS_USER}"
    return 0
  fi

  if id "${AIONS_USER}" >/dev/null 2>&1; then
    log_pass "runtime user exists: ${AIONS_USER}"
  else
    log_fail "runtime user missing: ${AIONS_USER}"
    return 0
  fi

  local user_env="${home}/aions/config/aions-runtime.env"
  local first_boot="${home}/aions/first-boot.state"
  local user_logs="${home}/aions/logs"

  if [[ -f "${user_env}" ]]; then
    log_pass "user runtime env: ${user_env}"
  else
    log_warn "user runtime env missing (run first_boot_setup.sh as ${AIONS_USER}): ${user_env}"
  fi

  if [[ -f "${first_boot}" ]]; then
    log_pass "first-boot marker: ${first_boot}"
  else
    log_warn "first-boot marker missing: ${first_boot}"
  fi

  if [[ -d "${user_logs}" ]]; then
    log_pass "user log dir: ${user_logs}"
  else
    log_warn "user log dir missing: ${user_logs}"
  fi

  if command -v loginctl >/dev/null 2>&1; then
    if loginctl show-user "${AIONS_USER}" -p Linger 2>/dev/null | grep -q 'Linger=yes'; then
      log_pass "systemd user linger enabled for ${AIONS_USER}"
    else
      log_warn "systemd user linger not enabled for ${AIONS_USER}"
    fi
  else
    log_warn "loginctl unavailable; skipped linger check"
  fi

  if [[ "${WITH_RUNTIME}" -ne 1 ]]; then
    log_warn "runtime health gate skipped (use --with-runtime after repo + venv deploy)"
    return 0
  fi

  local manifest
  manifest="$(manifest_path)"
  if [[ ! -f "${manifest}" ]]; then
    log_fail "cannot run runtime health without manifest"
    return 0
  fi
  load_paths_from_manifest "${manifest}"

  local repo="${AIONS_REPO:-${INSTALL_ROOT}/repo}"
  local health_script="${repo}/scripts/aions_healthcheck.sh"
  if [[ ! -x "${health_script}" && -f "${health_script}" ]]; then
    chmod +x "${health_script}" 2>/dev/null || true
  fi

  if [[ ! -f "${health_script}" ]]; then
    if [[ "${STRICT_HEALTH}" -eq 1 ]]; then
      log_fail "runtime health script missing: ${health_script}"
    else
      log_warn "runtime health script missing: ${health_script}"
    fi
    return 0
  fi

  echo "--- runtime health gate (as ${AIONS_USER}) ---"
  if sudo -u "${AIONS_USER}" -H bash -lc "
    set -euo pipefail
    if [[ -f '${user_env}' ]]; then
      set -a
      # shellcheck disable=SC1090
      source '${user_env}'
      set +a
    fi
    export AIONS_LOG_DIR='${user_logs}'
    bash '${health_script}'
  "; then
    log_pass "runtime health gate GREEN"
  else
    if [[ "${STRICT_HEALTH}" -eq 1 ]]; then
      log_fail "runtime health gate RED"
    else
      log_warn "runtime health gate RED (use --strict-health to fail hard)"
    fi
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      ROOT_PREFIX="${2:-}"
      shift 2
      ;;
    --user)
      AIONS_USER="${2:-}"
      shift 2
      ;;
    --phase)
      PHASE="${2:-}"
      shift 2
      ;;
    --with-runtime)
      WITH_RUNTIME=1
      shift
      ;;
    --strict-health)
      STRICT_HEALTH=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

ROOT_PREFIX="$(abs_root "${ROOT_PREFIX}")"

case "${PHASE}" in
  layout) phase_layout ;;
  reboot) phase_reboot ;;
  health) phase_health ;;
  all)
    phase_layout
    phase_reboot
    phase_health
    ;;
  *)
    echo "Unknown phase: ${PHASE}" >&2
    exit 1
    ;;
esac

echo "=== Summary ==="
echo "pass=${PASS_COUNT} warn=${WARN_COUNT} fail=${FAIL_COUNT}"

if [[ "${FAIL_COUNT}" -gt 0 ]]; then
  exit 1
fi
if [[ "${STRICT_HEALTH}" -eq 1 && "${WARN_COUNT}" -gt 0 ]]; then
  exit 1
fi
exit 0
