from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


DEFAULT_EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
}


class SearchProviderError(RuntimeError):
    """Raised when the AIONS search provider cannot satisfy a request."""


class AionsLinuxIndexProvider:
    """AIONS-owned filesystem index for Linux/WSL hosts."""

    provider_name = "aions-linux-index"

    def __init__(
        self,
        roots: Sequence[Path],
        index_path: Path,
        *,
        auto_refresh_seconds: int = 900,
        excluded_dirs: Optional[Iterable[str]] = None,
    ) -> None:
        self.roots = [Path(root) for root in roots]
        self.index_path = Path(index_path)
        self.auto_refresh_seconds = max(int(auto_refresh_seconds), 0)
        self.excluded_dirs = {
            entry.strip()
            for entry in (excluded_dirs or DEFAULT_EXCLUDED_DIRS)
            if str(entry).strip()
        }

    def status(self) -> Dict[str, Any]:
        existing_roots = [str(root) for root in self.roots if root.exists()]
        payload: Dict[str, Any] = {
            "provider": self.provider_name,
            "index_path": str(self.index_path),
            "roots": existing_roots,
            "auto_refresh_seconds": self.auto_refresh_seconds,
            "excluded_dirs": sorted(self.excluded_dirs),
            "index_exists": self.index_path.exists(),
            "stale": self._is_stale(),
        }
        if self.index_path.exists():
            stat = self.index_path.stat()
            payload["index_mtime"] = int(stat.st_mtime)
            payload["index_age_seconds"] = max(0, int(time.time() - stat.st_mtime))
            payload["index_size_bytes"] = stat.st_size
            try:
                cached = json.loads(self.index_path.read_text(encoding="utf-8"))
                payload["entry_count"] = int(cached.get("entry_count", len(cached.get("entries", []))))
            except (OSError, json.JSONDecodeError, TypeError, ValueError):
                payload["entry_count"] = None
        return payload

    def ensure_fresh(self) -> Dict[str, Any]:
        """Refresh the index when missing or older than auto_refresh_seconds."""
        if not self.index_path.exists() or self._is_stale():
            return self.refresh()
        return {
            "provider": self.provider_name,
            "refreshed": False,
            "index_path": str(self.index_path),
            "index_age_seconds": max(0, int(time.time() - self.index_path.stat().st_mtime)),
        }

    def refresh(self) -> Dict[str, Any]:
        roots = [root for root in self.roots if root.exists()]
        if not roots:
            raise SearchProviderError("No valid Linux search roots configured")

        entries: List[Dict[str, Any]] = []
        scanned_roots: List[str] = []
        for root in roots:
            scanned_roots.append(str(root))
            entries.extend(self._scan_root(root))

        payload = {
            "version": 1,
            "provider": self.provider_name,
            "generated_at": int(time.time()),
            "roots": scanned_roots,
            "entry_count": len(entries),
            "entries": entries,
        }
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.index_path.with_suffix(self.index_path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp_path, self.index_path)
        return {
            "provider": self.provider_name,
            "roots": scanned_roots,
            "entry_count": len(entries),
            "index_path": str(self.index_path),
        }

    def search(self, query: str, max_results: int, folder: str = "") -> Dict[str, Any]:
        normalized_query = (query or "").strip()
        if not normalized_query:
            raise SearchProviderError("Search query cannot be empty")

        entries = self._load_entries()
        folder_prefix = self._normalize_folder_prefix(folder) if folder else ""
        query_lower = normalized_query.lower()

        scored: List[tuple[int, Dict[str, Any]]] = []
        for entry in entries:
            if folder_prefix and not entry["path_lower"].startswith(folder_prefix):
                continue
            score = self._score_query(entry, query_lower)
            if score <= 0:
                continue
            scored.append((score, entry))

        scored.sort(key=lambda item: (-item[0], item[1]["path"]))
        files = [item[1]["path"] for item in scored[:max_results]]
        return {
            "ok": True,
            "provider": self.provider_name,
            "query": normalized_query,
            "files": files,
            "count": len(files),
        }

    def search_ext(self, extension: str, max_results: int, folder: str = "") -> Dict[str, Any]:
        ext = extension.strip().lstrip(".").lower()
        if not ext:
            raise SearchProviderError("Extension cannot be empty")

        entries = self._load_entries()
        folder_prefix = self._normalize_folder_prefix(folder) if folder else ""
        matches: List[Dict[str, Any]] = []
        for entry in entries:
            if folder_prefix and not entry["path_lower"].startswith(folder_prefix):
                continue
            if entry["ext"] != ext:
                continue
            matches.append(entry)

        matches.sort(key=lambda item: item["path"])
        files = [entry["path"] for entry in matches[:max_results]]
        return {
            "ok": True,
            "provider": self.provider_name,
            "query": f"*.{ext}",
            "files": files,
            "count": len(files),
        }

    def _load_entries(self) -> List[Dict[str, Any]]:
        self.ensure_fresh()

        payload = json.loads(self.index_path.read_text(encoding="utf-8"))
        entries = payload.get("entries", [])
        if not isinstance(entries, list):
            raise SearchProviderError("Search index is corrupted")
        return entries

    def _is_stale(self) -> bool:
        if self.auto_refresh_seconds <= 0:
            return False
        if not self.index_path.exists():
            return True
        age = time.time() - self.index_path.stat().st_mtime
        return age > self.auto_refresh_seconds

    def _scan_root(self, root: Path) -> List[Dict[str, Any]]:
        entries: List[Dict[str, Any]] = []
        for current_root, dirnames, filenames in os.walk(root):
            dirnames[:] = [name for name in dirnames if name not in self.excluded_dirs]
            current_path = Path(current_root)
            rel_root = current_path.relative_to(root)

            for dirname in dirnames:
                dir_path = current_path / dirname
                entries.append(self._make_entry(dir_path, root, rel_root / dirname, is_dir=True))

            for filename in filenames:
                file_path = current_path / filename
                entries.append(self._make_entry(file_path, root, rel_root / filename, is_dir=False))
        return entries

    def _make_entry(self, path: Path, root: Path, relative_path: Path, *, is_dir: bool) -> Dict[str, Any]:
        stat = path.stat()
        ext = "" if is_dir else path.suffix.lstrip(".").lower()
        absolute = str(path)
        return {
            "path": absolute,
            "path_lower": absolute.lower(),
            "name": path.name,
            "name_lower": path.name.lower(),
            "ext": ext,
            "is_dir": is_dir,
            "root": str(root),
            "relative_path": str(relative_path),
            "mtime": int(stat.st_mtime),
            "size": 0 if is_dir else int(stat.st_size),
        }

    @staticmethod
    def _normalize_folder_prefix(folder: str) -> str:
        raw = str(Path(folder).expanduser())
        return raw.rstrip("/\\").lower() + os.sep

    @staticmethod
    def _score_query(entry: Dict[str, Any], query_lower: str) -> int:
        name = entry["name_lower"]
        full_path = entry["path_lower"]
        relative_path = entry["relative_path"].lower()

        if name == query_lower:
            return 150
        if name.startswith(query_lower):
            return 120
        if query_lower in name:
            return 90
        if relative_path.endswith(query_lower):
            return 70
        if query_lower in relative_path:
            return 55
        if query_lower in full_path:
            return 40
        return 0
