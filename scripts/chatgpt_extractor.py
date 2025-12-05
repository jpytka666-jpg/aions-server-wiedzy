"""
ChatGPT Conversation Extractor
==============================
Wyciąga rozmowy z ChatGPT Desktop App cache.
Parsuje LevelDB i IndexedDB, zapisuje do czytelnego formatu.

Autor: AIONS Project
"""

import os
import re
import json
import struct
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import hashlib

# =============================================================================
# CONFIG
# =============================================================================

CHATGPT_CACHE = Path(r"C:\Users\User\AppData\Local\Packages\OpenAI.ChatGPT-Desktop_2p2nqsd0c76g0\LocalCache\Roaming\ChatGPT")
OUTPUT_DIR = Path(r"E:\server wiedzy\chatgpt_extracted")

# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class Conversation:
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: List[Dict] = None
    raw_data: str = ""
    
    def __post_init__(self):
        if self.messages is None:
            self.messages = []

@dataclass
class ExtractionResult:
    timestamp: str
    conversations: List[Conversation]
    custom_gpts: List[Dict]
    user_info: Dict
    raw_chunks: List[str]
    errors: List[str]

# =============================================================================
# LEVELDB PARSER (simplified - reads raw binary)
# =============================================================================

def extract_json_objects(data: bytes) -> List[Dict]:
    """Extract JSON objects from binary data"""
    results = []
    text = data.decode('utf-8', errors='ignore')
    
    # Find all JSON-like structures
    # Pattern for conversation objects
    patterns = [
        r'\{"value":\s*\{[^}]+\}[^}]*\}',
        r'\{"id":\s*"[^"]+",\s*"title":\s*"[^"]*"[^}]*\}',
        r'\{"gizmos?":\s*\[[^\]]*\]\}',
    ]
    
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.DOTALL):
            try:
                # Try to parse as JSON
                json_str = match.group()
                # Fix common issues
                json_str = re.sub(r',\s*}', '}', json_str)
                json_str = re.sub(r',\s*]', ']', json_str)
                obj = json.loads(json_str)
                results.append(obj)
            except:
                pass
    
    return results

def extract_conversations_from_text(text: str) -> List[Dict]:
    """Extract conversation metadata from raw text"""
    conversations = []
    
    # Pattern for conversation items in cache
    # Looking for: "id":"xxx","title":"yyy","created_at":"zzz"
    conv_pattern = r'"id"\s*:\s*"([a-f0-9-]+)"[^}]*"title"\s*:\s*"([^"]*)"[^}]*"created_at"\s*:\s*"([^"]*)"'
    
    for match in re.finditer(conv_pattern, text, re.IGNORECASE):
        conv_id, title, created = match.groups()
        conversations.append({
            "id": conv_id,
            "title": title,
            "created_at": created
        })
    
    # Also try simpler pattern
    simple_pattern = r'"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})"\s*,\s*"([^"]+)"'
    for match in re.finditer(simple_pattern, text):
        conv_id, title = match.groups()
        if not any(c["id"] == conv_id for c in conversations):
            conversations.append({"id": conv_id, "title": title})
    
    return conversations

def extract_readable_strings(data: bytes, min_length: int = 10) -> List[str]:
    """Extract readable strings from binary data"""
    text = data.decode('utf-8', errors='ignore')
    
    # Split by null bytes and other control chars
    chunks = re.split(r'[\x00-\x1f]+', text)
    
    # Filter readable chunks
    readable = []
    for chunk in chunks:
        chunk = chunk.strip()
        if len(chunk) >= min_length:
            # Must have some letters
            if re.search(r'[a-zA-Z]{3,}', chunk):
                readable.append(chunk)
    
    return readable

