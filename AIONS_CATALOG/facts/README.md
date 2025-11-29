# 📋 FACTS - Bazy faktów CBMS

## Główne bazy faktów

### 1. ContextVault facts.jsonl (GŁÓWNA)
- **Linie**: 7,895
- **Rozmiar**: 7.2 MB
- **Ścieżka**: `C:\Users\User\ContextVault\memory\facts.jsonl`

### 2. AIONS V3 facts.jsonl
- **Ścieżka**: `C:\Users\User\OneDrive...\AIONS_CBMS_RELEASE_V3\memory\facts.jsonl`

### 3. CBMS_SEED facts.jsonl
- **Ścieżka**: `E:\AJAJAJ\CBMS_SEED\facts.jsonl`
- **Status**: Template (1 linia)

## Knowledge Manifests

| Lokalizacja | Fakty | Rozmiar |
|-------------|-------|---------|
| ContextVault | 33,945+ | ~10 MB |
| AIONS V3 | 33,945+ | ~10 MB |
| AIONS V0-V2 | varies | - |

## Format facts.jsonl

```jsonl
{"id": "F2C8B5288A83F", "content": "...", "chunk_ref": "K05EFF163EF91", "source": "manual"}
{"id": "FDE58CCB67A62", "content": "...", "chunk_ref": "K05EFF163EF91", "source": "auto"}
```

## Format knowledge_manifest.json

```json
{
  "chunks": {
    "K09AE8C11E0C6": {
      "concept": "thinking_pattern",
      "content": "ANALYTICAL_BREAKDOWN...",
      "references": []
    }
  },
  "concept_map": {
    "machine_learning": ["K0FFFE109954D", "K852203B72973"],
    "web_development": ["KC09D82ED999A"]
  },
  "metadata": {
    "total_facts": 33945,
    "last_updated": "2025-10-28"
  }
}
```

## Typy faktów

| Typ | Opis | Przykład |
|-----|------|----------|
| Domain knowledge | Wiedza specjalistyczna | ML, Python, Web Dev |
| Thinking pattern | Wzorce myślenia | ANALYTICAL_BREAKDOWN |
| System info | Informacje o AIONS | Bootstrap, config |
| Meta | Referencje | "Based on N chunks" |

## Inne pliki wiedzy

| Plik | Ścieżka |
|------|---------|
| cbms_rules.jsonl | `E:\AJAJAJ\CBMS_SEED\` |
| glossaries.jsonl | `E:\AJAJAJ\CBMS_SEED\` |
| styles.jsonl | `E:\AJAJAJ\CBMS_SEED\` |
| kr_maps.jsonl | `E:\AJAJAJ\CBMS_SEED\` |
| claude_chunks.txt | `E:\AJAJAJ\` (173 KB) |

## Komendy diagnostyczne

```bash
# Policz fakty
wc -l facts.jsonl

# Szukaj w faktach
grep "machine learning" facts.jsonl

# Walidacja JSON
python -c "import json; [json.loads(l) for l in open('facts.jsonl')]"
```
