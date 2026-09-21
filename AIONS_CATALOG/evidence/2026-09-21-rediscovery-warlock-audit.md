# Historical cognition evidence audit — 2026-09-21

AUTHOR: GPT-5.6 Sol / ChatGPT
STATUS: VERIFIED AGAINST GITHUB SOURCES AVAILABLE 2026-09-21

## Rediscovery failure

The CBMS synthesis wrapper was not a new defect in September 2026.

- `AIONS_DEEP_DIVE_REPORT_20251129.md` already identifies `_synthesize_chunks()` as a template bug.
- `AIONS_DEPENDENCY_MAP_20251128.md` already records generic-template responses.
- Commit `592d5eec613398d00941d9a0dfb0af754658e5cb` on 2026-09-21 described the same synthesis wrapper as the "next real defect".
- Commit `eaf6a20e6999509797b707add53f9040a4f692cd` records the correction and the false-verdict fixes in the historical guard.

Conclusion: this is a verified example of REDISCOVERY_FAILURE.

## Warlock — separate architecture, code thread, and runtime status

Three different facts must not be collapsed into one:

1. Architecture: `obrazowanie-stanu/00_CORE_SYSTEM/architektura-aions.md` defines Warlock as the controlled boundary between Marcin/world/cloud and the AIONS core.
2. Code/design thread: `polip-agi` commit `2cd32c4fbff03afc48ea6953a54b65a66bbb9f40` introduces `WarlockBridge`, legacy `sheriff_bridge` deserialization, and `warlock-bridge` topology identifiers. `super-system` branch `feat/warlock-kali-lab-foundation` exists and points to `f53da77b595e3e8f3aeed4771f9baafd15054482`.
3. Runtime on canonical Server Wiedzy: `obrazowanie-stanu/03_AGENT_STATE/Anthropic/Cowork/2026-09-21-architektura-aions-organy-i-dowody.md` reports no Warlock file or directory found on E:\\server wiedzy during its bounded search and explicitly says Warlock was not a runtime organ there.

Conclusion: WARLOCK is a real architectural/code concept with repository evidence, but runtime implementation on canonical Server Wiedzy is NOT VERIFIED.

## Warlock rename documentation corruption

The same `polip-agi` commit `2cd32c4fbff03afc48ea6953a54b65a66bbb9f40` also contains documentation replacements that are semantically wrong, including phrases equivalent to:

- "Warlock replaces the earlier name Warlock"
- "migracja Warlock -> Warlock"

The Rust topology change itself is real; the migration prose was damaged by an over-broad rename. Treat this as a separate documentation defect, not evidence that the Warlock concept is invalid.
