# TASKS — AIONS GGUF Runner (poziom C)

Tracking wdrożenia. **Nie implementować silnika w tym tasku designu** — checklista na później.

Legenda: `[ ]` todo · `[~]` w toku · `[x]` done · `[-]` cancelled / out of scope

---

## Faza D — Design (ten folder)

- [x] README AIONS-first
- [x] DESIGN.md (cel, arch, API speak/understand, modele, fazy, ryzyka, sukces)
- [x] TASKS.md
- [x] Symulacja flow (bez llama.cpp): `scripts/simulate_runner_flow.py` → `artifacts/simulate_runner_flow.json`
- [ ] Review Marcina / akceptacja kierunku (submodule vs bin, port 11435, dual backend)
- [ ] memory_store summary po akceptacji (opcjonalnie powtórka)

---

## Faza 0 — Proof of concept

- [ ] Utworzyć `build/` + `.gitignore` (binaria, modele, artifacts)
- [ ] Pin llama.cpp (submodule **lub** dokumentowana ścieżka do oficjalnego release Windows)
- [ ] Zbudować / pobrać `llama-cli` / `llama-server` (CPU najpierw; CUDA/Vulkan osobno)
- [ ] One-shot: załaduj `E:\server wiedzy\models\qwen2.5-3b-instruct\qwen2.5-3b-instruct-q4_K_M.gguf`
- [ ] CLI speak z CONTEXT zawierającym `<addr>…</addr>` i `<<CB:A1>>` (ręczny smoke)
- [ ] Bench tok/s vs Ollama **ten sam GGUF** → `artifacts/bench_faza0.json`
- [ ] Zapisać backend użyty (cpu/cuda/vulkan) i czy M2000M w ogóle działa

---

## Faza 1 — Parity z ustami AIONS

### Wrapper HTTP

- [ ] `GET /health`
- [ ] `POST /v1/understand` (kontrakt = `llm_mouth.understand`)
- [ ] `POST /v1/speak` (kontrakt = `llm_mouth.speak`)
- [ ] Domyślne `n_predict` z `AIONS_MOUTH_NUM_PREDICT` (≤ 200)
- [ ] System prompty skopiowane/zsynchronizowane z `llm_mouth.py` (usta, nie asystent ogólny)
- [ ] Protected spans: Hangul `<addr>`, `<<CB:*>>` — testy golden
- [ ] Brak UI / brak OpenAI-compat jako wymogu

### Integracja MCP (cienka)

- [ ] Env `AIONS_MOUTH_BACKEND=ollama|gguf`
- [ ] Env `AIONS_GGUF_HOST` + mapowanie tagu `AIONS_MOUTH_MODEL` → ścieżka GGUF
- [ ] Smoke: `llm_understand` + `llm_speak` przez runner
- [ ] Smoke: **CBMS gate hit → mouth_calls = 0** (runner nie wołany)
- [ ] Nie psuć ścieżki Ollama (rollback = zmiana env)

### Jakość / sukces

- [ ] Porównanie jakości speak (subiektywne PL + checklista „tylko CONTEXT”)
- [ ] Tok/s ≥ Ollama (ten sam GGUF, ten sam device class)
- [ ] Zero zapisów do `D:\LOCAL LLM MODELS`

---

## Faza 2 — Multi-model slots

- [ ] `POST /v1/load` / `/v1/unload`
- [ ] Rejestr tagów: `aions-mouth`, opcjonalnie `bielik-aions`
- [ ] Exclusive load (jeden model w VRAM); unload przed switch
- [ ] Bielik: ścieżka D: read-only **lub** kopia GGUF na E:
- [ ] Dokument VRAM: Qwen primary, Bielik secondary/CPU

---

## Faza 3 — Image / multimodal

- [-] OUT OF SCOPE — nie planować w tym projekcie

---

## Non-goals (pilnować przy review PR)

- [ ] Żaden PR nie dodaje treningu HF / LoRA tutaj
- [ ] Żaden PR nie zastępuje CBMS „modelem generatywnym”
- [ ] Żaden PR nie buduje Ollama-clone UI / registry pull
- [ ] Model Runtime adapter = osobny tracking (link gdy powstanie)

---

## Artefakty oczekiwane (później)

```text
experiments/aions_gguf_runner/
  README.md          # done
  DESIGN.md          # done
  TASKS.md           # done
  artifacts/         # bench JSON, golden prompts (Faza 0+)
  build/             # skrypty build (Faza 0+)
  wrapper/           # cienki HTTP/CLI (Faza 1+)
  third_party/       # submodule llama.cpp (opcjonalnie)
```

---

## Definition of Done (projekt runnerski, nie sam design)

Faza 1 zamknięta gdy: MCP usta działają na runnerze, gate omija LLM, bench ≥ Ollama na tym samym GGUF, adresy CBMS nietknięte, Ollama nadal dostępna jako fallback.
