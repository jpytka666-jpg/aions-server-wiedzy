#!/usr/bin/env bash
# Milestone C isolated test — run inside Ubuntu 22.04/24.04 container as root.
set -euo pipefail

REPO_SRC="${REPO_SRC:-/repo}"
LOG_DIR="${LOG_DIR:-/mnt/aions-logs}"
mkdir -p "${LOG_DIR}"

log() { echo "[MILESTONE-C-TEST] $(date -Iseconds) $*" | tee -a "${LOG_DIR}/main.log"; }
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

log "Container test start — REPO_SRC=${REPO_SRC}"

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq sudo python3.11 python3.11-venv python3-pip git rsync curl jq adduser ca-certificates

if ! id aions >/dev/null 2>&1; then
  adduser --disabled-password --gecos "" aions
fi

HOST_DIR="${REPO_SRC}/runtime/host"
cd "${HOST_DIR}"

# Install host layout + venv (skip systemd runtime in container)
run_step install bash install_aions_host.sh \
  --source-repo "${REPO_SRC}" \
  --skip-runtime-up || INSTALL_EC=$?

run_step validate_layout bash validate_install.sh --phase layout || true

run_step first_boot sudo -u aions \
  AIONS_HOST_ENV=/etc/aions/aions-runtime.env \
  AIONS_HOST_MCP_ENV=/etc/aions/aions-mcp.env \
  AIONS_REPO=/opt/aions/repo \
  AIONS_STATE_ROOT=/var/lib/aions \
  AIONS_LOG_ROOT=/var/log/aions \
  bash first_boot_setup.sh || true

run_step validate_all bash validate_install.sh --user aions --phase all || true

run_step validate_strict bash validate_install.sh \
  --user aions \
  --phase all \
  --with-runtime \
  --strict-health || true

# Manual health gate (independent of systemd)
run_step health_manual sudo -u aions -H bash -lc '
  set -euo pipefail
  source ~/aions/config/aions-runtime.env
  export AIONS_LOG_DIR=~/aions/logs
  bash /opt/aions/repo/scripts/aions_healthcheck.sh
' || true

log "=== SUMMARY ==="
for f in install validate_layout first_boot validate_all validate_strict health_manual; do
  ec="?"
  [[ -f "${LOG_DIR}/${f}.exit" ]] && ec="$(cat "${LOG_DIR}/${f}.exit")"
  log "${f}: exit=${ec}"
done

log "Logs in ${LOG_DIR}"
