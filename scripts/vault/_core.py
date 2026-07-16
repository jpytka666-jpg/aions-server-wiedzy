"""AIONS local secrets vault — Windows DPAPI (CurrentUser), offline, no KMS.

Encrypted blobs live under runtime/secrets/vault/ (gitignored).
Scripts here are tracked; never commit vault data or plaintext secrets.
"""

from __future__ import annotations

import base64
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AIONS_MARKER_PLAIN = b"AIONS_OPERATOR_VAULT_V1"
AIONS_ENTROPY = b"AIONS_LOCAL_VAULT_V1"
VAULT_FORMAT = "aions_vault_v1"
CRYPTO_DPAPI = "dpapi"
MARKER_FILENAME = ".aions_operator.key"
INDEX_FILENAME = "index.json"
BLOB_SUFFIX = ".enc.json"


def repo_root() -> Path:
    env = os.environ.get("AIONS_PATH", "").strip()
    if env:
        return Path(env).parent
    for candidate in (
        Path(r"E:\server wiedzy"),
        Path("/mnt/e/server wiedzy"),
        Path("/mnt/d/AIONS_DEV/repo/server-wiedzy"),
    ):
        if candidate.exists():
            return candidate
    return Path(__file__).resolve().parents[2]


def vault_dir() -> Path:
    path = repo_root() / "runtime" / "secrets" / "vault"
    path.mkdir(parents=True, exist_ok=True)
    return path


def marker_path() -> Path:
    return vault_dir() / MARKER_FILENAME


def index_path() -> Path:
    return vault_dir() / INDEX_FILENAME


def blob_path(vault_id: str) -> Path:
    safe = _sanitize_vault_id(vault_id)
    return vault_dir() / f"{safe}{BLOB_SUFFIX}"


def _sanitize_vault_id(vault_id: str) -> str:
    cleaned = "".join(c if c.isalnum() or c in "-_" else "_" for c in vault_id.strip())
    if not cleaned:
        raise ValueError("vault_id must contain at least one alphanumeric character")
    return cleaned


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# --- Windows DPAPI (ctypes, no pip) -----------------------------------------


def _is_windows() -> bool:
    return platform.system() == "Windows"


def _dpapi_protect(plaintext: bytes, entropy: bytes | None = None) -> bytes:
    if not _is_windows():
        raise RuntimeError("DPAPI vault wymaga Windows (CurrentUser).")
    try:
        return _dpapi_protect_ctypes(plaintext, entropy)
    except Exception:
        return _dpapi_protect_powershell(plaintext, entropy)


def _dpapi_unprotect(ciphertext: bytes, entropy: bytes | None = None) -> bytes:
    if not _is_windows():
        raise RuntimeError("DPAPI vault wymaga Windows (CurrentUser).")
    try:
        return _dpapi_unprotect_ctypes(ciphertext, entropy)
    except Exception:
        return _dpapi_unprotect_powershell(ciphertext, entropy)


def _dpapi_protect_ctypes(plaintext: bytes, entropy: bytes | None) -> bytes:
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]

    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32

    in_blob = DATA_BLOB(len(plaintext), ctypes.cast(ctypes.create_string_buffer(plaintext), ctypes.POINTER(ctypes.c_byte)))
    out_blob = DATA_BLOB()
    entropy_blob = None
    entropy_ptr = None
    if entropy:
        entropy_blob = DATA_BLOB(len(entropy), ctypes.cast(ctypes.create_string_buffer(entropy), ctypes.POINTER(ctypes.c_byte)))
        entropy_ptr = ctypes.byref(entropy_blob)

    if not crypt32.CryptProtectData(
        ctypes.byref(in_blob),
        None,
        entropy_ptr,
        None,
        None,
        0,
        ctypes.byref(out_blob),
    ):
        raise OSError(f"CryptProtectData failed: {ctypes.get_last_error()}")

    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        kernel32.LocalFree(out_blob.pbData)


def _dpapi_unprotect_ctypes(ciphertext: bytes, entropy: bytes | None) -> bytes:
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]

    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32

    in_blob = DATA_BLOB(len(ciphertext), ctypes.cast(ctypes.create_string_buffer(ciphertext), ctypes.POINTER(ctypes.c_byte)))
    out_blob = DATA_BLOB()
    entropy_blob = None
    entropy_ptr = None
    if entropy:
        entropy_blob = DATA_BLOB(len(entropy), ctypes.cast(ctypes.create_string_buffer(entropy), ctypes.POINTER(ctypes.c_byte)))
        entropy_ptr = ctypes.byref(entropy_blob)

    if not crypt32.CryptUnprotectData(
        ctypes.byref(in_blob),
        None,
        entropy_ptr,
        None,
        None,
        0,
        ctypes.byref(out_blob),
    ):
        raise OSError(f"CryptUnprotectData failed: {ctypes.get_last_error()}")

    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        kernel32.LocalFree(out_blob.pbData)


