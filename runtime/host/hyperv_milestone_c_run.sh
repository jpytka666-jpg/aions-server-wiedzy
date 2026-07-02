#!/usr/bin/env bash
# Milestone C full test — real Ubuntu 22.04 VM (Hyper-V), systemd user session.
# Invoked on the guest after repo mount at REPO_SRC.
set -euo pipefail

REPO_SRC="${REPO_SRC:-/mnt/aions-repo}"
LOG_DIR="${LOG_DIR:-/var/log/aions/milestone-c}"
PIP_CACHE="${PIP_CACHE:-/mnt/aions-cache/pip}"
VM_USER="${VM_USER:-ubuntu}"

mkdir -p "${LOG_DIR}" "${PIP_CACHE}"

log() { echo "[MILESTONE-C-HYPERV] $(date -Iseconds) $*" | tee -a "${LOG_DIR}/main.log"; }
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

log "Full Milestone C Hyper-V start — REPO_SRC=${REPO_SRC}"

export DEBIAN_FRONTEND=noninteractive
export PIP_CACHE_DIR="${PIP_CACHE}"
export TMPDIR="${PIP_CACHE}/../temp"
mkdir -p "${TMPDIR}"

# Minimal deps; install_aions_host.sh creates venv + pip install
apt-get update -qq
apt-get install -y -qq sudo adduser ca-certificates curl jq git rsync

if ! id aions >/dev/null 2>&1; then
  adduser --disabled-password --gecos "" aions
fi

HOST_DIR="${REPO_SRC}/runtime/host"
[[ -d "${HOST_DIR}" ]] || { log "ERROR: missing ${HOST_DIR}"; exit 1; }
cd "${HOST_DIR}"

run_step install sudo bash install_aions_host.sh --source-repo "${REPO_SRC}"

run_step validate_layout sudo bash validate_install.sh --phase layout

run_step first_boot sudo -u aions \
  AIONS_HOST_ENV=/etc/aions/aions-runtime.env \
  AIONS_HOST_MCP_ENV=/etc/aions/aions-mcp.env \
  AIONS_REPO=/opt/aions/repo \
  AIONS_STATE_ROOT=/var/lib/aions \
  AIONS_LOG_ROOT=/var/log/aions \
  bash first_boot_setup.sh

run_step aions_ctl_up sudo -u aions bash -lc '
  export XDG_RUNTIME_DIR=/run/user/$(id -u aions)
  /opt/aions/repo/scripts/aions-ctl enable health
  /opt/aions/repo/scripts/aions-ctl up
  /opt/aions/repo/scripts/aions-ctl status
'

run_step validate_strict sudo bash validate_install.sh \
  --user aions \
  --phase all \
  --with-runtime \
  --strict-health

log "=== SUMMARY (pre-reboot) ==="
OVERALL=0
for f in install validate_layout first_boot aions_ctl_up validate_strict; do
  ec="?"
  [[ -f "${LOG_DIR}/${f}.exit" ]] && ec="$(cat "${LOG_DIR}/${f}.exit")"
  log "${f}: exit=${ec}"
  [[ "${ec}" != "0" && "${ec}" != "?" ]] && OVERALL=1
done
log "OVERALL_PRE_REBOOT=${OVERALL}"
echo "${OVERALL}" > "${LOG_DIR}/overall_pre_reboot.exit"
exit "${OVERALL}"
