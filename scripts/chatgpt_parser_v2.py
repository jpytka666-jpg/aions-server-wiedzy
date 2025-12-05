"""
ChatGPT Deep Parser v2
======================
Ulepszona ekstrakcja - szuka konkretnych wzorców konwersacji.
"""

import re
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

INPUT_FILE = Path(r"E:\server wiedzy\chatgpt_extracted\deep\ALL_RAW.txt")
OUTPUT_DIR = Path(r"E:\server wiedzy\chatgpt_extracted")

def extract_conversations():
    """Extract conversation titles and metadata"""
    
    print("Reading raw data...")
    with open(INPUT_FILE, 'r', encoding='utf-8', errors='replace') as f:
        text = f.read()
    
    print(f"Total chars: {len(text)}")
    
    conversations = []
    
    # Pattern 1: conversation items with title
    # "id":"xxx-xxx-xxx","title":"Some Title","created_at":"2025-..."
    pattern1 = r'"id"\s*:\s*"([a-f0-9-]{36})"\s*,\s*"title"\s*:\s*"([^"]*)"'
    for match in re.finditer(pattern1, text):
        conv_id, title = match.groups()
        if title and len(title) > 1:
            conversations.append({
                "id": conv_id,
                "title": title,
                "source": "pattern1"
            })
    
    # Pattern 2: Looking for conversation blocks in cache format
    # "items":[{"id":"xxx","title":"yyy",...}]
    pattern2 = r'"items"\s*:\s*\[(.*?)\]'
    for match in re.finditer(pattern2, text, re.DOTALL):
        items_str = match.group(1)
        # Extract individual items
        item_pattern = r'\{"id"\s*:\s*"([^"]+)"\s*,\s*"title"\s*:\s*"([^"]*)"'
        for item_match in re.finditer(item_pattern, items_str):
            conv_id, title = item_match.groups()
            if title and len(title) > 1 and not any(c["id"] == conv_id for c in conversations):
                conversations.append({
                    "id": conv_id,
                    "title": title,
                    "source": "pattern2"
                })
    
    # Pattern 3: conversation-history entries
    # Szukamy w blokach "pages":[{"items":[...]}]
    page_pattern = r'"pages"\s*:\s*\[\s*\{\s*"items"\s*:\s*\[(.*?)\]\s*\}'
    for match in re.finditer(page_pattern, text, re.DOTALL):
        content = match.group(1)
        # Parse individual conversation entries
        conv_pattern = r'\{"id":"([^"]+)","title":"([^"]*)"(?:,"created_at":"([^"]*)")?'
        for conv_match in re.finditer(conv_pattern, content):
            groups = conv_match.groups()
            conv_id = groups[0]
            title = groups[1]
            created = groups[2] if len(groups) > 2 else None
            
            if title and not any(c["id"] == conv_id for c in conversations):
                conversations.append({
                    "id": conv_id,
                    "title": title,
                    "created_at": created,
                    "source": "pattern3"
                })
    
    # Pattern 4: Any readable title-like strings near UUIDs
    # UUID followed by some text
    uuid_pattern = r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})[^a-zA-Z]*([A-Z][a-zA-Z\s]{5,50})'
    for match in re.finditer(uuid_pattern, text):
        conv_id, title = match.groups()
        title = title.strip()
        if not any(c["id"] == conv_id for c in conversations):
            if re.match(r'^[A-Z][a-zA-Z\s]+$', title):  # Clean title
                conversations.append({
                    "id": conv_id,
                    "title": title,
                    "source": "pattern4"
                })
    
    print(f"\nFound {len(conversations)} conversations")
    
    return conversations

def extract_user_info():
    """Extract user information"""
    
    with open(INPUT_FILE, 'r', encoding='utf-8', errors='replace') as f:
        text = f.read()
    
    user_info = {}
    
    # Display name
    match = re.search(r'"display_name"\s*:\s*"([^"]+)"', text)
    if match:
        user_info["display_name"] = match.group(1)
    
    # User ID
    match = re.search(r'user-([A-Za-z0-9]+)/', text)
    if match:
        user_info["user_id"] = match.group(1)
    
    # Email
    match = re.search(r'"email"\s*:\s*"([^"]+@[^"]+)"', text)
    if match:
        user_info["email"] = match.group(1)
    
    # Organization
    match = re.search(r'"organization_id"\s*:\s*"([^"]+)"', text)
    if match:
        user_info["organization_id"] = match.group(1)
    
    return user_info

