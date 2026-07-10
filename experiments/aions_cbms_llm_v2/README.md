# KORZENIEC — AIONS CBMS-LLM v2

> **Korzeń myśli rośnie z codebooka, nie z szumu.**
> Następca Phi-KR / PHIZONKKILL — bez `torch.randn`.

## Co DZIAŁA TERAZ (2026-07-10, Faza 1+2 start)

| Komponent | Status | Gdzie |
|-----------|--------|-------|
| **CBMS-first gate** | **DZIAŁA** | `control_plane/cbms_gate.py` + podpięcie w `llm_adapter.py` |
| Retrieval (Chroma + symbolic + korean keys) | **DZIAŁA** | `cbms_gate.retrieve()` |
| Gate hit ≥0.7 → odpowiedź bez Ollamy | **DZIAŁA** | `compose_from_chunks()` |
| Gate miss → Bielik + `<addr>` + `<<CB:*>>` | **DZIAŁA** (wymaga Ollamy) | `gate_answer()` |
| Smoke test gate | **DZIAŁA** | `scripts/gate_demo.py` → `artifacts/gate_smoke.json` |
| Vocab Hangul+codebook (4040 tokenów) | **DZIAŁA** | `artifacts/vocab/korzeniec_vocab.json` |
| Semantic embedding init (anti-randn) | **DZIAŁA** | `artifacts/embeddings/` |
| HF Bielik + vocab merge | **STUB** | `scripts/prepare_hf_bielik_cbms.py` — patrz [NEXT.md](./NEXT.md) |
| Natywny Hangul w GGUF Ollama | **NIE** | wymaga HF→train→export |
| LoRA na adresach CBMS | **NIE** | Faza 3 |

## Czego NIE udajemy

1. **GGUF `bielik-aions` nie ma natywnych tokenów Hangul** — Ollama widzi adresy jako zwykły tekst. To wystarczy na gate+prompt (Faza 1). Pełny native vocab = osobny eksport HF.
2. **Gate ≠ magiczny NLG** — przy hit składa odpowiedź z treści chunków, nie „myśli” jak pełny LLM.
3. **Nie ruszamy** `D:\LOCAL LLM MODELS\` ani produkcyjnych chunków CBMS.

## Złota zasada (wdrożona)

```
confidence(CBMS) >= 0.7  →  odpowiedź z chunków (bez LLM)
confidence(CBMS) <  0.7  →  Bielik + kontekst CBMS + Hangul/codebook w prompcie
```

Env:

```
AIONS_CBMS_FIRST=1          # domyślnie włączone
AIONS_CBMS_CONFIDENCE=0.7
```

## Quickstart gate (działa bez Ollamy)

```powershell
cd "E:\server wiedzy"
python experiments/aions_cbms_llm_v2/scripts/gate_demo.py
type experiments\aions_cbms_llm_v2\artifacts\gate_smoke.json
```

Pełny test z Bielikiem (miss → Ollama):

```powershell
python experiments/aions_cbms_llm_v2/scripts/gate_demo.py --with-llm
```

Użycie w kodzie:

```python
from control_plane.cbms_gate import chat_cbms_first_full
out = chat_cbms_first_full("Jak działa pipeline CBMS?")
print(out["gate"], out["confidence"], out["content"][:200])
```

## Quickstart vocab/embedding (Faza 0 artefakty)

```powershell
cd "E:\server wiedzy\experiments\aions_cbms_llm_v2"
python scripts/build_cbms_vocab.py
python scripts/init_cbms_embeddings.py --method semantic
python scripts/prepare_hf_bielik_cbms.py   # stub jeśli brak HF
```

## Bazowy model

| Pole | Wartość |
|------|---------|
| Model | **Bielik-4.5B-v3.0-Instruct** (SpeakLeash) |
| Ollama (usta) | `bielik-aions` — Q4 GGUF, read-only |
| HF (trening vocab) | opcjonalny download — [NEXT.md](./NEXT.md) |

## Ścieżki

| Co | Path |
|----|------|
| Gate | `E:\server wiedzy\control_plane\cbms_gate.py` |
| llm_adapter | `E:\server wiedzy\control_plane\llm_adapter.py` |
| Codebook | `E:\server wiedzy\aions_core\memory\codebook\codebook.json` |
| Ten eksperyment | `E:\server wiedzy\experiments\aions_cbms_llm_v2\` |
| Bielik Q4 (read-only) | `D:\LOCAL LLM MODELS\Bielik-4.5B-Q4_K_M\` |

## Dokumenty

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [INTEGRATION.md](./INTEGRATION.md) — gate wdrożony (Faza 1)
- [NEXT.md](./NEXT.md) — HF download + LoRA (Faza 2–3)
- [scripts/design_spec.json](./scripts/design_spec.json)

## Status

**Faza 1 DONE** — gate produkcyjny w `control_plane/`.
**Faza 2 START** — `prepare_hf_bielik_cbms.py` + stub manifest; pełny HF merge gdy model lokalny.
