from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import sys

# Force Offline Mode for Transformers
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

# Add local path to sys.path to find modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Suppress warnings and logs during import
import warnings
warnings.filterwarnings("ignore")

try:
    from unified_core import AIONSv2
    print("SUCCESS: Imported AIONSv2 from unified_core")
except ImportError as e:
    print(f"IMPORT ERROR: Could not import AIONSv2: {e}")
    # Fallback to local dir
    sys.path.append(os.getcwd())
    try:
        from unified_core import AIONSv2
        print("SUCCESS: Imported AIONSv2 after sys.path append")
    except ImportError as e2:
         print(f"FATAL IMPORT ERROR: {e2}")
         raise

app = FastAPI(title="AIONS Kernel API", version="4.0 (Fusion)")

# Global instance
print("Initializing AIONS Fusion Core...")
try:
    # Initialize with all Phase 4 components enabled
    aions = AIONSv2(
        enable_vector=True,
        enable_hybrid=True,
        enable_agent=True,
        enable_style=True,
        enable_monitoring=True
    )
    # Run a quick health check on startup
    health = aions.health_check()
    print(f"Fusion Core Status: {health.get('status', 'unknown')}")
except Exception as e:
    print(f"CRITICAL ERROR INIT FUSION CORE: {e}")
    aions = None

class QueryRequest(BaseModel):
    query: str

@app.post("/query")
async def query_endpoint(req: QueryRequest):
    if not aions:
        raise HTTPException(status_code=503, detail="AIONS Kernel not initialized")
    try:
        # Phase 4: Use 'process' method of unified core
        response = aions.process(req.query)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def status_endpoint():
    if not aions:
        return {"status": "error", "detail": "Kernel failed to load"}
    return aions.health_check()

@app.get("/")
async def root():
    if not aions:
        return {"status": "error"}
    return {"status": "online", "system": "AIONS Fusion Core", "version": "4.0"}
