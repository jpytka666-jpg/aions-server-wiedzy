# AIONS GGUF Runner — poziom C (projekt / design)

> **Status:** design only (2026-07-11). Brak implementacji silnika.  
> **Profil:** AIONS-first — cienkie usta/gardło, **nie** generyczny serwer LLM.  
> **Osobny tor:** Model Runtime (adapter) ≠ ten projekt. Tu tylko ścieżka C = runner GGUF / llama.cpp.

## Jednym zdaniem

Lokalny, cienki fork/wrapper **llama.cpp**, który ładuje GGUF i serwuje **tylko** to, czego potrzebują usta AIONS (`llm_speak` / `llm_understand`) — z natywnym szacunkiem dla adresów CBMS (Hangul / `<<CB:*>>`) i krótkim `n_predict`. Mózg (CBMS + Chroma + MCP) zostaje na `E:\server wiedzy`.

## AIONS-first (twarde zasady)

| Warstwa | Co robi | Co NIE robi |
|---------|---------|-------------|
| **Mózg** | CBMS gate, Chroma, MCP tools, decyzje | Generacja NLG „z głowy” |
| **Usta (ten runner)** | Przeformułowanie kontekstu / intent JSON | Fakty, tool-calling, esej |
| **Gate hit** | Odpowiedź z CBMS **omija runner** | — |

Hangul w ścieżce promptu = **adresy bloków** (`<addr>…</addr>`), nie koreański NLG.  
`<<CB:*>>` = symbole codebook. Runner **nie tłumaczy** ich na „ładny tekst koreański” — przekazuje / chroni jako tokeny adresowe.

## Dokumenty

| Plik | Treść |
|------|--------|
| [DESIGN.md](./DESIGN.md) | Cel, architektura, API speak/understand, modele, fazy, ryzyka, sukces |
| [TASKS.md](./TASKS.md) | Checklista wdrożenia (tracking, bez kodu runnera teraz) |
| [scripts/simulate_runner_flow.py](./scripts/simulate_runner_flow.py) | Symulacja gate→usta (bez llama.cpp) |
| [artifacts/simulate_runner_flow.json](./artifacts/simulate_runner_flow.json) | Wynik PASS/FAIL symulacji |

```powershell
.\scripts\aions_python.ps1 experiments\aions_gguf_runner\scripts\simulate_runner_flow.py
```

## Szybki kontekst sprzętu / ust dziś

- **HW:** Quadro M2000M **4 GB** VRAM, 64 GB RAM, Windows  
- **Usta dziś:** Ollama → tag `aions-mouth` (Qwen2.5-3B Q4), opcjonalnie `bielik-aions`  
- **MCP:** `llm_speak` / `llm_understand` w `mcpServers/.../llm_mouth.py` (`AIONS_MOUTH_MODEL`, `OLLAMA_HOST`)  
- **GGUF kanoniczny (E:):** `E:\server wiedzy\models\qwen2.5-3b-instruct\qwen2.5-3b-instruct-q4_K_M.gguf`  
- **D:\LOCAL LLM MODELS:** read-only (Bielik itd.) — bez destrukcji; kopia na E: jeśli potrzeba

## Non-goals (skrót)

- Nie CBMS / nie drugi mózg  
- Nie trening HF / LoRA w tym repo  
- Nie klon Ollamy (UI, library, pull registry)  
- Nie image / multimodal (Faza 3 = tylko wzmianka OUT OF SCOPE)  
- Nie ruszać wag na D: destrukcyjnie

## Kryteria sukcesu (skrót)

1. **Parity ust:** `speak` / `understand` przez runner ≥ jakość Ollamy na **tym samym** GGUF Qwen 3B Q4.  
2. **Tok/s:** ≥ Ollama (CPU lub GPU — ten sam backend porównawczy) na tym samym GGUF.  
3. **Gate:** hit CBMS → **zero** wywołań runnera (usta nie gaszą mózgu).  
4. **Adresy:** Hangul / `<<CB:*>>` w kontekście nie są „naprawiane” ani stripowane przez runner.

## Relacja do innych eksperymentów

- `experiments/aions_cbms_llm_v2` (KORZENIEC) — vocab / embeddingi / gate — **mózg/most**, nie runner.  
- Ten folder — **tylko** ścieżka C (inference GGUF pod usta).

Szczegóły → [DESIGN.md](./DESIGN.md).
