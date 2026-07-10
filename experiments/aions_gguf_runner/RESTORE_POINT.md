# RESTORE POINT — przed Faza 0 aions_gguf_runner

- **timestamp:** 2026-07-11T00:51:19+01:00
- **parent HEAD (pre-commit):** 78b8d802bd592d555558a708a43d32107f9a337e
- **branch:** main
- **cel:** checkpoint przed implementacją Fazy 0 (wrapper llama-cli / HTTP stub)

## Ustalenia (stan przed Faza 0)

1. CBMS gate (control_plane/cbms_gate.py) — hit omija LLM / runner
2. llm_speak / llm_understand + llm_mouth.py (Ollama ions-mouth) — działa
3. Design + symulacja xperiments/aions_gguf_runner — mandatory PASS; opcjonalny S5 Hangul mutation FAIL (Ollama zamienia `<addr>각</addr>` → `język`; CB przeżywa)
4. GGUF kanoniczny E: models/qwen2.5-3b-instruct/qwen2.5-3b-instruct-q4_K_M.gguf (gitignore — nie w gicie)
5. llama-cli dostępny: D:\LOCAL LLM MODELS\Bielik-4.5B-Q4_K_M\llama-cli.exe (read-only D:)
6. NIE push; NIE mutować chunków CBMS / D:\LOCAL LLM MODELS

## Pliki w tym commicie

- control_plane/cbms_gate (+ llm_adapter)
- mcpServers/.../llm_mouth.py + server.py (narzędzia llm_*)
- experiments/aions_gguf_runner (design + simulate)
- experiments/aions_cbms_llm_v2 (docs/scripts, bez nested .git)
- models/qwen2.5-3b-instruct docs (Modelfile, README)
