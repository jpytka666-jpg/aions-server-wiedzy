"""Env / path config for AIONS GGUF Runner (Faza 0)."""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
EXP_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_GGUF = (
    REPO_ROOT
    / "models"
    / "qwen2.5-3b-instruct"
    / "qwen2.5-3b-instruct-q4_K_M.gguf"
)

# Prefer existing llama-cli next to Bielik (read-only D:); override via env.
DEFAULT_LLAMA_CLI_CANDIDATES = (
    Path(r"D:\LOCAL LLM MODELS\Bielik-4.5B-Q4_K_M\llama-cli.exe"),
    Path(r"C:\Users\User\OneDrive\Desktop\PYTHON\llama-b6181-bin-win-cpu-x64\llama-cli.exe"),
)


def _env(name: str, default: str = "") -> str:
    val = os.environ.get(name)
    return val if val not in (None, "") else default


def gguf_path() -> Path:
    return Path(_env("AIONS_GGUF_PATH", str(DEFAULT_GGUF)))


def llama_cli_path() -> Path | None:
    explicit = _env("AIONS_LLAMA_CLI")
    if explicit:
        p = Path(explicit)
        return p if p.is_file() else None
    for cand in DEFAULT_LLAMA_CLI_CANDIDATES:
        if cand.is_file():
            return cand
    return None


def host() -> str:
    return _env("AIONS_GGUF_HOST", "http://127.0.0.1:11435").rstrip("/")


def n_predict() -> int:
    try:
        return int(_env("AIONS_MOUTH_NUM_PREDICT", "200"))
    except ValueError:
        return 200


def n_ctx() -> int:
    try:
        return int(_env("AIONS_GGUF_N_CTX", "2048"))
    except ValueError:
        return 2048


def timeout_s() -> float:
    try:
        return float(_env("AIONS_MOUTH_TIMEOUT", "180"))
    except ValueError:
        return 180.0


def model_tag() -> str:
    return _env("AIONS_MOUTH_MODEL", "aions-mouth")


def backend_mode() -> str:
    """real | stub — auto if llama-cli + gguf present."""
    forced = _env("AIONS_GGUF_MODE", "auto").lower()
    cli = llama_cli_path()
    gguf = gguf_path()
    can_real = bool(cli and cli.is_file() and gguf.is_file())
    if forced == "stub":
        return "stub"
    if forced == "real":
        return "real" if can_real else "stub"
    return "real" if can_real else "stub"
