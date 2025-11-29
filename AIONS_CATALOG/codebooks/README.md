# 📖 CODEBOOKS - Systemy kodowania CBMS

## 1. Esperanto Codebook

### Lokalizacja
`E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\thinking_patterns\codebook.json`

### Symbole CRLA (CR1-CR5)
```json
{
  "CR1": { "sem": "crla-system", "eo": ["crla", "turniro"], "pl": ["CRLA", "turniej"] },
  "CR2": { "sem": "crla-winner", "eo": ["gajninto"], "pl": ["zwycięzca"] },
  "CR3": { "sem": "crla-score", "eo": ["poentaro"], "pl": ["wynik"] },
  "CR4": { "sem": "crla-latency", "eo": ["latenco"], "pl": ["latencja"] },
  "CR5": { "sem": "crla-determinism", "eo": ["determinismo"], "pl": ["deterministyczność"] }
}
```

### Symbole CBMS (CB1-CB6)
```json
{
  "CB1": { "sem": "cbms-system", "eo": ["cbms", "memorsistemo"], "pl": ["CBMS", "system pamięci"] },
  "CB2": { "sem": "memory-block", "eo": ["memorbloko", "bloko"], "pl": ["blok", "blok pamięci"] },
  "CB3": { "sem": "chunk", "eo": ["fragmento"], "pl": ["chunk", "fragment"] },
  "CB4": { "sem": "refusal", "eo": ["refuzo"], "pl": ["odmowa"] },
  "CB5": { "sem": "panic", "eo": ["paniko"], "pl": ["panika"] },
  "CB6": { "sem": "facts-keys", "eo": ["faktoj", "ŝlosiloj", "indekso"], "pl": ["fakty", "klucze", "indeks"] }
}
```

### Symbole podstawowe (A1-E5)
```json
{
  "A1": { "sem": "byc-past-1sg", "eo": ["mi estis"], "pl": ["byłem", "byłam"] },
  "B2": { "sem": "dzisiaj", "eo": ["hodiaŭ"], "pl": ["dzisiaj", "dziś"] },
  "C3": { "sem": "miejsce-sklep", "eo": ["en vendejo", "vendejo"], "pl": ["w sklepie", "sklep"] },
  "D4": { "sem": "kupic-1sg-past", "eo": ["mi aĉetis"], "pl": ["kupiłem", "kupiłam"] },
  "E5": { "sem": "chleb", "eo": ["pano", "panon"], "pl": ["chleb"] }
}
```

## 2. Korean Keys Codebook

### Lokalizacja
`E:\AI_WORKSPACE\MASTER_CLEAN\CBMS_KR\`

### Parametry
- **Syllables used**: 8,042
- **Compression ratio**: 36:1 (documented), 3.29:1 (actual)
- **Pattern count**: 4,016+

### Mechanizm
1. Character 3-grams
2. SHA1 hash prefixes
3. Set intersection for semantic search
4. O(n) lookup complexity

### Format Korean address
- Hangul syllables: 가, 각, 갂, 갃, 간, 갅...
- Mapping: doc_id (Korean) → chunk_id (K[hex])

## 3. Token Map

### Lokalizacja
`E:\AJAJAJ\CBMS_SEED\token_map.json`

### Zastosowanie
Mapowanie tokenów dla modeli Mistral/Phi3

## 4. Decoder Hooks

### Lokalizacja
`E:\AJAJAJ\CBMS_SEED\decoder_hooks.json`

### Zastosowanie
Hooks do dekodera dla custom inference
