
import os
import json
import time
import sys
from pathlib import Path
from tqdm import tqdm

# Ensure we can import core modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from aions_vector_enhancement import VectorEnhancement

def ingest_chunks():
    print("🚀 Starting Big Data Ingestion into LanceDB...")
    
    # 1. Initialize Vector DB
    vector_db = VectorEnhancement()
    if not vector_db.connected:
        print("❌ Failed to connect to Vector DB. Aborting.")
        return

    # 2. Locate Chunks
    chunks_dir = Path(r"E:\AI_WORKSPACE\MASTER_CLEAN_SNAPSHOT\AIONS_CORE\AIONS_V10\AIONS_CBMS_RELEASE_V3\memory\chunks")
    if not chunks_dir.exists():
        print(f"❌ Chunks directory not found at {chunks_dir}")
        return

    print(f"📂 Scanning {chunks_dir}...")
    files = list(chunks_dir.glob("*.json"))
    print(f"📦 Found {len(files)} JSON chunks to process.")

    # 3. Batch Process
    batch_size = 100
    texts = []
    metadatas = []
    ids = []
    
    # Check for embedding capability
    try:
        from sentence_transformers import SentenceTransformer
        # Load the EXACT model matching the table name for compatibility
        # Table: ...all-MiniLM-L6-v2...
        print("🧠 Loading embedding model 'all-MiniLM-L6-v2'...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Model loaded.")
    except ImportError:
        print("❌ sentence_transformers not installed. Install it first.")
        return
    except Exception as e:
        print(f"❌ Failed to load embedding model: {e}")
        return

    print("⚡ Beginning ingestion...")
    count = 0
    start_time = time.time()

    for file_path in tqdm(files, desc="Ingesting"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract content - normalize standard CBMS formats
            content = data.get('content') or data.get('text') or data.get('body')
            if not content:
                # Fallback: maybe it's a list or other structure?
                continue
                
            chunk_id = data.get('id', file_path.stem)
            
            texts.append(content)
            metadatas.append({"source": str(file_path), "id": chunk_id, "type": "chunk"})
            ids.append(chunk_id)
            
            if len(texts) >= batch_size:
                # Generate Embeddings
                embeddings = model.encode(texts)
                
                # Format for LanceDB: Match existing schema
                # Schema: path, cachekey, uuid, vector, startLine, endLine, contents
                to_add = []
                for i in range(len(texts)):
                    to_add.append({
                        "vector": embeddings[i],
                        "contents": texts[i],
                        "path": metadatas[i]["source"],
                        "uuid": str(ids[i]),
                        "cachekey": str(ids[i]),
                        "startLine": 0.0,
                        "endLine": 0.0
                    })
                
                # Add to Table
                vector_db.table.add(to_add)
                
                count += len(texts)
                texts = []
                metadatas = []
                ids = []
                
        except Exception as e:
            print(f"⚠ Error processing {file_path.name}: {e}")
            continue

    # Final batch
    if texts:
        embeddings = model.encode(texts)
        to_add = []
        for i in range(len(texts)):
             to_add.append({
                "vector": embeddings[i],
                "contents": texts[i],
                "path": metadatas[i]["source"],
                "uuid": str(ids[i]),
                "cachekey": str(ids[i]),
                "startLine": 0.0,
                "endLine": 0.0
            })
        vector_db.table.add(to_add)
        count += len(texts)

    duration = time.time() - start_time
    print(f"✅ Ingestion Complete!")
    print(f"📊 Processed {count} chunks in {duration:.2f} seconds.")
    print(f"🚀 Speed: {count / duration:.2f} chunks/sec")

if __name__ == "__main__":
    ingest_chunks()
