from __future__ import annotations
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple
import uuid

import chromadb  # type: ignore[reportMissingImports]
from chromadb.config import Settings  # type: ignore[reportMissingImports]

from .context_schema import normalize_metadata

CHROMA_PATH = os.environ.get("CHROMA_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "chroma"))

def _distance_to_similarity(distance: float, space: str | None) -> float:
    """Convert a Chroma query distance into a 0..1 similarity score.

    Chroma's distance meaning depends on the collection's hnsw:space:
      - "cosine": distance = 1 - cosine_similarity (range 0..2) -> similarity = 1 - distance
      - "ip":     distance = 1 - inner_product; for unit-normalised embeddings this
                  behaves like cosine distance -> similarity = 1 - distance
      - "l2" (or unset/None): Chroma's DEFAULT when hnsw:space is not explicitly
                  configured. This is SQUARED L2 distance, not cosine distance.
                  For unit-normalised embeddings (e.g. all-MiniLM-L6-v2 output),
                  squared_L2 = 2 - 2*cosine_similarity, so:
                      cosine_similarity = 1 - (squared_L2 / 2)
    """
    space_key = (space or "l2").strip().lower()
    if space_key in ("cosine", "ip", "dot", "inner_product"):
        similarity = 1.0 - distance
    else:  # "l2" / squared L2 (Chroma default when hnsw:space is unset)
        similarity = 1.0 - (distance / 2.0)
    return max(0.0, min(1.0, similarity))


class VectorStore:
    """Session-scoped collections in ChromaDB persistent client."""
    def __init__(self, persist_path: str | None = None) -> None:
        self.persist_path = (persist_path or CHROMA_PATH).replace('\\', '/')
        os.makedirs(self.persist_path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.persist_path)
        self._collections: Dict[str, chromadb.api.models.Collection.Collection] = {}

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
            coll_space = None
            try:
                coll_meta = getattr(coll, "metadata", None) or {}
                coll_space = coll_meta.get("hnsw:space")
            except Exception:
                coll_space = None
            for i in range(len(ids)):
                # Chroma returns distance where lower is better; convert to score 0..1
                # using the collection's actual distance metric (defaults to squared L2,
                # which is Chroma's default when hnsw:space is not set explicitly).
                dist = float(dists[i]) if i < len(dists) else 0.0
                base_score = _distance_to_similarity(dist, coll_space)
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
        }
