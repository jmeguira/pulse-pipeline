# Pulse Check

**Signal-first video discovery, filtering, and compilation.**

Pulse Check is an internal, state-driven pipeline for tapping into internet throughput around a thematic cluster,
refining aggressively for signal, and producing compiled outputs. It is designed to be bounded, rerunnable, and boring
to operate.

---

## North Star

Build a rerunnable, signal-first content pipeline that discovers, filters, deduplicates, ranks, and compiles
high-quality short-form video into reusable outputs with minimal operator overhead.

---

## Mental Model (one line)

> **Discover broadly, filter hard, dedup aggressively, rank cleanly, commit late.**

---

## Pipeline Diagram

             ┌──────────┐
             │ Discover │
             └────┬─────┘
                  │
             ┌────▼─────┐
             │  Filter  │   (hard gates only)
             └────┬─────┘
                  │
             ┌────▼─────┐
             │  Dedup   │   (pool / history relative)
             └────┬─────┘
                  │
      ┌───────────▼───────────┐
      │  Acquisition Loop     │
      │  (repeat until pool   │
      │   ≥ candidate_goal)   │
      └───────────┬───────────┘
                  │
             ┌────▼─────┐
             │  Score   │   (never rejects)
             └────┬─────┘
                  │
             ┌────▼─────┐
             │  Select  │   (choose target_count)
             └────┬─────┘
                  │
      ┌───────────▼───────────┐
      │   Execution Stages    │
      │ Download → Preprocess │
      │        → Compile      │
      └───────────┬───────────┘
                  │
             ┌────▼─────┐
             │ Persist  │   (record provenance)
             └────┬─────┘
                  │
             ┌────▼─────┐
             │  Clean   │   (remove leftovers)
             └──────────┘

---

## Phase 0 — Foundations (Mostly Done)

**Goal:** Establish a stable, debuggable single-run pipeline with clear contracts.

- Sequential pipeline scaffold
- `Clip` + `ClipMetadata` as central domain objects
- `PipelineContext` (run_config + clips)
- Stage base class with clear contracts
- Download + preprocess robustness (file checks, failure logging)
- Compile MVP (title card, countdown, transitions)
- Handoff artifacts + initial architecture snapshot

---

## Phase 1 — Infra & Pipeline Hardening (Active)

**Goal:** Make the system boring, bounded, and safe to rerun.

### State & Contracts

- Explicit ClipState lifecycle
- Forward-only state transitions
- State-based include/exclude helpers (`clips_in_state`, `clips_not_in_state`)
- Stage-level `should_run()` for rerun safety where appropriate

### Discovery Hardening

- Bounded discovery via `candidate_goal = target_count * OVERSAMPLE`
- `MAX_PAGES` safety cap
- Deduplication by source ID during discovery (within-run)
- Atomic merge of newly discovered candidates with existing clip pool
- Explicit discovery exit reasons + diagnostics (evaluated / accepted / accept rate)

### Execution Safety

- Idempotent stages (skip when artifacts exist)
- No downstream stage may increase clip count after selection
- Runtime modes planned (ingest-only / compile-only / end-to-end)

---

## Phase 2 — Acquire: Discover, Filter, Dedup (Next)

**Goal:** Build a bounded acquisition loop that produces a sufficiently large, clean eligible pool for ranking and
selection.

### Discover

- Enumerate candidates and hydrate required metadata
- Bounded by `candidate_goal` and `MAX_PAGES`
- Output: `DISCOVERED` (preferred) or transitional candidate state

### Filter (Hard Gate)

- Pass/fail only (intrinsic constraints)
- Duration, age restriction, topic/keyword match, language sanity (optional)
- Record structured rejection reasons + counts
- Output: `ELIGIBLE`

### Dedup (Pool/History Gate)

- Separate from Filter (different semantics + future DB/persistence hooks)
- v0: cheap heuristics (e.g., normalized-title matching, pattern checks)
- v1: exact ID + pool-relative checks
- v2: optional persistence-backed checks (DB) and near-duplicate fingerprinting
- Output: `ELIGIBLE` (deduped pool)

### Acquisition Loop (State Machine)

- Loop **Discover → Filter → Dedup** until:
    - `len(ELIGIBLE_DEDUPED) >= candidate_goal`, or
    - bounds exhausted (`MAX_PAGES` / quotas / end of results)
- Persist “seen” memory across loop iterations (IDs/titles/fingerprints)

---

## Phase 3 — Rank & Commit: Score, Select (Next)

**Goal:** Rank a clean pool and commit resources only to the best clips.

### Score (Soft Ranking)

- Attach score components
- Never rejects
- Fully rerunnable
- Output: `ELIGIBLE` + score metadata

### Select

- Choose exactly `target_count`
- Output: `SELECTED`
- v0: simple sort + slice
- v1+: diversity, fatigue penalties, paradigm-aware selection

---

## Phase 4 — Execute: Download, Preprocess, Compile (Ongoing)

**Goal:** Artifact-producing stages that run only on `SELECTED`.

- Download: produce `DOWNLOADED`, idempotent via file existence checks
- Preprocess: produce `PROCESSED`, idempotent
- Compile: produce `COMPILED` output(s), deterministic ordering

---

## Phase 5 — Persist, Then Clean (Planned)

**Goal:** Record provenance and results, then safely remove run leftovers.

### Persist

- Persist run outcomes and provenance (metadata-first)
- Record: eligibility results, rejection reasons, dedup outcomes, scores, selection outcomes
- Record: output artifact paths, sizes/checksums (optional), failures
- Write-only initially; read-path added later with content pool

### Clean

- Remove temporary/intermediate artifacts safely
- Prune unselected downloads and partial/failed outputs
- Safe to skip during debugging
- Runs after Persist

---

## Phase 6 — Fingerprinting & Cross-Run Dedup (P0–P1)

**Goal:** Prevent repeats and near-duplicates across runs.

- Metadata similarity
- Perceptual frame hashing
- Optional audio fingerprinting
- Cross-run dedup once persistence exists

---

## Phase 7 — Persistence & Content Pool (P1)

**Goal:** Let clips outlive a single run.

- Metadata-first DB (SQLite MVP → Postgres)
- Write-only initially; read-path later
- Persist: eligibility, scores, selection outcomes, usage history
- Enable: pool reuse, fatigue penalties, cross-run dedup

---

## Phase 8 — Editorial & Output Polish (P1–P2)

**Goal:** Decouple video structure from ingestion logic.

- Explicit Curate / Editorialize stage
- Paradigms: countdown, thematic grouping, random montage
- Audio/visual polish
- Dual-format outputs (vertical + horizontal)

---

## Phase 9 — Orchestration & Scale (Future)

**Goal:** Move from single-run toolkit to continuous engine.

- Orchestration (cron / queue / workflow)
- Topic-based nugget engine
- Multi-source ingestion (optional)

---

## Engineering Level-Up (Cross-Cutting)

- Idempotent, resumable stages
- Structured per-run/per-stage logs
- Minimal tests (wiring, state transitions, date logic)
- Handoff-quality documentation

---

## Explicit Non-Goals (for now)

- Microservices-first architecture
- Premature ML-driven ranking
- Early read-path persistence
