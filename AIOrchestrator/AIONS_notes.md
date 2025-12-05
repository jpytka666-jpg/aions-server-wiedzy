# AIONS / CBMS - Architecture Notes (2025-11-02)

- **CBMS (Code Book Memory System)**
  - Knowledge stored as chunks (ID "Kxxxx") with manifest and concept map.
  - Each chunk carries full semantics; generation works on blocks, not tokens.
  - Combined with CBMS-ES-KR (Esperanto + Hangul indexing) for compression (~3.29:1) and fast key matching.

- **CBMS-ES-KR**
  - Esperanto-style symbolic index plus Hangul addressing, so multi-language concepts map cleanly.
  - "Plasters" = domain-specific bundles of knowledge and matching thinking patterns.

- **CRLA (Chain Reaction Learning Algorithm)**
  - Simulates multiple answer variants (tournament K=12, J=0.893).
  - Winning branch becomes a new "thinking pattern" chunk; no traditional training, pure editing.
  - Patterns are reusable and editable, so the system evolves without gradient updates.

- **Thinking patterns / Claude-style reasoning**
  - Every query logs reasoning: context chunks, retrieved chunks, synthesis steps.
  - Over time the system accumulates "claude patterns" that speed up and stabilize responses.
  - Halucinations are prevented: fallback "I do not know / CBMS-KR data missing" when no block fits.

- **Zero token soup**
  - Answers are composed from Hangul keys + concept map + symbolic index.
  - Longer context improves efficiency because many blocks repeat.
  - Math solver is deterministic: 100% accuracy on numeric questions (GSM8K).

- **Pocket-QC**
  - Mentioned "Pocket Quantum Computer" simulator built on CRLA (check tools/ for implementations).

- **Key traits**
  - Fully offline, no hallucinations, no classical token-based pipeline.
  - Accuracy limited by available chunks; soft refusal if knowledge is missing.
  - Rich documentation (AIONS_FULL_ANALYSIS_REPORT) and operational scripts (benchmark, server API, PowerShell chat).

- **Integration ideas with Run-AI**
  1. Set environment variables (e.g. `AIONS_HOME`), relocate dependencies from `E:\...`.
  2. Add `Invoke-AIONS` module to Run-AI (chat/test/benchmark/server entry points).
  3. Surface AIONS logs (latest benchmark/test) inside `C:\AIOrchestrator\logs`.
  4. Register Task Scheduler jobs for automated benchmarks.
  5. Implement a command router so natural text commands trigger AIONS modes.
  6. Fix facts loader fallback so manual JSON facts are used when index fails.
  7. Align logging/telemetry (offline JSON/EventLog) via `docs/telemetry_playbook.md`.
