"""
ChatGPT ULTIMATE Extractor v3
=============================
Wyciąga WSZYSTKO z cache ChatGPT Desktop.
"""

import re
import json
from pathlib import Path
from datetime import datetime

INPUT_FILE = Path(r"E:\server wiedzy\chatgpt_extracted\deep\Local Storage_002374.ldb.txt")
OUTPUT_DIR = Path(r"E:\server wiedzy\chatgpt_extracted")

def clean_text(text):
    """Remove control chars and clean up spaced text"""
    # Remove null bytes and control chars
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    # Fix spaced out text like "C V   d l a   R e t a i l"
    # If we see single chars separated by spaces, join them
    text = re.sub(r'(?<=\w) (?=\w(?:\s\w)*(?:\s|$))', '', text)
    return text

def extract_all_data(text):
    """Extract all valuable data"""
    
    results = {
        "user_info": {},
        "conversations": [],
        "custom_gpts": [],
        "drafts": [],
        "stats": {},
        "model_info": {},
        "raw_titles": []
    }
    
    # Clean the text first
    cleaned = clean_text(text)
    
    # === USER INFO ===
    
    # Email
    emails = re.findall(r'[\w.-]+@[\w.-]+\.\w+', text)
    if emails:
        results["user_info"]["emails"] = list(set(emails))
    
    # Display name
    match = re.search(r'"display_name"\s*:\s*"([^"]+)"', text)
    if match:
        results["user_info"]["display_name"] = match.group(1)
    
    # User ID
    match = re.search(r'user-([A-Za-z0-9]{20,})', text)
    if match:
        results["user_info"]["user_id"] = match.group(1)
    
    # Message count
    match = re.search(r'loggedInUserMessageCount[^\d]*(\d+)', text)
    if match:
        results["stats"]["total_messages"] = int(match.group(1))
    
    # === CONVERSATION TITLES ===
    
    # Pattern: UUID followed by title in quotes
    # Looking in cleaned text for better parsing
    title_pattern = r'"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})"\s*,\s*"([^"]{2,100})"'
    for match in re.finditer(title_pattern, cleaned):
        conv_id, title = match.groups()
        if not title.startswith('{') and not title.startswith('http'):
            results["conversations"].append({
                "id": conv_id,
                "title": title
            })
    
    # Alternative: Look for "title":"xxx" patterns
    title_pattern2 = r'"title"\s*:\s*"([^"]{3,100})"'
    for match in re.finditer(title_pattern2, text):
        title = match.group(1)
        if title and not title.startswith('{'):
            if title not in results["raw_titles"]:
                results["raw_titles"].append(title)
    
    # === CONVERSATION HISTORY BLOCK ===
    
    # Find conversation-history JSON block
    history_match = re.search(r'conversation-history.*?"items"\s*:\s*\[(.*?)\]', text, re.DOTALL)
    if history_match:
        items_text = history_match.group(1)
        
        # Extract each conversation item
        # Pattern: "id":"xxx","title":"yyy"
        conv_pattern = r'"id"\s*:\s*"([^"]+)"\s*,\s*"t[^"]*"\s*:\s*"([^"]*)"'
        for m in re.finditer(conv_pattern, items_text):
            conv_id, title = m.groups()
            # Decode spaced text
            title = clean_text(title)
            if title and len(title) > 1:
                existing = [c["id"] for c in results["conversations"]]
                if conv_id not in existing:
                    results["conversations"].append({
                        "id": conv_id,
                        "title": title
                    })
    
    # === CUSTOM GPTS ===
    
    # Find gizmo definitions
    gizmo_pattern = r'"gizmo"\s*:\s*\{[^}]*"id"\s*:\s*"([^"]+)"[^}]*"short_url"\s*:\s*"([^"]*)"'
    for match in re.finditer(gizmo_pattern, text, re.DOTALL):
        gpt_id, short_url = match.groups()
        results["custom_gpts"].append({
            "id": gpt_id,
            "short_url": short_url
        })
    
    # === DRAFTS ===
    
    # Find draft messages
    draft_pattern = r'"drafts"\s*:\s*\[(.*?)\]'
    draft_match = re.search(draft_pattern, text, re.DOTALL)
    if draft_match:
        drafts_text = draft_match.group(1)
        
        # Extract content
        content_pattern = r'"content"\s*[^"]*"([^"]{10,})"'
        for m in re.finditer(content_pattern, drafts_text):
            content = clean_text(m.group(1))
            if content:
                results["drafts"].append(content)
    
    # === MODEL INFO ===
    
    # GPT-5 references
    if 'gpt-5' in text.lower():
        results["model_info"]["has_gpt5_access"] = True
    
    # Context budget
    match = re.search(r'"budget"\s*:\s*(\d+)', text)
    if match:
        results["model_info"]["context_budget"] = int(match.group(1))
    
    # Memory settings
    if '"memory_enabled"' in text:
        results["model_info"]["memory_enabled"] = True
    
    return results

