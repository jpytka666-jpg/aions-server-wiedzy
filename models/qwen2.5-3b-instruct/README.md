# Qwen2.5-3B-Instruct Q4 — AIONS Mouth

## Paths (this machine, 2026-07-10)

| What | Path |
|------|------|
| Ollama models dir (`OLLAMA_MODELS`) | `D:\fitness-app\ollama-models` (not C: default) |
| Pull tag | `qwen2.5:3b-instruct-q4_K_M` (~1.9 GB) |
| Working tag | `aions-mouth` |
| Modelfile + docs (E:) | `E:\server wiedzy\models\qwen2.5-3b-instruct\` |
| Blob (sha256) | `D:\fitness-app\ollama-models\blobs\sha256-5ee4f07cdb9beadbbb293e85803c569b01bd37ed059d2715faa7bb405f31caa6` |
| Optional GGUF copy on E: | `E:\server wiedzy\models\qwen2.5-3b-instruct\qwen2.5-3b-instruct-q4_K_M.gguf` (if copied) |

## MCP tools (prod aions-context)

- `llm_understand(text)` — intent JSON
- `llm_speak(context, user_lang?)` — short reply from context only

Env: `AIONS_MOUTH_MODEL=aions-mouth`, `OLLAMA_HOST=http://localhost:11434`

## Do not touch

- `D:\LOCAL LLM MODELS` (no destructive ops)
- Bielik / `bielik-aions` (untouched)
