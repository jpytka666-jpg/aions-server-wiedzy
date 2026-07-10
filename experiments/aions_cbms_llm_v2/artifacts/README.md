# KORZENIEC artifacts

| Path | Co |
|------|-----|
| `vocab/korzeniec_vocab.json` | Hangul + `<<CB:*>>` + kontrolki (build_cbms_vocab.py) |
| `embeddings/` | Semantic init (anti-randn) — JSON + opcjonalnie `.pt` |
| `gate_smoke.json` | Wynik `scripts/gate_demo.py` |
| `hf_bielik_cbms_stub/` | Kopia HF+vocab **albo** stub_manifest (NIGDY nie LOCAL LLM MODELS) |

Write policy: tylko ten katalog. Chunki CBMS i GGUF Bielika = read-only.
