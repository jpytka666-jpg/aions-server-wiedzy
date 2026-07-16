"""
AIONS Knowledge Server - API-backed VectorStore adapter.

Allows selected MCP/runtime paths to use the localhost FastAPI control plane
instead of loading the embedded Chroma stack in-process.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Tuple
from urllib import error, parse, request

DEFAULT_API_BASE_URL = os.environ.get("AIONS_API_BASE_URL", "http://127.0.0.1:8765").rstrip("/")


def get_connection_mode() -> str:
    """Return current backing mode for diagnostics."""
    return "api"


class VectorStore:
    """Thin HTTP client that mirrors the embedded VectorStore interface."""

    def __init__(self, persist_path: str | None = None, api_base_url: str | None = None) -> None:
        self.persist_path = persist_path
        self.base_url = (api_base_url or DEFAULT_API_BASE_URL).rstrip("/")

    def _request(
        self,
        method: str,
        path: str,
        payload: Dict[str, Any] | None = None,
        timeout: int = 10,
    ) -> Dict[str, Any]:
        data = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = request.Request(
            url=f"{self.base_url}{path}",
            data=data,
            headers=headers,
            method=method.upper(),
        )
        try:
            with request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else {}
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"API request failed: {exc.code} {body[:300]}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"API request failed: {exc.reason}") from exc

    def add_items(self, session_id: str, items: List[Tuple[str | None, str, dict | None]]):
        batch_items = [
            {"id": item_id, "text": text, "metadata": metadata or {}}
            for item_id, text, metadata in items
        ]
        response = self._request(
            "POST",
            "/contexts",
            {"session_id": session_id, "items": batch_items},
        )
        return response.get("ids", [])

    def search(
        self,
        session_id: str,
        query: str,
        top_k: int = 5,
        metadata_filter: Dict[str, Any] | None = None,
        keyword_bias: float = 0.0,
    ):
        response = self._request(
            "POST",
            "/search",
            {
                "session_id": session_id,
                "query": query,
                "top_k": top_k,
                "metadata_filter": metadata_filter,
                "keyword_bias": keyword_bias,
            },
        )
        return response.get("results", [])

    def sessions_count(self) -> int:
        response = self._request("GET", "/health")
        return int(response.get("sessions", 0))

    def list_sessions(self):
        response = self._request("GET", "/sessions")
        sessions = response.get("sessions", [])
        normalized = []
        for session in sessions:
            normalized.append(
                {
                    "session_id": session.get("session_id"),
                    "documents": session.get("documents", 0),
                    "metadata": session.get("metadata"),
                }
            )
        return normalized

    def session_stats(self, session_id: str):
        encoded = parse.quote(session_id, safe="")
        return self._request("GET", f"/sessions/{encoded}")

    def dump_session(self, session_id: str):
        encoded = parse.quote(session_id, safe="")
        return self._request("GET", f"/sessions/{encoded}/dump")

    def prune_expired(self, session_id: str, older_than: datetime | None = None):
        encoded = parse.quote(session_id, safe="")
        payload = {}
        if older_than is not None:
            payload["cutoff_iso"] = older_than.isoformat().replace("+00:00", "Z")
        response = self._request(
            "POST",
            f"/sessions/{encoded}/prune",
            payload or {},
        )
        return int(response.get("removed", 0))

    def summary(self):
        return self._request("GET", "/dashboard")

    def get_status(self) -> Dict[str, Any]:
        status = self._request("GET", "/status")
        status["base_url"] = self.base_url
        return status
