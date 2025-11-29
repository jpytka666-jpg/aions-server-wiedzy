# 🤖 MODELS - Modele AI i weights

## CBMS_SEED (Mistral Repack)

### Lokalizacja
- **Seed folder**: `E:\AJAJAJ\CBMS_SEED\`
- **Source**: `D:\models\Mistral-7B-AIONS-REPACK\chunks`

### Statystyki
- **Artifacts**: 13,889
- **Total size**: 14.5 GB (13,824 MB)

### Pliki w CBMS_SEED
```
E:\AJAJAJ\CBMS_SEED\
├── seed_manifest.json    # Manifest z metadanymi
├── bench_plan.json       # Plan benchmarku
├── cbms_rules.jsonl      # Reguły CBMS
├── decoder_hooks.json    # Hooks dekodera
├── facts.jsonl           # Fakty (template)
├── glossaries.jsonl      # Słowniki
├── kr_maps.jsonl         # Mapy koreańskie
├── seed_summary.txt      # Podsumowanie
├── styles.jsonl          # Style odpowiedzi
└── token_map.json        # Mapa tokenów
```

### seed_manifest.json
```json
{
  "source_path": "D:\\models\\Mistral-7B-AIONS-REPACK\\chunks",
  "artifact_count": 13889,
  "total_bytes": 14496047104,
  "total_mb": 13824.51,
  "sample_artifacts": ["chunk_000000000.bin", ...],
  "quant_plan": {
    "Q5": ["attn", "mlp"],
    "Q4": ["others"]
  },
  "generated_at": "2025-09-18T23:46:22"
}
```

## Inne modele (referencje)

| Model | Lokalizacja | Rozmiar |
|-------|-------------|---------|
| Mistral-7B-FULL-AIONS | `D:\models\Mistral-7B-FULL-AIONS\` | ~14 GB |
| Phi-3-mini-4k | `E:\...\huggingface_cache\` | ~2 GB |
| phi3-q4.gguf | `E:\...\CLAUDE_EXPERIMENT\` | 267 MB |

## Korean Neural Injection

### Pliki
- `KOREAN_NEURAL_INJECTION_PHI3.py`
- `KOREAN_PHI3_INJECTOR.py`
- `AIONS_KOREAN_MODIFIED_PHI3.safetensors`

### Parametry
- **Compression**: 3.29:1
- **Korean syllables**: 4,016

## Quantization

### Obsługiwane formaty
- Q4 (4-bit)
- Q5 (5-bit)
- GGUF (llama.cpp compatible)
- safetensors (HuggingFace)

### Narzędzia
- `REPACK_PHI3.py` - Product Quantization
- `llama.cpp` - GGUF conversion
