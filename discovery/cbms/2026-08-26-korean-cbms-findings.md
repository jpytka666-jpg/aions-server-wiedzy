# CBMS Discovery — Korean Pattern / Esperanto Separation

**Date:** 2026-08-26  
**Project:** AIONS / CBMS  
**Repository:** `jpytka666-jpg/aions-server-wiedzy`  
**Discovery branch:** `discovery/cbms-structure-2026-08-26`  
**Local discovery branch:** `discovery/cbms-structure`  
**Local base commit observed:** `77a8485`  
**Remote main observed during publication:** `afeb8921e3753ae06872b29ced73cf6d373a3495`

## Scope

This document records an evidence-based finding from the existing CBMS artefacts. It is **not an implementation change** and does not claim that the historical Korean experiment was a complete or lossless neural compression system.

## Current evidence

The existing `esperanto_bridge.py` is a deterministic, lightweight normalization layer for PL/EN → Esperanto. Example canonicalization found in the code/codebook:

`byłem` / `byłam` / related forms → `mi estis` → symbol `A1`

The current `codebook.json` contains 16 symbols. Its structure is explicitly symbolic/semantic (`sem`, `eo`, `pl`) rather than a learned neural codebook.

A historical artefact, `aions_core/AIONS_KOREAN_INJECTION_RESULTS.json`, reports:

- model: Microsoft Phi-3 Mini 4K Instruct
- timestamp: `2025-09-13`
- `cbms_blocks`: 8
- `semantic_units`: 8
- `korean_syllables`: 16
- `injection_mappings`: 48
- `compression_ratio`: 3.31125
- `memory_reduction_percent`: 75.0
- `neural_modifications`: 48 mappings, each with a 100-value vector, for 4,800 values total

## Critical finding: one neural-pattern blob

A SHA-256 comparison of the serialized `neural_pattern` field for each of the 8 `cbms_data` semantic units produced exactly one distinct digest:

`fbfb16c4dc276df7`

The digest was associated with all eight semantic units:

- `인공지능`
- `신경망`
- `학습`
- `처리`
- `최적화`
- `압축`
- `효율`
- `성능`

Therefore, this artefact **does not by itself demonstrate eight distinct neural representations**. The recorded `neural_pattern` appears to be a common/shared payload or template in this particular historical result.

## Interpretation

There are two conceptually separate mechanisms in the evidence so far:

### 1. Canonical semantic normalization

`PL/EN text → normalization → Esperanto canonical form → CBMS symbol`

Esperanto functions here as a deterministic canonicalization funnel, not as a general-purpose translation system.

### 2. Historical Korean/CBMS block experiment

`semantic unit → Hangul syllable/block representation → CBMS-labelled neural payload`

The Hangul layer should currently be treated as a **block/indexing representation experiment**, not as proof that Korean language itself provides compression.

The two mechanisms should not be conflated until the generating code is traced.

## What is still unproven

The following claims require source-code provenance or reconstruction tests before being accepted as properties of CBMS:

1. The exact algorithm that generated `AIONS_KOREAN_INJECTION_RESULTS.json`.
2. Whether the reported `compression_ratio` was measured against a reconstructible representation.
3. Whether the reported 75% memory reduction was measured from actual serialized/stored data or from an abstract accounting model.
4. Whether the Hangul syllables carry semantic identity, positional identity, or are simply labels.
5. Whether the `neural_pattern` is intentionally shared by design or was duplicated by an artefact-generation shortcut.
6. Whether a round-trip decode/reconstruction test exists for the historical result.

## Next investigation target

**Do not implement yet.** Locate the generator/source code responsible for `AIONS_KOREAN_INJECTION_RESULTS.json` and trace:

`input → block generation → neural_pattern generation → compression measurement → JSON output`

The next proof point is the generator, not another interpretation of the output JSON.

## Provenance / publication note

This document was published as a visible GitHub discovery artefact on a dedicated branch so that the historical evidence and its limitations remain reviewable without modifying the live AIONS runtime.
