# AIONS — archaeology, reconstruction, development

**Document status:** owner-directed plan, 2026-10-10. **Scope:** public, non-sensitive roadmap. **Source of operational truth:** a separately access-controlled SQLite catalogue and immutable primary artifacts, **not this page**.

## The mission: three phases in a fixed order

### Phase A — archaeology first

1. Inventory each authorized repository, **every branch and Git ref**, all reachable historical commits, including rescued, deleted or superseded code.
2. Enumerate complete source files and distinct Git blobs. Inspect **the contents** of every in-scope source blob, not only HEAD metadata, README files or selected examples. Deduplicate by content hash while preserving all commit/path/ref occurrences.
3. Record each inspected fact with precise provenance: repository, ref, full commit SHA, blob SHA, path/lines, observation time, reading agent, and explicit verification tier. Record missing/unreadable/uninspected objects as gaps, not negative findings.
4. Catalogue the WPC compression and runtime history, including VQ, WPC v2/v3/v4, Qwen MoE, GPU/CPU attempts, resident runtime, CBMS/CRLA/Pocket QC, agent/MCP integrations.
5. After the Git archaeology, extend the same **read-only and owner-authorized** process to legacy disks, backups, logs and model artifacts. Do not modify or execute unknown historical artifacts merely to inventory them.

**Definition of done:** machine-countable totals for repositories, refs, commits, file occurrences, unique blobs, inspected bodies, errors and unresolved gaps; all claims point to primary evidence.

### Phase R — reproduce what previously worked

1. Reconstruct capabilities from pinned versions and evidence, rather than inferring them from current `main`.
2. Restore WPC compressors, loaders, model/runtime variants and their original operating contracts in controlled branches.
3. Reproduce compilation, model quality, throughput, memory usage and hardware assumptions; convert every failure into a regression test.
4. Require owner review and actual, dated test evidence before declaring a historical capability restored.

**Definition of done:** reproducible runs and test baselines on appropriate authorized hardware. No arbitrary local model deployment before WPC archaeology and reconstruction.

### Phase D — further development

1. Evolve deterministic offline-first AIONS, CBMS/CRLA/Pocket QC and an integrated Rust MCP interface after the reconstruction baseline.
2. Keep code change sets in approved shared repositories on feature branches, with tests, review and merge.
3. Version evidence, decisions, supersession links and outcomes alongside the code; prevent unsupported historical claims from becoming trusted facts.

**Definition of done:** new capabilities have executable acceptance tests, traceable design decisions and operational measurements.

## Working roles (2026-10-10 snapshot)

Owner → GPT-6 coordinator → Paperclip **Codex C.E.O.** → specialists: **FOREMAN** (Claude Opus 5.5, code/tests), **POPYCHAJŁO** (Claude Haiku 4.5, medium, exhaustive archaeology), **KONSULTANT** (Claude Fable 5.1, max, narrowly scoped complex architecture review). These are separate, fixed-model agents; do not swap FOREMAN's model as a substitute for role assignment. Workers should operate in bounded, reviewable batches.

## Evidence inventory snapshot and limitations

- WPC Engine mirror inventory: **77 branch refs**, **51 distinct branch HEADs**. These are *metadata coverage*, not full source-body coverage.
- Paperclip LOR-19, LOR-21: index/coverage inventory; LOR-20: historical model claims; LOR-22: source-level WPC codec analysis.
- LOR-26: successful small bounded VQ source review of **three historical blobs**; this does **not** imply all historical code has been inspected.
- WPC model throughput statements from documents or owner recollection must not be relabelled as independently replicated benchmarks.
- More branch and history coverage remains explicitly outstanding.

## Operational evidence database

**Preferred target:** private SQLite on the Orange Pi NVMe, with WAL, FTS5 and SHA-256-addressed immutable evidence. First prototype schema includes `sources`, `evidence`, `facts`, `fact_evidence`, `repositories`, `repository_refs`, `milestones`, `work_items`, `work_events`, `decisions`, `decision_edges`, `coverage_targets`, `archaeology_events` and `artifact_manifest`.

Status at drafting: **a staging database exists and passes integrity tests, but deployment to the Orange Pi has not been verified**. Do not interpret a document or a staged database as a live deployed service. Automatic agent-to-database synchronization is **not implemented**, and must be designed, permissioned and tested before advertising it.

To avoid accumulating unreviewed handoffs: store canonical evidence references once; use indexed structured facts, bidirectional decision-supersession checks, measured `observed_at`, clear stage status, orphan detection, and a single read-first entrypoint.

## Public GitHub versus private backup

- This repository is **public**. It may contain this roadmap, schemas, public-source evidence hashes, sanitized coverage summaries, migration specifications and redacted reports.
- **Never commit the raw SQLite operational database**, personal conversations, secrets, network credentials, unredacted internal logs, or sensitive disk inventory to a public repository.
- A true SQLite backup must be checkpoint-consistent (WAL included/backup API), integrity-verified, and stored in a protected destination; an eventual private encrypted remote backup requires verified repository access, key custody and restoration tests.
- Git tracks authored source and version history; private SQLite/CAS holds operational facts, immutable evidence and work statuses. Neither is a substitute for the other.

## Acceptance checks for each archaeology batch

- [ ] All requested refs/commits/file blobs enumerated with immutable IDs.
- [ ] Every claimed inspected blob actually read, with source location and a valid hash.
- [ ] Results classified as code-inspected, executed/tested, documented, owner-reported or unknown.
- [ ] Attempt → error → fix → test → result linked without fictional closure.
- [ ] Work item and decisions updated in the protected knowledge catalogue once available, with a verified publication receipt.
- [ ] No unauthorized VM, device, router, Git, model or service mutation.

**Source references:** WPC source-of-truth report in `AIONS_CATALOG/evidence/2026-10-09-WPC-SOURCE-OF-TRUTH.md`; Paperclip issue IDs LOR-19 to LOR-26 and follow-up backlog LOR-27 to LOR-29. The latter are operational records, not automatically public evidence.
