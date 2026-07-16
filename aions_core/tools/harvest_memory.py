import json
import os
import shutil
from pathlib import Path

def harvest_memory():
    # Target directory
    target_dir = Path(r"E:\server wiedzy\aions_core\memory\chunks")
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Source directories (Updated with MFT findings)
    source_paths = [
        r"C:\Users\User\ContextVault\memory\chunks",
        r"C:\Users\User\OneDrive - Global Banking School\Desktop\AIONS_CBMS_RELEASE_V3\memory\chunks",
        r"C:\Users\User\OneDrive - Global Banking School\Desktop\AIONS_TEXTY_DLA_TEPYCH_AJAJ\AIONS_CBMS_RELEASE_V3\memory\chunks",
        r"C:\Users\User\OneDrive - Global Banking School\Desktop\MAPA_LASU_SOLO_CBMS\AIONS_CBMS_RELEASE\memory\chunks",
        r"E:\AI_WORKSPACE\MASTER_CLEAN\AIONS_CORE\AIONS_V10\AIONS_CBMS_RELEASE_V3\memory\chunks"
    ]

    print("Starting Phase 2 Memory Harvest (C: Drive)...")
    
    total_processed = 0
    new_chunks = 0
    updated_chunks = 0
    
    for src in source_paths:
        src_path = Path(src)
        if not src_path.exists():
            print(f"Skipping missing path: {src}")
            continue
            
        print(f"Scanning: {src}")
        try:
            for file in src_path.glob("*.json"):
                total_processed += 1
                dest_file = target_dir / file.name
                
                should_copy = False
                if not dest_file.exists():
                    should_copy = True
                    new_chunks += 1
                else:
                    # If exists, take the larger one (more info)
                    if file.stat().st_size > dest_file.stat().st_size:
                        should_copy = True
                        updated_chunks += 1
                
                if should_copy:
                    try:
                        shutil.copy2(file, dest_file)
                    except Exception as e:
                        print(f"Failed to copy {file.name}: {e}")
        except Exception as e:
            print(f"Error accessing {src}: {e}")

    print("="*40)
    print(f"Harvest Complete.")
    print(f"Scanned chunks: {total_processed}")
    print(f"New chunks added: {new_chunks}")
    print(f"Chunks updated (better version): {updated_chunks}")
    print(f"Total chunks in library: {len(list(target_dir.glob('*.json')))}")
    print("="*40)

if __name__ == "__main__":
    harvest_memory()
