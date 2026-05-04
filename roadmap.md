# Roadmap — Pulse

> **Archived.** This is the build log as it stood when I closed the project.
> Phases marked in-progress were the live work at the time of archive, not
> ongoing commitments.

---

## Orientation (at archive)

**What Pulse was**

- A system that **samples what's resonating within a defined time window** for a topic and renders it as video.
- **Observational, time-bounded, and lightweight** by design.
- Built to explore **theme × time slices**, not to declare importance or predict outcomes.

**What it was not**

- Not a generalized or scalable engine.
- Not a recommendation or relevance model.
- Not an editorial or personality-driven product.
- Not an automated publishing machine.

**Operating principles**

- One run → one artifact.
- Prefer **derived state** over persistent counters.
- Expand scope **only at points of observed friction**.
- Treat search and acquisition as **hinting systems**, not ground truth.
- Preserve legibility to minimize cognitive and operational load.
- Favor **clean exits and explicit stopping points**.

---

## Status at archive

- Pipeline ran **end-to-end** and produced inspectable artifacts.
- DISCOVER loop was fast, configurable, and human-inspectable.
- Execution volume controlled via an explicit `SELECTED` boundary.
- Infra, logging, flags, and failure semantics stable.
- Live work at the time of stopping:
    - **Acquisition tightening** (Phase 4)
    - **Editing subtraction / simplification** (Phase 5)

---

## Phase 0 — MVP Proven (✅ Complete)

**Goal:** Prove end-to-end feasibility

- Query YouTube
- Download clips
- Compile video
- Upload manually

**Outcome:** System viability confirmed.

---

## Phase 1 — Pipeline Formalization (✅ Complete)

**Goal:** Create durable structure without over-engineering

- Stage-based pipeline
- Explicit orchestrator
- Acquire → Assemble flow
- Clip lifecycle implemented (MVP)
- Contracts acknowledged for future expansion

**Outcome:** Maintainable, legible pipeline.

---

## Phase 2 — Acquisition Tightening (🟢 Complete)

**Goal:** Improve top-of-funnel signal quality without narrowing prematurely

- Stage groups enforced: `DISCOVER / ASSEMBLE / PERSIST`
- Date-bounded popularity sampling
- Shorts bias and configurable ordering
- Language & region bias
- `keyword_config` as primary acquisition surface
- Explicit acquisition state tracking
- `clips.json` artifact for human inspection

**Outcome:** DISCOVER is fast, inspectable, and human-in-the-loop.

---

## Phase 2.5 — Hardening & Extensibility (🟢 Complete)

**Goal:** Stabilize control surfaces before expanding capability

- Flags-first execution model
- Unified logging with levels
- Per-stage and total timing
- Standardized exception handling
- Clear execution gating (`dry_run` limited to DISCOVER)

**Outcome:** Stable infra with clean failure semantics and low cognitive overhead.

---

## Phase 3 — Selection & Pool Shaping (🟢 Complete — MVP)

**Goal:** Control execution volume independently of discovery volume

- Introduced `SELECTED` as a hard execution boundary
- Acquire fills to **candidate goal**
- Select trims to **exact execution target** (temporary heuristic)
- Downstream stages consume only `SELECTED`

**Outcome:** Execution volume decoupled from discovery.

---

## Phase 4 — Signal Shaping & Acquisition Refinement (🟢 In Progress)

**Goal:** Reduce junk and repetition before execution

**Active work**

- Implement **FILTER** stage (cheap hard rejects)
- Implement **CULL** stage (run-scoped dedup)
- Minimal reason codes for rejection
- Cleaner, more legible pools entering selection

**Notes**

- No scoring or ranking yet
- No persistence beyond run artifacts
- Focus is clarity, not correctness

---

## Phase 5 — Compilation Simplification (🟢 In Progress)

**Goal:** Remove value-negative editing work

**Authoritative editing baseline**

**Keep**

- Minimal logo watermark (small, static)
- Creator attribution (format TBD)

**Remove**

- Thumbnail generation
- Title cards
- Transitions
- Countdowns
- Outros / end slates

**Outcome:** Compilation acts as a neutral container, not a performance.

---

## Phase 6 — Selection Quality Improvements (🔜 Later)

**Goal:** Pick better clips, not more clips

- Lightweight scoring (views/day, engagement ratios)
- Simple diversity constraints
- Keyword-specific tuning

**Prerequisites**

- Phase 4 + Phase 5 complete
- Observed friction justifies complexity

---

## ⚠️ Parked / Deferred Work (Explicit)

These are intentionally parked, not abandoned:

- Duration-based targeting (≈15–20 minutes)
- Niche discovery and demand analysis
- Top-down trend tooling
- Publishing automation
- Thumbnail / title optimization
- Persistent DB-backed history
- ML-based relevance models
- GUI tooling

---

## Known Risks / Accepted Debt

- Adaptive harvesting logic partial and stage-local
- Selection heuristic intentionally naive
- Determinism across reruns not guaranteed
- `profile` and `save_intermediates` flags available but not activated
- No orchestration re-entry from downstream when pool is thin

---

## Deferred Future Ideas / Ops Surface

- CLI overrides for flags and high-level run intent
- Config layering cleanup (`.env` for secrets / machine state, JSON for run intent)
- Resolved-run snapshot for reproducibility
- Stage-group gating generalization beyond `dry_run`

---

## Priority window at archive

1. Phase 4 — FILTER + CULL
2. Phase 5 — Editing subtraction
3. Ship artifacts, observe friction
4. Re-evaluate next expansion point

The re-evaluation in step 4 is what closed the project: the architecture had
landed where I wanted it, and the next interesting questions were no longer
about the pipeline.
