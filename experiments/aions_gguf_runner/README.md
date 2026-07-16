# AIONS GGUF Runner — poziom C (Faza 0 scaffold)

> **Status:** Faza 0 proof (2026-07-11) — cienki wrapper + CLI/HTTP; silnik = istniejący `llama-cli` (nie fork).  
> **Profil:** AIONS-first — usta/gardło, **nie** generyczny serwer LLM.  
> **Restore point:** commit `5dfae12` + [RESTORE_POINT.md](./RESTORE_POINT.md)

## Jednym zdaniem

Lokalny wrapper wokół **llama-cli** ładuje GGUF z E: i serwuje **speak / understand** (jak `llm_mouth`), z gate-first i ochroną `<addr>` / `<<CB:*>>`. Mózg zostaje CBMS.

## Jak odpalić

```powershell
# Z repo root (E:\server wiedzy)
.\scripts\aions_python.ps1 experiments\aions_gguf_runner\scripts\smoke_faza0.py
.\scripts\aions_python.ps1 experiments\aions_gguf_runner\scripts\simulate_runner_flow.py

# CLI (cwd = experiments\aions_gguf_runner)
cd experiments\aions_gguf_runner
..\..\scripts\aions_python.ps1 -m wrapper health
..\..\scripts\aions_python.ps1 -m wrapper speak --context "Adres <addr>각</addr> <<CB:A1>>" --lang pl
..\..\scripts\aions_python.ps1 -m wrapper serve
# Szybki stub: $env:AIONS_GGUF_SMOKE_REAL='0'
```

### Env

| Env | Default | Opis |
|-----|---------|------|
| `AIONS_MOUTH_BACKEND` | `ollama` | `ollama` \| `llamacpp` \| `gguf` — **nie psuje** domyślnego Ollama |
| `AIONS_GGUF_HOST` | `http://127.0.0.1:11435` | HTTP runner |
| `AIONS_GGUF_PATH` | `models/qwen2.5-3b-instruct/…q4_K_M.gguf` | GGUF na E: |
| `AIONS_LLAMA_CLI` | auto (Bielik folder) | ścieżka do `llama-cli.exe` |
| `AIONS_GGUF_MODE` | `auto` | `auto` \| `real` \| `stub` |
| `AIONS_MOUTH_NUM_PREDICT` | `200` | limit generacji |

## AIONS-first

| Warstwa | Co robi |
|---------|---------|
| **Gate hit** | Odpowiedź CBMS, `mouth_calls=0`, runner nie startuje |
| **Miss / speak** | CONTEXT → krótki reply; post-process dokleja brakujące `<addr>` / `<<CB:*>>` |
| **Understand** | Intent JSON (`lang/need/remember/summary`) |

## Dokumenty

| Plik | Treść |
|------|--------|
| [DESIGN.md](./DESIGN.md) | Architektura, API, fazy |
| [TASKS.md](./TASKS.md) | Checklista |
| [RESTORE_POINT.md](./RESTORE_POINT.md) | Checkpoint przed Faza 0 |
| [wrapper/](./wrapper/) | Faza 0 kod |

## Relacja

- `experiments/aions_cbms_llm_v2` — mózg/most (KORZENIEC)  
- Ten folder — ścieżka C (inference GGUF pod usta)
