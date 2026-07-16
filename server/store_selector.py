"""
AIONS Knowledge Server - Store Selector
=======================================

Automatically selects between HTTP and embedded ChromaDB based on:
1. CHROMA_USE_HTTP env var (if set to 'true', forces HTTP)
2. Auto-detection: tries HTTP first, falls back to embedded

Usage in app.py:
    from .store_selector import VectorStore, get_connection_mode
"""

import os

# Check if user explicitly wants HTTP mode
USE_HTTP = os.environ.get("CHROMA_USE_HTTP", "auto").lower()

if USE_HTTP == "true":
    # Force HTTP mode
    from .store_http import VectorStore, get_connection_mode
    print("[STORE-SELECTOR] Using HTTP mode (forced via CHROMA_USE_HTTP=true)")

elif USE_HTTP == "false":
    # Force embedded mode
    from .store import VectorStore
    def get_connection_mode() -> str:
        return "embedded"
    print("[STORE-SELECTOR] Using embedded mode (forced via CHROMA_USE_HTTP=false)")

else:
    # Auto-detect: try HTTP first, fall back to embedded
    try:
        import chromadb
        client = chromadb.HttpClient(
            host=os.environ.get("CHROMA_HOST", "127.0.0.1"),  # ALWAYS-ON fix: unikamy DNS/IPv6 lag dla "localhost"
            port=int(os.environ.get("CHROMA_PORT", "8000"))
        )
        client.heartbeat()
        # HTTP works, use it
        from .store_http import VectorStore, get_connection_mode
        print("[STORE-SELECTOR] Using HTTP mode (auto-detected)")
    except Exception as e:
        # HTTP failed, use embedded
        from .store import VectorStore
        def get_connection_mode() -> str:
            return "embedded"
        print(f"[STORE-SELECTOR] Using embedded mode (HTTP unavailable: {e})")
