# KORZENIEC — Integracja z AIONS

## Stan obecny (Faza 1 wdrożona 2026-07-10)

`E:\server wiedzy\control_plane\cbms_gate.py` + cienkie podpięcie w `llm_adapter.py`:

- `AIONS_CBMS_FIRST=1` (domyślnie) → `chat()` / `chat_full()` idą przez gate
- `retrieve()` = Korean Keys + lexical + symbolic (Esperanto/codebook) + Chroma (best-effort)
- hit ≥0.7 → `compose_from_chunks()` bez Ollamy
- miss → Bielik z `<addr>` Hangul + `<<CB:*>>` w sekcji KORZENIEC promptu

Smoke: `experiments/aions_cbms_llm_v2/scripts/gate_demo.py`

## API

```python
from control_plane.cbms_gate import retrieve, gate_decide, gate_answer, chat_cbms_first_full

r = retrieve("Co to jest codebook w CBMS?")
d = gate_decide(r, threshold=0.7)          # {"hit": True/False, ...}
out = chat_cbms_first_full("Jak działa pipeline CBMS?")
# out["gate"] in {"hit","miss"}; hit → used_llm=False
```

`llm_adapter.chat_full` przy `AIONS_CBMS_FIRST=1` deleguje do `chat_cbms_first_full`
(chyba że `force_llm=True`).

## Prompt przy miss

```
<addr>…Hangul keys…</addr>
<cbms><<CB:CB1>> <<CB:CB3>> …</cbms>
```

Tokenizer Bielika (GGUF) traktuje to jako tekst — wystarczy na Faza 1.
Pełne rozszerzenie vocab HF + LoRA = Faza 2–3 (patrz NEXT.md).

## LoRA (opcjonalnie, Faza 3)

| Param | Wartość |
|-------|---------|
| Base | Bielik-4.5B-v3.0-Instruct (HF, offload RAM) |
| Rank / alpha | 8 / 16 |
| Targets | q_proj, v_proj, o_proj |
| Export | `artifacts/lora/` — **nie** nadpisuje GGUF w LOCAL LLM MODELS |

## Codebook engine

`server/codebook_engine.py`: `encode_eo_to_cbms` / `decode_cbms_to_eo`.
Gate mapuje symbole na `<<CB:SYM>>`.

## Czego nie robić

| Zakaz | Powód |
|-------|--------|
| Patch safetensors w `D:\LOCAL LLM MODELS\*` | Phi-KR lekcja |
| `torch.randn` na Hangul/CB tokenach | Semantyka = 0 |
| Mutacja chunków CBMS „pod model” | Mózg kanoniczny |
| Wymuszanie generacji po koreańsku | Hangul = adres, usta = PL |

## Env

```
AIONS_CBMS_FIRST=1
AIONS_CBMS_CONFIDENCE=0.7
AIONS_KORZENIEC_ROOT=E:\server wiedzy\experiments\aions_cbms_llm_v2
```
