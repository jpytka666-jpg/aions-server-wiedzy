"""
AIONS Knowledge Server - VectorStore with HTTP Client
======================================================

This version uses ChromaDB HttpClient instead of PersistentClient.
All clients (MCP, Knowledge Server, TS server) connect to shared ChromaDB HTTP server.

FALLBACK: If ChromaDB server unavailable, falls back to PersistentClient (embedded).

Usage:
1. Start ChromaDB server: chroma run --host 0.0.0.0 --port 8000 --path "E:\server wiedzy\data\chroma"
2. Import this module instead of store.py
"""

from __future__ import annotations
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple
import uuid

import chromadb
from chromadb.config import Settings

from .context_schema import normalize_metadata

# Configuration
CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", "8000"))
CHROMA_PATH = os.environ.get("CHROMA_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "chroma"))

# Connection mode tracking
_connection_mode: str = "unknown"


def get_connection_mode() -> str:
    """Return current connection mode: 'http' or 'embedded'"""
    return _connection_mode


class VectorStore:
    """Session-scoped collections in ChromaDB - HTTP client with embedded fallback."""

    def __init__(self, persist_path: str | None = None,
                 chroma_host: str | None = None,
                 chroma_port: int | None = None) -> None:
        global _connection_mode

        self.persist_path = (persist_path or CHROMA_PATH).replace('\\', '/')
        self.host = chroma_host or CHROMA_HOST
        self.port = chroma_port or CHROMA_PORT
        self._collections: Dict[str, chromadb.api.models.Collection.Collection] = {}

        # Try HTTP client first
        self.client = self._connect_http()

        if self.client is None:
            # Fallback to embedded PersistentClient
            print(f"[STORE] ChromaDB HTTP not available at {self.host}:{self.port}, using embedded mode")
            os.makedirs(self.persist_path, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.persist_path)
            _connection_mode = "embedded"
        else:
            _connection_mode = "http"

    def _connect_http(self) -> chromadb.HttpClient | None:
        """Try to connect via HTTP, return None if failed."""
        try:
            client = chromadb.HttpClient(host=self.host, port=self.port)
            # Test connection with heartbeat
            client.heartbeat()
            print(f"[STORE] Connected to ChromaDB HTTP at {self.host}:{self.port}")
            return client
        except Exception as e:
            print(f"[STORE] HTTP connection failed: {e}")
            return None

    def reconnect_http(self) -> bool:
        """Try to reconnect to HTTP server (useful after server restart)."""
        global _connection_mode
        new_client = self._connect_http()
        if new_client:
            self.client = new_client
            self._collections.clear()  # Clear cached collections
            _connection_mode = "http"
            return True
        return False

    def _get_coll(self, session_id: str):
        if session_id in self._collections:
            return self._collections[session_id]
        # create or get collection for session
        coll = self.client.get_or_create_collection(name=f"session_{session_id}")
        self._collections[session_id] = coll
        return coll

    def add_items(self, session_id: str, items: List[Tuple[str | None, str, dict | None]]):
        coll = self._get_coll(session_id)
        ids: List[str] = []
        docs: List[str] = []
        metadatas: List[dict | None] = []
        for iid, text, meta in items:
            ids.append(iid or str(uuid.uuid4()))
            docs.append(text)
            metadatas.append(normalize_metadata(meta))
        coll.add(ids=ids, documents=docs, metadatas=metadatas)
        try:
            coll.modify(metadata={"updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")})
        except Exception:
            pass
        return ids

    def search(self, session_id: str, query: str, top_k: int = 5, metadata_filter: Dict[str, Any] | None = None, keyword_bias: float = 0.0):
        coll = self._get_coll(session_id)
        where = metadata_filter or None
        res = coll.query(query_texts=[query], n_results=max(1, min(100, top_k)), where=where)
        # res: {ids, documents, distances, metadatas}
        hits = []
        if res and res.get("ids"):
            ids = res["ids"][0]
            docs = res["documents"][0]
            dists = res.get("distances", [[0.0]*len(ids)])[0]
            metas = res.get("metadatas", [[None]*len(ids)])[0]
            for i in range(len(ids)):
                # Chroma returns distance where lower is better; convert to score 0..1 (roughly)
                dist = float(dists[i]) if i < len(dists) else 0.0
                base_score = max(0.0, 1.0 - dist)
                keyword_bonus = 0.0
                if keyword_bias and docs[i]:
                    normalized = docs[i].lower()
                    if all(token in normalized for token in query.lower().split()):
                        keyword_bonus = float(keyword_bias)
                total_score = max(0.0, min(1.0, base_score + keyword_bonus))
                hit_payload = {
                    "id": ids[i],
                    "text": docs[i],
                    "score": total_score,
                    "metadata": metas[i],
                }
                if keyword_bonus:
                    hit_payload["keyword_bonus"] = keyword_bonus
                hits.append(hit_payload)
        return hits

    def sessions_count(self) -> int:
        return len(self.client.list_collections())

    def list_sessions(self):
        sessions = []
        for coll_info in self.client.list_collections():
            name = coll_info.name
            coll = self.client.get_collection(name=name)
            metadata = coll_info.metadata or {}
            sessions.append({
                "session_id": name.replace("session_", "", 1),
                "documents": coll.count(),
                "metadata": metadata,
            })
        return sessions

    def session_stats(self, session_id: str):
        coll = self._get_coll(session_id)
        metadata = getattr(coll, "metadata", None)
        total = coll.count()
        if total == 0:
            return {"session_id": session_id, "documents": 0, "metadata": metadata}
        data = coll.get(include=["metadatas"], limit=total)
        timestamps = []
        agents = set()
        for meta in data.get("metadatas", []):
            if not meta:
                continue
            stamp = meta.get("timestamp")
            if stamp:
                try:
                    timestamps.append(datetime.fromisoformat(stamp.replace("Z", "+00:00")))
                except ValueError:
                    pass
            agent = meta.get("agent")
            if agent:
                agents.add(agent)
        timestamps.sort()
        return {
            "session_id": session_id,
            "documents": total,
            "first_entry": timestamps[0].isoformat().replace("+00:00", "Z") if timestamps else None,
            "last_entry": timestamps[-1].isoformat().replace("+00:00", "Z") if timestamps else None,
            "agents": sorted(agents),
            "metadata": metadata,
        }

    def dump_session(self, session_id: str):
        coll = self._get_coll(session_id)
        total = coll.count()
        if total == 0:
            return {"session_id": session_id, "entries": []}
        data = coll.get(include=["documents", "metadatas"], limit=total)
        entries = []
        for iid, doc, meta in zip(data.get("ids", []), data.get("documents", []), data.get("metadatas", [])):
            entries.append({"id": iid, "text": doc, "metadata": meta})
        return {"session_id": session_id, "entries": entries}

    def prune_expired(self, session_id: str, older_than: datetime | None = None):
        coll = self._get_coll(session_id)
        total = coll.count()
        if total == 0:
            return 0
        data = coll.get(include=["metadatas"], limit=total)
        now = older_than or datetime.now(timezone.utc)
        purge_ids: List[str] = []
        for iid, meta in zip(data.get("ids", []), data.get("metadatas", [])):
            if not meta:
                continue
            expires_at = meta.get("expires_at")
            if not expires_at:
                continue
            try:
                expires = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            except ValueError:
                continue
            if expires <= now:
                purge_ids.append(iid)
        if purge_ids:
            for chunk_start in range(0, len(purge_ids), 500):
                coll.delete(ids=purge_ids[chunk_start:chunk_start + 500])
        return len(purge_ids)

    def summary(self):
        sessions = self.list_sessions()
        total_documents = 0
        total_sessions = len(sessions)
        agents_count: Dict[str, int] = {}
        recent_sessions: List[Dict[str, Any]] = []
        for entry in sessions:
            session_id = entry["session_id"]
            stats = self.session_stats(session_id)
            total_documents += stats["documents"]
            for agent in stats.get("agents", []):
                agents_count[agent] = agents_count.get(agent, 0) + stats["documents"]
            recent_sessions.append({
                "session_id": session_id,
                "documents": stats["documents"],
                "last_entry": stats.get("last_entry"),
            })
        recent_sessions.sort(key=lambda item: item.get("last_entry") or "", reverse=True)
        return {
            "total_sessions": total_sessions,
            "total_documents": total_documents,
            "by_agent": agents_count,
            "recent_sessions": recent_sessions[:10],
            "connection_mode": get_connection_mode(),
        }

    def get_status(self) -> Dict[str, Any]:
        """Return connection status info."""
        return {
            "mode": get_connection_mode(),
            "host": self.host if get_connection_mode() == "http" else None,
            "port": self.port if get_connection_mode() == "http" else None,
            "path": self.persist_path if get_connection_mode() == "embedded" else None,
            "sessions": self.sessions_count(),
        }
