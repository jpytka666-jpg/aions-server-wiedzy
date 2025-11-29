# 📑 INDICES - Indeksy CBMS

## Główne indeksy

### 1. CBMS_INDEX_FULL (GŁÓWNY)
- **Docs**: 6,819
- **Rozmiar**: 4.7 MB
- **Ścieżka**: `E:\AI_WORKSPACE\MASTER_CLEAN\CBMS\CBMS_INDEX_FULL\kr_meta.json`
- **Backup**: `E:\AI_WORKSPACE\MASTER_CLEAN_SNAPSHOT\CBMS\CBMS_INDEX_FULL\`

### 2. CBMS_INDEX_KOREAN
- **Korean syllables**: 8,042
- **Compression ratio**: 36:1
- **Ścieżka**: `E:\AI_WORKSPACE\MASTER_CLEAN\CBMS_KR\CBMS_INDEX_KOREAN\kr_meta.json`

### 3. CBMS_INDEX (basic)
- **Ścieżka**: `E:\AI_WORKSPACE\MASTER_CLEAN\CBMS\CBMS_INDEX\kr_meta.json`

## Knowledge Manifests

| Lokalizacja | Rozmiar |
|-------------|---------|
| `C:\Users\User\ContextVault\memory\knowledge_manifest.json` | ~10 MB |
| `C:\Users\User\OneDrive...\AIONS_CBMS_RELEASE_V3\memory\knowledge_manifest.json` | ~10 MB |
| `E:\AI_WORKSPACE\MASTER_CLEAN\AIONS_CORE\...\knowledge_manifest.json` | varies |

## Struktura kr_meta.json

```json
{
  "version": "korean-cbms-1.0",
  "korean_syllables_used": 8042,
  "compression_ratio": 36.0,
  "docs": [
    {
      "doc_id": "가",           // Korean syllable ID
      "original_id": "F2C8B5288A83F",
      "chunk_id": "K05EFF163EF91",
      "title": "...",
      "text": "...",
      "source": "facts.jsonl"
    }
  ]
}
```

## Użycie

```python
import json
with open('kr_meta.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    print(f"Docs: {len(data['docs'])}")
    print(f"Korean syllables: {data.get('korean_syllables_used', 0)}")
```
