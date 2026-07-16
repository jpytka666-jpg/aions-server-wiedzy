from __future__ import annotations
import os
from datetime import datetime
from typing import List
try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
except Exception as e:
    raise ImportError(
        "Brak zależności 'fastapi'. Zainstaluj ją w swoim środowisku uruchomieniowym: "
        "'python -m pip install fastapi uvicorn' i uruchom aplikację ponownie. "
        f"Pierwotny błąd: {e}"
    ) from e
from .models import (
    ContextBatch,
    SearchRequest,
    SearchResponse,
    HealthResponse,
    SearchHit,
    SessionListResponse,
    SessionInfo,
    SessionDumpResponse,
    SessionDumpEntry,
    PruneRequest,
    PruneResponse,
    DashboardSummary,
)
from .store_selector import VectorStore, get_connection_mode

app = FastAPI(title="AIONS Knowledge Server", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = VectorStore(persist_path=os.environ.get("CHROMA_PATH"))

@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", sessions=store.sessions_count())

@app.get("/status")
def status():
    """Extended status with connection mode info."""
    return {
        "status": "ok",
        "sessions": store.sessions_count(),
        "connection_mode": get_connection_mode(),
        "chromadb_mode": "http" if get_connection_mode() == "http" else "embedded",
    }

@app.post("/contexts")
def add_context(batch: ContextBatch):
    tuples = [(item.id, item.text, item.metadata) for item in batch.items]
    ids = store.add_items(batch.session_id, tuples)
    return {"inserted": len(ids), "ids": ids}

@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest):
    hits = store.search(
        req.session_id,
        req.query,
        req.top_k,
        req.metadata_filter,
        req.keyword_bias,
    )
    return SearchResponse(results=[SearchHit(**h) for h in hits])

@app.get("/sessions", response_model=SessionListResponse)
def sessions():
    sessions_raw = store.list_sessions()
    info: List[SessionInfo] = []
    for entry in sessions_raw:
        stats = store.session_stats(entry["session_id"])
        stats["metadata"] = entry.get("metadata")
        info.append(SessionInfo(**stats))
    return SessionListResponse(sessions=info)

@app.get("/sessions/{session_id}", response_model=SessionInfo)
def session_details(session_id: str):
    stats = store.session_stats(session_id)
    return SessionInfo(**stats)

@app.get("/sessions/{session_id}/dump", response_model=SessionDumpResponse)
def session_dump(session_id: str):
    result = store.dump_session(session_id)
    entries = [SessionDumpEntry(**entry) for entry in result["entries"]]
    return SessionDumpResponse(session_id=session_id, entries=entries)

@app.post("/sessions/{session_id}/prune", response_model=PruneResponse)
def session_prune(session_id: str, body: PruneRequest | None = None):
    cutoff = None
    if body and body.cutoff_iso:
        cutoff = datetime.fromisoformat(body.cutoff_iso.replace("Z", "+00:00"))
    removed = store.prune_expired(session_id, cutoff)
    return PruneResponse(session_id=session_id, removed=removed)

@app.get("/dashboard", response_model=DashboardSummary)
def dashboard():
    return DashboardSummary(**store.summary())

try:
    from control_plane.api import router as control_plane_router

    app.include_router(control_plane_router, prefix="/v1")
except ImportError:
    pass
