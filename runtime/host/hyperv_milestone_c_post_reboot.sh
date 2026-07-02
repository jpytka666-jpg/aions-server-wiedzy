#!/usr/bin/env bash
# Milestone C post-reboot validation on Hyper-V guest.
set -euo pipefail

REPO_SRC="${REPO_SRC:-/opt/aions/repo}"
LOG_DIR="${LOG_DIR:-/var/log/aions/milestone-c}"
mkdir -p "${LOG_DIR}"

log() { echo "[MILESTONE-C-HYPERV-REBOOT] $(date -Iseconds) $*" | tee -a "${LOG_DIR}/reboot.log"; }

log "Post-reboot validation start"
export XDG_RUNTIME_DIR=/run/user/$(id -u aions)

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

HOST_DIR="${REPO_SRC}/runtime/host"
cd "${HOST_DIR}"

run_step aions_ctl_status sudo -u aions bash -lc '
  export XDG_RUNTIME_DIR=/run/user/$(id -u aions)
  /opt/aions/repo/scripts/aions-ctl status
'

run_step validate_post_reboot sudo bash validate_install.sh \
  --user aions \
  --phase all \
  --with-runtime \
  --strict-health

OVERALL=0
for f in aions_ctl_status validate_post_reboot; do
  ec="?"
  [[ -f "${LOG_DIR}/${f}.exit" ]] && ec="$(cat "${LOG_DIR}/${f}.exit")"
  log "${f}: exit=${ec}"
  [[ "${ec}" != "0" && "${ec}" != "?" ]] && OVERALL=1
done
log "OVERALL_POST_REBOOT=${OVERALL}"
echo "${OVERALL}" > "${LOG_DIR}/overall_post_reboot.exit"
exit "${OVERALL}"
