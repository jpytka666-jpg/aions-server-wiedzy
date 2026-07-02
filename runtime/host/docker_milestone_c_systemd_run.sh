#!/usr/bin/env bash
# Milestone C full test — Ubuntu 22.04 with systemd (privileged container).
# Run on Linux host or inside container after systemd init.
set -euo pipefail

REPO_SRC="${REPO_SRC:-/opt/aions/repo}"
LOG_DIR="${LOG_DIR:-/tmp/aions-milestone-c-logs}"
mkdir -p "${LOG_DIR}"

log() { echo "[MILESTONE-C-SYSTEMD] $(date -Iseconds) $*" | tee -a "${LOG_DIR}/main.log"; }
run_step() {
  local name="$1"
  shift
  log "=== STEP: ${name} ==="
  set +e
  "$@" 2>&1 | tee -a "${LOG_DIR}/${name}.log"
  local ec=${PIPESTATUS[0]}
  set -e
  log "=== STEP ${name} exit=${ec} ==="
  echo "${ec}" > "${LOG_DIR}/${name}.exit"
  return "${ec}"
}

log "Full Milestone C start — REPO_SRC=${REPO_SRC} (direct mount, no staging rsync)"

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq \
  sudo python3.11 python3.11-venv python3-pip git rsync curl jq adduser \
  ca-certificates dbus-user-session systemd-sysv || true

if ! id aions >/dev/null 2>&1; then
  adduser --disabled-password --gecos "" aions
fi

[[ -d "${REPO_SRC}/runtime/host" ]] || { log "ERROR: repo mount missing at ${REPO_SRC}"; exit 1; }

HOST_DIR="${REPO_SRC}/runtime/host"
cd "${HOST_DIR}"

# Full install WITHOUT --skip-runtime-up (requires systemd user session)
run_step install bash install_aions_host.sh --source-repo "${REPO_SRC}"

run_step validate_layout sudo bash validate_install.sh --phase layout

run_step first_boot sudo -u aions \
  AIONS_HOST_ENV=/etc/aions/aions-runtime.env \
  AIONS_HOST_MCP_ENV=/etc/aions/aions-mcp.env \
  AIONS_REPO=/opt/aions/repo \
  AIONS_STATE_ROOT=/var/lib/aions \
  AIONS_LOG_ROOT=/var/log/aions \
  bash first_boot_setup.sh

run_step validate_strict sudo bash validate_install.sh \
  --user aions \
  --phase all \
  --with-runtime \
  --strict-health

log "=== SUMMARY ==="
OVERALL=0
for f in install validate_layout first_boot validate_strict; do
  ec="?"
  [[ -f "${LOG_DIR}/${f}.exit" ]] && ec="$(cat "${LOG_DIR}/${f}.exit")"
  log "${f}: exit=${ec}"
  [[ "${ec}" != "0" && "${ec}" != "?" ]] && OVERALL=1
done

log "OVERALL=${OVERALL}"
exit "${OVERALL}"