def parse_ldb_file(filepath: Path) -> Dict[str, Any]:
    """Parse a single LevelDB file"""
    result = {
        "file": str(filepath),
        "size": filepath.stat().st_size,
        "conversations": [],
        "json_objects": [],
        "readable_chunks": [],
        "raw_text": ""
    }
    
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        
        # Extract readable text
        result["raw_text"] = data.decode('utf-8', errors='ignore')
        
        # Extract JSON objects
        result["json_objects"] = extract_json_objects(data)
        
        # Extract conversation metadata
        result["conversations"] = extract_conversations_from_text(result["raw_text"])
        
        # Extract readable chunks
        result["readable_chunks"] = extract_readable_strings(data, 20)
        
    except Exception as e:
        result["error"] = str(e)
    
    return result

# =============================================================================
# MAIN EXTRACTOR
# =============================================================================

def extract_all() -> ExtractionResult:
    """Extract all ChatGPT data"""
    
    print("="*60)
    print("ChatGPT Conversation Extractor")
    print("="*60)
    
    result = ExtractionResult(
        timestamp=datetime.now().isoformat(),
        conversations=[],
        custom_gpts=[],
        user_info={},
        raw_chunks=[],
        errors=[]
    )
    
    # Find all LevelDB files
    local_storage = CHATGPT_CACHE / "Local Storage" / "leveldb"
    indexed_db = CHATGPT_CACHE / "IndexedDB" / "https_chatgpt.com_0.indexeddb.leveldb"
    
    all_conversations = {}
    all_gpts = []
    
    for db_path in [local_storage, indexed_db]:
        if not db_path.exists():
            print(f"[SKIP] {db_path} not found")
            continue
        
        print(f"\n[SCANNING] {db_path}")
        
        for file in db_path.iterdir():
            if file.suffix in ['.ldb', '.log']:
                print(f"  Parsing: {file.name} ({file.stat().st_size} bytes)")
                
                parsed = parse_ldb_file(file)
                
                # Collect conversations
                for conv in parsed.get("conversations", []):
                    conv_id = conv.get("id", "")
                    if conv_id and conv_id not in all_conversations:
                        all_conversations[conv_id] = conv
                
                # Collect JSON objects
                for obj in parsed.get("json_objects", []):
                    if "gizmos" in obj or "gizmo" in obj:
                        all_gpts.append(obj)
                
                # Collect readable chunks
                for chunk in parsed.get("readable_chunks", []):
                    if chunk not in result.raw_chunks:
                        result.raw_chunks.append(chunk)
                
                if "error" in parsed:
                    result.errors.append(f"{file.name}: {parsed['error']}")
    
    # Build conversation objects
    for conv_id, conv_data in all_conversations.items():
        result.conversations.append(Conversation(
            id=conv_id,
            title=conv_data.get("title", "Unknown"),
            created_at=conv_data.get("created_at", ""),
            updated_at=conv_data.get("updated_at", ""),
            raw_data=json.dumps(conv_data)
        ))
    
    result.custom_gpts = all_gpts
    
    # Sort by created_at if available
    result.conversations.sort(key=lambda x: x.created_at if x.created_at else "", reverse=True)
    
    print(f"\n[RESULTS]")
    print(f"  Conversations: {len(result.conversations)}")
    print(f"  Custom GPTs: {len(result.custom_gpts)}")
    print(f"  Raw chunks: {len(result.raw_chunks)}")
    print(f"  Errors: {len(result.errors)}")
    
    return result

