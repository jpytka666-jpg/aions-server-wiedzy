# KORZENIEC — NEXT (Faza 2→3)

Gate Fazy 1 **nie wymaga** poniższych kroków. To ścieżka do natywnego vocab w HF Bieliku.

## Dlaczego stub?

Lokalnie masz **GGUF Q4** (`D:\LOCAL LLM MODELS\Bielik-4.5B-Q4_K_M\`) — to format Ollama, nie pełny HF tokenizer+embeddings do resize. Skrypt `prepare_hf_bielik_cbms.py` szuka osobnej kopii HF i zapisuje **tylko** do `artifacts/hf_bielik_cbms_stub/`.

## Krok 1 — pobierz HF Bielik (jednorazowo)

```powershell
pip install transformers torch accelerate safetensors

# ~9GB RAM/disk — offload na dysk jeśli trzeba
huggingface-cli download speakleash/Bielik-4.5B-v3.0-Instruct `
  --local-dir "E:\server wiedzy\experiments\aions_cbms_llm_v2\hf_cache\bielik-hf"
```

Albo ustaw istniejącą ścieżkę:

```powershell
$env:KORZENIEC_HF_MODEL_PATH = "E:\ścieżka\do\folderu\z\config.json"
```

## Krok 2 — merge vocab + semantic embeddings

```powershell
cd "E:\server wiedzy\experiments\aions_cbms_llm_v2"

# upewnij się że artefakty istnieją
python scripts/build_cbms_vocab.py
python scripts/init_cbms_embeddings.py --method semantic

# merge (zapis do artifacts/hf_bielik_cbms_stub/)
python scripts/prepare_hf_bielik_cbms.py
```

Sukces: `artifacts/hf_bielik_cbms_stub/prepare_report.json` ze `status: PREPARED`.

Stub (brak HF): `artifacts/hf_bielik_cbms_stub/stub_manifest.json`.

## Krok 3 — LoRA (Faza 3, opcjonalnie)

```powershell
# szkic — nie zautomatyzowane w tej fali
# base: artifacts/hf_bielik_cbms_stub/model
# data: pary (query PL → kontekst Hangul+<<CB:*>> → answer z chunków)
# rank 8, alpha 16, targets q_proj v_proj o_proj
# output: artifacts/lora/korzeniec_lora/
```

**NIE** merguj do GGUF w `LOCAL LLM MODELS`. Serwuj adapter osobno albo nowy GGUF z kopii.

## Krok 4 — Ollama z rozszerzonym modelem (przyszłość)

1. Merge LoRA do HF kopii w `artifacts/`
2. Konwersja HF → GGUF (`llama.cpp` convert)
3. Nowy tag Ollama np. `bielik-korzeniec` — **osobny** od `bielik-aions`

## Weryfikacja gate (niezależna od HF)

```powershell
cd "E:\server wiedzy"
python experiments/aions_cbms_llm_v2/scripts/gate_demo.py
# oczekuj PASS w gate_smoke.json
```

## Env

| Zmienna | Domyślnie | Opis |
|---------|-----------|------|
| `AIONS_CBMS_FIRST` | `1` | Gate przed Ollamą |
| `AIONS_CBMS_CONFIDENCE` | `0.7` | Próg hit |
| `KORZENIEC_HF_MODEL_PATH` | — | Ścieżka do HF z `config.json` |
| `AIONS_PATH` | `aions_core` | CBMS memory root |
