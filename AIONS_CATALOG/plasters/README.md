# 🎯 PLASTERS - Extended Knowledge Packs

## Główne pakiety

### 1. plasters_200g (GŁÓWNY)
- **PACKi**: 200 (PACK-0000 do PACK-0199)
- **Q&As**: ~343,200 (avg 1,716 per PACK)
- **Ścieżka**: `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\plasters_200g\`

### 2. plasters_fullstack
- **PACKi**: 448
- **Q&As**: ~768,768
- **Ścieżka**: `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\plasters_fullstack\`

### 3. plasters_unified (agregacja)
- **Ścieżka**: `E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\plasters_unified\`
- Zawiera: plasters_200g, plasters_active, plasters_claude, plasters_custom, plasters_general, plasters_howto, plasters_programming

## Struktura PACK

```
PACK-0100/
├── module.json    # Metadata
├── enc.npz        # Encoder weights (numpy)
├── dec.npz        # Decoder weights (numpy)
└── kb.mmap        # Knowledge base (memory-mapped)
```

## module.json format

```json
{
  "name": "PACK-0100",
  "d_model": 1024,
  "rank": 512,
  "files": {
    "enc": "enc.npz",
    "dec": "dec.npz",
    "kb": "kb.mmap"
  },
  "stats": {
    "mu": 0.0,
    "sigma": 1.0,
    "qa_count": 1716
  },
  "router": {
    "idf": "idf.npz",
    "minhash": "mhash.npz",
    "tags": ["PACK"]
  }
}
```

## Użycie w AIONS

```bash
# Ustawienie zmiennej środowiskowej
$env:CBMS_ENABLE_PLASTERS = "1"
$env:CBMS_PLASTERS_DIR = "E:\AI_WORKSPACE\MASTER_CLEAN\UNCLASSIFIED\plasters_200g"

# Sprawdzenie statusu
curl http://localhost:9000/plasters/stats
```

## Specjalistyczne plasters

| Pakiet | Tematyka |
|--------|----------|
| plasters_claude | Claude-specific knowledge |
| plasters_howto | Instrukcje i tutoriale |
| plasters_programming | Programowanie |
| plasters_custom | Własne paczki użytkownika |
| plasters_general | Wiedza ogólna |
