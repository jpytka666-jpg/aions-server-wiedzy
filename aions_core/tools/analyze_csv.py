import csv
import os
from collections import defaultdict

def analyze_csv():
    csv_path = r"E:\server wiedzy\FULL_SCAN_20251128_114059\everything_full.csv"
    
    print(f"Analyzing {csv_path}...")
    
    chunk_counts = defaultdict(int)
    critical_files = {
        'crla_core.py': [],
        'pocket_qc.py': [],
        'plasters_loader.py': [],
        'AIONS_ULTIMATE_UNIFIED.py': [],
        'knowledge_manifest.json': []
    }
    
    try:
        with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
            # csv reader handles quotes
            reader = csv.reader(f)
            headers = next(reader) # skip header
            
            for i, row in enumerate(reader):
                if not row: continue
                path = row[0]
                
                # Check for chunks
                if ".json" in path and "chunks" in path:
                    # Get parent dir
                    parent = os.path.dirname(path)
                    chunk_counts[parent] += 1
                
                # Check for critical files
                basename = os.path.basename(path)
                if basename in critical_files:
                    critical_files[basename].append(path)
                    
                if i % 100000 == 0:
                    print(f"Processed {i} lines...")

    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    print("\n" + "="*50)
    print("TOP CHUNK LOCATIONS:")
    print("="*50)
    # Sort by count desc
    sorted_chunks = sorted(chunk_counts.items(), key=lambda x: x[1], reverse=True)
    for path, count in sorted_chunks[:20]:
        print(f"Count: {count:<6} | Path: {path}")

    print("\n" + "="*50)
    print("CRITICAL FILE LOCATIONS:")
    print("="*50)
    for filename, paths in critical_files.items():
        print(f"\n[{filename}] ({len(paths)} found):")
        for p in paths[:5]: # limit output
            print(f"  - {p}")

if __name__ == "__main__":
    analyze_csv()
