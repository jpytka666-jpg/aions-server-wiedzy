import json
import os
import hashlib
from datetime import datetime
from pathlib import Path

def rebuild_manifest():
    root_dir = Path(__file__).parent.parent
    memory_dir = root_dir / "memory"
    chunks_dir = memory_dir / "chunks"
    manifest_file = memory_dir / "knowledge_manifest.json"

    print(f"Scanning chunks in: {chunks_dir}")
    
    # Load or init manifest
    if manifest_file.exists():
        with open(manifest_file, 'r', encoding='utf-8') as f:
            try:
                manifest = json.load(f)
            except:
                manifest = {}
    else:
        manifest = {}

    # Reset maps for clean rebuild provided we trust disk
    manifest["version"] = "1.0"
    manifest["created"] = datetime.now().isoformat()
    manifest["chunk_index"] = {}
    manifest["concept_map"] = {}
    manifest["thinking_sessions"] = manifest.get("thinking_sessions", [])
    
    files = list(chunks_dir.glob("*.json"))
    print(f"Found {len(files)} chunk files on disk.")

    count = 0
    for p in files:
        try:
            with open(p, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            chunk_id = data.get("id")
            if not chunk_id:
                # Infer from filename
                chunk_id = p.stem
            
            concept = data.get("concept", "general")
            content = data.get("content", "")
            
            # Update Chunk Index
            manifest["chunk_index"][chunk_id] = {
                "concept": concept,
                "size": len(content),
                "created": data.get("created", datetime.now().isoformat()),
                "file": str(p)
            }

            # Update Concept Map
            if concept not in manifest["concept_map"]:
                manifest["concept_map"][concept] = []
            if chunk_id not in manifest["concept_map"][concept]:
                manifest["concept_map"][concept].append(chunk_id)
            
            count += 1
            if count % 200 == 0:
                print(f"Processed {count} chunks...")

        except Exception as e:
            print(f"Error processing {p.name}: {e}")

    manifest["total_chunks"] = count
    
    print(f"Saving manifest with {count} chunks...")
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print("Done.")

if __name__ == "__main__":
    rebuild_manifest()