def _ps1_helper() -> Path:
    return Path(__file__).resolve().parent / "dpapi.ps1"


def _dpapi_protect_powershell(plaintext: bytes, entropy: bytes | None) -> bytes:
    ps1 = _ps1_helper()
    if not ps1.exists():
        raise RuntimeError("Brak dpapi.ps1 fallback")
    args = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(ps1),
        "protect",
        base64.b64encode(plaintext).decode("ascii"),
    ]
    if entropy:
        args.append(base64.b64encode(entropy).decode("ascii"))
    proc = subprocess.run(args, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "DPAPI protect (PS) failed")
    return base64.b64decode(proc.stdout.strip())


def _dpapi_unprotect_powershell(ciphertext: bytes, entropy: bytes | None) -> bytes:
    ps1 = _ps1_helper()
    if not ps1.exists():
        raise RuntimeError("Brak dpapi.ps1 fallback")
    args = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(ps1),
        "unprotect",
        base64.b64encode(ciphertext).decode("ascii"),
    ]
    if entropy:
        args.append(base64.b64encode(entropy).decode("ascii"))
    proc = subprocess.run(args, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "DPAPI unprotect (PS) failed")
    return base64.b64decode(proc.stdout.strip())


# --- Marker + index ---------------------------------------------------------


def ensure_operator_marker() -> Path:
    """Create DPAPI-protected operator marker on first seal (CurrentUser only)."""
    path = marker_path()
    if path.exists():
        return path
    protected = _dpapi_protect(AIONS_MARKER_PLAIN, AIONS_ENTROPY)
    path.write_bytes(protected)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return path


def verify_operator_marker() -> None:
    """Raise if marker missing or not decryptable for this Windows user."""
    path = marker_path()
    if not path.exists():
        raise RuntimeError(
            "Brak markera operatora (.aions_operator.key). "
            "Uruchom najpierw seal_secret.py (seal pierwszego sekretu)."
        )
    protected = path.read_bytes()
    plain = _dpapi_unprotect(protected, AIONS_ENTROPY)
    if plain != AIONS_MARKER_PLAIN:
        raise RuntimeError("Marker operatora nieprawidłowy — odmowa odszyfrowania.")


def load_index() -> dict[str, Any]:
    path = index_path()
    if not path.exists():
        return {"version": 1, "entries": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_index(index: dict[str, Any]) -> None:
    index["version"] = 1
    index_path().write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")


def seal_file(
    input_path: Path,
    vault_id: str,
    label: str = "",
) -> Path:
    """Encrypt plaintext file into vault; update index. Returns blob path."""
    if not input_path.is_file():
        raise FileNotFoundError(f"Brak pliku wejściowego: {input_path}")

    ensure_operator_marker()
    safe_id = _sanitize_vault_id(vault_id)
    plaintext = input_path.read_bytes()
    ciphertext = _dpapi_protect(plaintext, AIONS_ENTROPY)

    envelope = {
        "format": VAULT_FORMAT,
        "crypto": CRYPTO_DPAPI,
        "vault_id": safe_id,
        "label": label or safe_id,
        "sealed_at": _now_iso(),
        "original_name": input_path.name,
        "ciphertext_b64": base64.b64encode(ciphertext).decode("ascii"),
    }
    out = blob_path(safe_id)
    out.write_text(json.dumps(envelope, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        os.chmod(out, 0o600)
    except OSError:
        pass

    index = load_index()
    entries = index.setdefault("entries", {})
    entries[safe_id] = {
        "label": envelope["label"],
        "blob": out.name,
        "sealed_at": envelope["sealed_at"],
        "original_name": envelope["original_name"],
    }
    save_index(index)
    return out


def open_vault_entry(vault_id: str) -> bytes:
    """Decrypt vault blob after operator marker check. Returns plaintext bytes."""
    verify_operator_marker()
    safe_id = _sanitize_vault_id(vault_id)
    path = blob_path(safe_id)
    if not path.exists():
        raise FileNotFoundError(f"Brak wpisu vault: {safe_id} ({path})")

    envelope = json.loads(path.read_text(encoding="utf-8"))
    if envelope.get("format") != VAULT_FORMAT or envelope.get("crypto") != CRYPTO_DPAPI:
        raise RuntimeError(f"Nieobsługiwany format vault: {path}")

    ciphertext = base64.b64decode(envelope["ciphertext_b64"])
    return _dpapi_unprotect(ciphertext, AIONS_ENTROPY)


def list_entries() -> dict[str, Any]:
    """Metadata only — no secret bytes."""
    return load_index().get("entries", {})
