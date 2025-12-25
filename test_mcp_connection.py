import sys
import os

# Add paths
sys.path.insert(0, r"E:\server wiedzy")
sys.path.insert(0, r"E:\server wiedzy\server")
sys.path.insert(0, r"E:\server wiedzy\mcpServers\VS_CODE_MCP_CODEX")

os.chdir(r"E:\server wiedzy")

print("=" * 50)
print("AIONS MCP SERVER TEST")
print("=" * 50)
print(f"Python: {sys.version}")
print(f"CWD: {os.getcwd()}")

# Test imports
try:
    from src.server import mcp_server, log
    print(f"\n✅ Server imported OK")
    print(f"   Tools count: {len(mcp_server._tools)}")
    print(f"   Tool names: {list(mcp_server._tools.keys())[:10]}...")
except Exception as e:
    print(f"\n❌ Server import FAILED: {e}")

# Test ChromaDB
try:
    import chromadb
    client = chromadb.PersistentClient(path=r"E:\server wiedzy\data\chroma")
    collections = client.list_collections()
    print(f"\n✅ ChromaDB OK")
    print(f"   Collections: {len(collections)}")
except Exception as e:
    print(f"\n❌ ChromaDB FAILED: {e}")

# Test Everything CLI
from pathlib import Path
everything = Path(r"C:\Program Files\Everything\es.exe")
print(f"\n{'✅' if everything.exists() else '❌'} Everything CLI: {everything.exists()}")

print("\n" + "=" * 50)
print("TEST COMPLETE")
print("=" * 50)