def save_results(result: ExtractionResult):
    """Save extraction results"""
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save summary
    summary = {
        "timestamp": result.timestamp,
        "conversation_count": len(result.conversations),
        "custom_gpt_count": len(result.custom_gpts),
        "conversations": [asdict(c) for c in result.conversations],
        "custom_gpts": result.custom_gpts,
        "errors": result.errors
    }
    
    with open(OUTPUT_DIR / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    # Save readable chunks
    with open(OUTPUT_DIR / "raw_chunks.txt", "w", encoding="utf-8") as f:
        for i, chunk in enumerate(result.raw_chunks):
            f.write(f"[{i}] {chunk}\n\n")
    
    # Save markdown report
    report = f"""# ChatGPT Extraction Report

**Extracted:** {result.timestamp}

## Conversations ({len(result.conversations)})

| # | Title | Created |
|---|-------|---------|
"""
    for i, conv in enumerate(result.conversations[:100], 1):
        title = conv.title[:50] + "..." if len(conv.title) > 50 else conv.title
        created = conv.created_at[:10] if conv.created_at else "?"
        report += f"| {i} | {title} | {created} |\n"
    
    report += f"\n## Custom GPTs ({len(result.custom_gpts)})\n\n"
    for gpt in result.custom_gpts[:20]:
        if isinstance(gpt, dict):
            report += f"- {json.dumps(gpt)[:200]}...\n"
    
    report += f"\n## Errors ({len(result.errors)})\n\n"
    for err in result.errors:
        report += f"- {err}\n"
    
    with open(OUTPUT_DIR / "REPORT.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n[SAVED]")
    print(f"  {OUTPUT_DIR / 'summary.json'}")
    print(f"  {OUTPUT_DIR / 'raw_chunks.txt'}")
    print(f"  {OUTPUT_DIR / 'REPORT.md'}")

def extract_deep_content():
    """Deep extraction - try to get actual message content"""
    
    print("\n" + "="*60)
    print("DEEP CONTENT EXTRACTION")
    print("="*60)
    
    deep_dir = OUTPUT_DIR / "deep"
    deep_dir.mkdir(parents=True, exist_ok=True)
    
    # Read all LDB files and dump raw
    local_storage = CHATGPT_CACHE / "Local Storage" / "leveldb"
    indexed_db = CHATGPT_CACHE / "IndexedDB" / "https_chatgpt.com_0.indexeddb.leveldb"
    
    all_text = []
    
    for db_path in [local_storage, indexed_db]:
        if not db_path.exists():
            continue
        
        for file in db_path.iterdir():
            if file.suffix in ['.ldb', '.log']:
                try:
                    with open(file, 'rb') as f:
                        data = f.read()
                    
                    text = data.decode('utf-8', errors='replace')
                    
                    # Save individual file
                    out_file = deep_dir / f"{file.parent.parent.name}_{file.name}.txt"
                    with open(out_file, 'w', encoding='utf-8') as f:
                        f.write(text)
                    
                    all_text.append(f"\n\n===== {file} =====\n\n{text}")
                    
                except Exception as e:
                    print(f"  Error: {file.name}: {e}")
    
    # Save combined
    with open(deep_dir / "ALL_RAW.txt", 'w', encoding='utf-8') as f:
        f.write("".join(all_text))
    
    print(f"\n[DEEP SAVED] {deep_dir}")
    
    # Try to extract message patterns
    combined = "".join(all_text)
    
    # Look for message-like patterns
    message_patterns = [
        r'"content":\s*\{[^}]*"parts":\s*\["([^"]+)"\]',
        r'"text":\s*"([^"]{50,})"',
        r'"message":\s*"([^"]{50,})"',
    ]
    
    messages = []
    for pattern in message_patterns:
        for match in re.finditer(pattern, combined):
            msg = match.group(1)
            if len(msg) > 30 and msg not in messages:
                messages.append(msg)
    
    if messages:
        with open(deep_dir / "extracted_messages.txt", 'w', encoding='utf-8') as f:
            for i, msg in enumerate(messages):
                f.write(f"\n[MSG {i}]\n{msg}\n")
        print(f"  Extracted {len(messages)} message fragments")

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Starting ChatGPT Data Extraction...")
    print("="*60 + "\n")
    
    # Basic extraction
    result = extract_all()
    save_results(result)
    
    # Deep extraction
    extract_deep_content()
    
    print("\n" + "="*60)
    print("EXTRACTION COMPLETE!")
    print(f"Results saved to: {OUTPUT_DIR}")
    print("="*60)
