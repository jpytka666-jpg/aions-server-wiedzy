#!/usr/bin/env bash
# AIONS Python launcher (WSL/Linux) — resolves correct venv from .aions/python.env
# Nigdy nie wołaj bare `python` w AIONS. Użyj start_aions_dev.sh lub ten skrypt.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONFIG="${REPO_ROOT}/.aions/python.env"

usage() {
  echo "Usage: $0 [--resolve|--ensure-venv] [python args...]" >&2
  exit 1
}

read_config() {
  if [[ ! -f "${CONFIG}" ]]; then
    local fallback="/mnt/e/server wiedzy/.aions/python.env"
    if [[ -f "${fallback}" ]]; then
      CONFIG="${fallback}"
      REPO_ROOT="/mnt/e/server wiedzy"
    else
      echo "[AIONS] Brak ${CONFIG}" >&2
      exit 1
    fi
  fi
  while IFS= read -r line || [[ -n "${line}" ]]; do
    line="${line%$'\r'}"
    [[ -z "${line}" || "${line}" == \#* ]] && continue
    local key="${line%%=*}"
    local val="${line#*=}"
    case "${key}" in
      AIONS_PYTHON_VERSION) AIONS_PYTHON_VERSION="${val}" ;;
      AIONS_VENV_LINUX) AIONS_VENV_LINUX="${val}" ;;
      AIONS_REPO_LINUX) AIONS_REPO_LINUX="${val}" ;;
      AIONS_VENV_WIN|AIONS_REPO_WIN) ;;
      AIONS_*)
        # Export runtime keys (e.g. AIONS_MOUTH_BACKEND) into process env
        export "${key}=${val}"
        ;;
    esac
  done < "${CONFIG}"
  if [[ -z "${AIONS_PYTHON_VERSION:-}" || -z "${AIONS_VENV_LINUX:-}" ]]; then
    echo "[AIONS] python.env: brak AIONS_PYTHON_VERSION lub AIONS_VENV_LINUX" >&2
    exit 1
  fi
}

resolve_python() {
  local py="${AIONS_VENV_LINUX}/bin/python"
  if [[ ! -x "${py}" ]]; then
    echo "[AIONS] Brak venv: ${py}" >&2
    echo "[AIONS] Utwórz: python${AIONS_PYTHON_VERSION} -m venv ${AIONS_VENV_LINUX}" >&2
    exit 1
  fi
  local actual
  actual="$("${py}" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  if [[ "${actual}" != "${AIONS_PYTHON_VERSION}" ]]; then
    echo "[AIONS] Zła wersja: oczekiwano ${AIONS_PYTHON_VERSION}, jest ${actual} (${py})" >&2
    exit 1
  fi
  echo "${py}"
}

ensure_venv() {
  local py="${AIONS_VENV_LINUX}/bin/python"
  if [[ -x "${py}" ]]; then
    resolve_python >/dev/null
    return 0
  fi
  echo "[AIONS] Tworzenie venv ${AIONS_VENV_LINUX} (Python ${AIONS_PYTHON_VERSION})..."
  "python${AIONS_PYTHON_VERSION}" -m venv "${AIONS_VENV_LINUX}"
  resolve_python >/dev/null
  local req="${AIONS_REPO_LINUX}/requirements-linux.txt"
  if [[ -f "${req}" ]]; then
    "${py}" -m pip install -r "${req}"
  fi
}

MODE="run"
ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --resolve)
      MODE="resolve"
      shift
      ;;
    --ensure-venv)
      MODE="ensure"
      shift
      ;;
    -h|--help)
      usage
      ;;
    *)
      ARGS+=("$1")
      shift
      ;;
  esac
done

read_config

case "${MODE}" in
  resolve)
    resolve_python
    ;;
  ensure)
    ensure_venv
    resolve_python
    ;;
  run)
    PY="$(resolve_python)"
    if [[ ${#ARGS[@]} -eq 0 ]]; then
      echo "${PY}"
    else
      exec "${PY}" "${ARGS[@]}"
    fi
    ;;
esac