def extract_spaced_titles(text):
    """Extract titles that are space-separated (like 'C V   d l a   R e t a i l')"""
    
    titles = []
    
    # Find patterns like: letter space letter space letter...
    # These are the actual conversation titles encoded weirdly
    
    # Look for sequences after UUID patterns
    pattern = r'([a-f0-9-]{36})[^a-zA-Z]*([A-Z][a-zA-Z\s]{10,100})'
    for match in re.finditer(pattern, text):
        uuid, title_raw = match.groups()
        # Check if it looks like spaced text
        if re.match(r'^[A-Z]([ ][a-zA-Z])+', title_raw):
            # It's spaced - join it
            title = title_raw.replace(' ', '')
        else:
            title = title_raw.strip()
        
        if len(title) > 3:
            titles.append({
                "id": uuid,
                "title": title
            })
    
    return titles

def main():
    print("="*60)
    print("ChatGPT ULTIMATE Extractor v3")
    print("="*60)
    
    # Read all ldb files
    all_text = ""
    ldb_dir = OUTPUT_DIR / "deep"
    
    for file in ldb_dir.glob("*.txt"):
        if "RAW" not in file.name:
            print(f"Reading: {file.name}")
            with open(file, 'r', encoding='utf-8', errors='replace') as f:
                all_text += f.read() + "\n\n"
    
    print(f"Total chars: {len(all_text)}")
    
    # Extract everything
    results = extract_all_data(all_text)
    
    # Also try spaced title extraction
    spaced_titles = extract_spaced_titles(all_text)
    results["spaced_titles"] = spaced_titles
    
    # Print summary
    print(f"\n=== RESULTS ===")
    print(f"User Info: {results['user_info']}")
    print(f"Stats: {results['stats']}")
    print(f"Conversations: {len(results['conversations'])}")
    print(f"Raw Titles: {len(results['raw_titles'])}")
    print(f"Custom GPTs: {len(results['custom_gpts'])}")
    print(f"Drafts: {len(results['drafts'])}")
    print(f"Model Info: {results['model_info']}")
    
    # Save results
    with open(OUTPUT_DIR / "ULTIMATE_EXTRACT.json", 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Generate markdown report
    report = f"""# ChatGPT Ultimate Extraction

**Extracted:** {datetime.now().isoformat()}

## User Info

| Field | Value |
|-------|-------|
| Display Name | {results['user_info'].get('display_name', '?')} |
| Emails | {', '.join(results['user_info'].get('emails', []))} |
| User ID | {results['user_info'].get('user_id', '?')} |
| Total Messages | {results['stats'].get('total_messages', '?')} |

## Model Access

| Feature | Value |
|---------|-------|
| GPT-5 Access | {results['model_info'].get('has_gpt5_access', False)} |
| Context Budget | {results['model_info'].get('context_budget', '?')} tokens |
| Memory | {results['model_info'].get('memory_enabled', '?')} |

## Conversations ({len(results['conversations'])})

"""
    for i, conv in enumerate(results['conversations'][:50], 1):
        report += f"{i}. **{conv['title']}** (ID: `{conv['id'][:8]}...`)\n"
    
    report += f"\n## Raw Titles Found ({len(results['raw_titles'])})\n\n"
    for title in results['raw_titles'][:100]:
        report += f"- {title}\n"
    
    report += f"\n## Custom GPTs ({len(results['custom_gpts'])})\n\n"
    for gpt in results['custom_gpts']:
        report += f"- **{gpt.get('short_url', gpt['id'])}** (ID: `{gpt['id'][:20]}...`)\n"
    
    if results['drafts']:
        report += f"\n## Drafts ({len(results['drafts'])})\n\n"
        for i, draft in enumerate(results['drafts'], 1):
            draft_short = draft[:300] + "..." if len(draft) > 300 else draft
            report += f"**Draft {i}:**\n```\n{draft_short}\n```\n\n"
    
    with open(OUTPUT_DIR / "ULTIMATE_REPORT.md", 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n[SAVED]")
    print(f"  {OUTPUT_DIR / 'ULTIMATE_EXTRACT.json'}")
    print(f"  {OUTPUT_DIR / 'ULTIMATE_REPORT.md'}")
    
    # Also print the most interesting findings
    print(f"\n=== HIGHLIGHTS ===")
    print(f"Emails: {results['user_info'].get('emails', [])}")
    print(f"Messages sent: {results['stats'].get('total_messages', '?')}")
    print(f"\nSome conversation titles:")
    for title in results['raw_titles'][:20]:
        print(f"  - {title}")

if __name__ == "__main__":
    main()
