# RESTORE POINT ? przed Faza 0 aions_gguf_runner

- **timestamp:** 2026-07-11T00:51:19+01:00
- **commit (restore):** `5dfae12def1abeeb6788ef5ad4004f668ba4267d`
- **parent HEAD (pre-commit):** `78b8d802bd592d555558a708a43d32107f9a337e`
- **branch:** main
- **cel:** checkpoint przed implementacj� Fazy 0 (wrapper llama-cli / HTTP stub)
- **push:** NIE

## Ustalenia (stan przed Faza 0)

1. CBMS gate (`control_plane/cbms_gate.py`) ? hit omija LLM / runner
2. `llm_speak` / `llm_understand` + `llm_mouth.py` (Ollama `aions-mouth`) ? dzia�a
3. Design + symulacja `experiments/aions_gguf_runner` ? mandatory PASS; opcjonalny S5 Hangul mutation FAIL (Ollama zamienia `<addr>?</addr>` ? `j�zyk`; CB prze�ywa)
4. GGUF kanoniczny E: `models/qwen2.5-3b-instruct/qwen2.5-3b-instruct-q4_K_M.gguf` (gitignore ? nie w gicie)
5. llama-cli dost�pny: `D:\LOCAL LLM MODELS\Bielik-4.5B-Q4_K_M\llama-cli.exe` (read-only D:)
6. NIE mutowa� chunk�w CBMS / `D:\LOCAL LLM MODELS`

## Pliki w tym commicie

- control_plane/cbms_gate (+ llm_adapter)
- mcpServers/.../llm_mouth.py + server.py (narz�dzia llm_*)
- experiments/aions_gguf_runner (design + simulate)
- experiments/aions_cbms_llm_v2 (docs/scripts; nested `.git` ? `.git_nested_bak`)
- models/qwen2.5-3b-instruct docs (Modelfile, README) ? **bez** GGUF

## Rollback

```powershell
git checkout 5dfae12
# lub: git revert <faza0-commit>  po kolejnych commitach
```
