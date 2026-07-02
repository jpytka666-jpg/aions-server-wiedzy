#!/usr/bin/env bash
# AIONS dev cache — wyłącznie D: (/mnt/d/AIONS_DEV/cache). NIE C:, NIE E:.
set -euo pipefail

AIONS_CACHE_ROOT="${AIONS_CACHE_ROOT:-/mnt/d/AIONS_DEV/cache}"

export AIONS_CACHE_ROOT
export PIP_CACHE_DIR="${PIP_CACHE_DIR:-${AIONS_CACHE_ROOT}/pip}"
export TEMP="${TEMP:-${AIONS_CACHE_ROOT}/temp}"
export TMP="${TMP:-${AIONS_CACHE_ROOT}/temp}"
export HF_HOME="${HF_HOME:-${AIONS_CACHE_ROOT}/hf}"
export HUGGINGFACE_HUB_CACHE="${HUGGINGFACE_HUB_CACHE:-${HF_HOME}/hub}"
export TRANSFORMERS_CACHE="${TRANSFORMERS_CACHE:-${HF_HOME}/transformers}"
export TORCH_HOME="${TORCH_HOME:-${AIONS_CACHE_ROOT}/torch}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-${AIONS_CACHE_ROOT}}"
export DOCKER_CONFIG="${DOCKER_CONFIG:-${AIONS_CACHE_ROOT}/docker/config}"

mkdir -p \
  "${PIP_CACHE_DIR}" \
  "${TEMP}" \
  "${TORCH_HOME}" \
  "${HF_HOME}/hub" \
  "${HF_HOME}/transformers" \
  "${AIONS_CACHE_ROOT}/docker/config"