def extract_all_readable_titles():
    """Extract ALL things that look like conversation titles"""
    
    with open(INPUT_FILE, 'r', encoding='utf-8', errors='replace') as f:
        text = f.read()
    
    titles = set()
    
    # Look for Polish text (your conversations are likely in Polish/English)
    # Pattern: Capitalized words or Polish words
    title_patterns = [
        r'"title"\s*:\s*"([^"]{3,100})"',
        r'"name"\s*:\s*"([^"]{3,100})"',
        r'"subject"\s*:\s*"([^"]{3,100})"',
    ]
    
    for pattern in title_patterns:
        for match in re.finditer(pattern, text):
            title = match.group(1)
            # Filter out garbage
            if (len(title) > 3 and 
                not title.startswith('{') and 
                not title.startswith('[') and
                not title.startswith('http') and
                re.search(r'[a-zA-Z]{2,}', title)):
                titles.add(title)
    
    return list(titles)

def find_conversation_content():
    """Try to find actual conversation content/messages"""
    
    with open(INPUT_FILE, 'r', encoding='utf-8', errors='replace') as f:
        text = f.read()
    
    messages = []
    
    # Pattern for message parts
    patterns = [
        r'"parts"\s*:\s*\["([^"]{20,500})"',
        r'"content"\s*:\s*"([^"]{20,500})"',
        r'"text"\s*:\s*"([^"]{20,500})"',
        r'"message"\s*:\s*"([^"]{20,500})"',
    ]
    
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            msg = match.group(1)
            if msg and len(msg) > 20:
                # Decode unicode escapes
                try:
                    msg = msg.encode().decode('unicode_escape')
                except:
                    pass
                messages.append(msg)
    
    return list(set(messages))

def main():
    print("="*60)
    print("ChatGPT Deep Parser v2")
    print("="*60)
    
    # Extract conversations
    conversations = extract_conversations()
    
    # Extract user info
    user_info = extract_user_info()
    print(f"\nUser info: {user_info}")
    
    # Extract all titles
    all_titles = extract_all_readable_titles()
    print(f"All readable titles: {len(all_titles)}")
    
    # Find message content
    messages = find_conversation_content()
    print(f"Message fragments: {len(messages)}")
    
    # Save results
    results = {
        "extracted_at": datetime.now().isoformat(),
        "user_info": user_info,
        "conversations": conversations,
        "all_titles": sorted(all_titles),
        "message_fragments": messages[:50]  # Limit
    }
    
    with open(OUTPUT_DIR / "parsed_v2.json", 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Generate readable report
    report = f"""# ChatGPT Deep Extraction v2

**User:** {user_info.get('display_name', 'Unknown')}
**User ID:** {user_info.get('user_id', 'Unknown')}
**Extracted:** {datetime.now().isoformat()}

## Conversations ({len(conversations)})

"""
    for i, conv in enumerate(conversations, 1):
        report += f"{i}. **{conv['title']}** (ID: {conv['id'][:8]}...)\n"
    
    report += f"\n## All Titles Found ({len(all_titles)})\n\n"
    for title in sorted(all_titles)[:100]:
        report += f"- {title}\n"
    
    report += f"\n## Message Fragments ({len(messages)})\n\n"
    for i, msg in enumerate(messages[:30], 1):
        # Truncate for readability
        msg_short = msg[:200] + "..." if len(msg) > 200 else msg
        report += f"**[{i}]** {msg_short}\n\n"
    
    with open(OUTPUT_DIR / "REPORT_v2.md", 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n[SAVED]")
    print(f"  {OUTPUT_DIR / 'parsed_v2.json'}")
    print(f"  {OUTPUT_DIR / 'REPORT_v2.md'}")

if __name__ == "__main__":
    main()
