# Product Roadmap — Pulse

---

## 🧭 Compass — Current Orientation

**What Pulse is**

* A system that **samples what’s resonating now** within a topic and renders it as video.

* Not predictive. Not exhaustive. **Observational and lightweight** by design.

**What matters right now**

* Maintain a **wide top-of-funnel** and learn from real outputs.

* Optimize for **signal discovery**, not framework completeness.

* Bias toward **shipping artifacts** over architectural elegance.

**What Pulse is not (yet)**

* Not a generalized engine for scale.

* Not a precision relevance model.

* Not an editorially perfected product.

**Operating principles**

* One run produces one video.

* Prefer derived state over duplicated counters.

* Expand scope **only at points of friction**.

* Treat search as a hinting system; shape downstream.

* Preserve readability to reduce cognitive load.

---

## Status Summary (Current)

* Pipeline **runs end-to-end and produces final artifacts**

* Clip lifecycle fully formalized through persistence

* Multiple validated full runs after orchestration + discovery refactor

* Current focus: **acquisition quality, selection boundaries, and observability**, not core viability

---

## Phase 0 — MVP Proven (✅ Complete)

**Goal:** Prove end-to-end feasibility

* Single-script MVP:

    * Query YouTube

    * Download clips

    * Compile video

    * Upload successfully

* Manual configuration

* Multiple successful uploads

**Outcome:** System viability confirmed

---

## Phase 1 — Pipeline Formalization (✅ Complete)

**Goal:** Turn MVP into a maintainable pipeline

* Stage-based pipeline introduced

* Context-driven execution

* Explicit orchestrator

* Acquire → Assemble flow

* Clip lifecycle states implemented to date:

    * `DISCOVERED → ELIGIBLE → SELECTED → DOWNLOADED → TRANSFORMED → COMPILED`

* Acknowledged expanded lifecycle (not fully implemented; subject to merge/mutation):

    *
    `DISCOVERED → FILTERED → CULLED → ELIGIBLE → SCORED → RANKED? → SELECTED → DOWNLOADED → TRANSFORMED → COMPILED → PERSISTED → CLEANED`

**Outcome:** Working pipeline with explicit contracts and durable boundaries

---

## Phase 2 — Acquisition Tightening (🟢 Complete)

**Goal:** Improve top-of-funnel signal quality without narrowing too early

* Introduced **stage groups** as hard invariants:

    * `DISCOVER / ASSEMBLE / PERSIST`
    * Groups represent **cost domains**, not descriptions
    * Enforced at class-definition time

* Refined DISCOVER loop:

    * Date-bounded popularity sampling
    * Shorts bias (`videoDuration="short"`)
    * Configurable ordering (`viewCount` vs `relevance`)
    * Language & region bias

* Implemented **Acquire / Discover loop**:

    * DISCOVER stages run until pool is “full”
    * Pool pruned to evaluation-eligible
    * Explicit awareness of DISCOVER → ASSEMBLE handoff (scoring/ranking treated as tech debt)

* `keyword_config` in continuous use since initial pipeline refactor:

    * Include / exclude terms
    * Composable query builder
    * Serves as the primary acquisition-shaping surface

* Clarified acquisition state:

    * `cursor`
    * `pages_processed`
    * `discovered`, `rejected`, `culled`

* Implemented **`clips.json`** artifact:

    * Written once at DISCOVER loop exit
    * Idempotent, overwritten each run
    * Explicit serialization (`to_dict`, not `__repr__`)
    * Human-inspectable (clickable links) for rapid judgment

**Outcome:** DISCOVER is fast, inspectable, and human-in-the-loop by default

---

## Phase 2.5 — Hardening & Extensibility (🟡 Active)

**Goal:** Stabilize control surfaces before expanding capability

* Flags-first execution model:

    * Centralized `flags.json` → `RuntimeFlags` → `ctx.flags`
    * Flags as the primary lens for behavior changes

* Logging infrastructure (in progress):

    * Log levels: `QUIET / NORMAL / DEBUG / TRACE`
    * `ctx.log`, `ctx.debug`, `ctx.error`, `ctx.trace`
    * Stage-level logging via DEBUG; clip-level via TRACE

* Exception handling standardization (in progress):

    * Stage wrapper with consistent try/except
    * Per-clip wrapper for partial failure tolerance
    * Single `strict` / `fail_fast` semantic

* Execution gating:

    * `dry_run` semantics locked (`DISCOVER` only)
    * Future generalization via stage-group gating

**Outcome (target):** Predictable behavior, legible runs, and safe iteration velocity

---

## Phase 3 — Selection & Pool Shaping (🟡 In Progress)

**Goal:** Control volume and intent before execution

* Introduced `SELECTED` as a hard execution boundary

* Acquire fills to **candidate goal**, not target count

* Select trims to **exact target count** (temporary heuristic: view count)

* Download and downstream stages consume **only `SELECTED`**

**Outcome:** Candidate inventory decoupled from execution volume

---

## Phase 4 — Signal Shaping & Scoring (🔜 Next)

**Goal:** Reduce junk, improve consistency

* Implement Filter stage (cheap hard rejects)

* Implement Cull stage (run-scoped dedup)

* Minimal reason codes for rejection

* Persist `clips.json` / run artifacts for inspection

**Outcome:** Cleaner, more explainable pool entering selection

---

## Phase 5 — Selection Quality Improvements (🔜 Later)

**Goal:** Pick better clips, not more clips

* Lightweight scoring (views/day, engagement ratios)

* Simple diversity constraints

* Keyword-specific tuning

**Outcome:** Higher-quality compilations with minimal added complexity

---

## Phase 6 — Editorial & UX Polish (🟡 Required if Shipping)

**Goal:** Improve viewer experience

* Title / description generation

* Transitions and pacing polish

* Intro / outro standardization

* Thematic consistency per keyword

---

## ⚠️ Deferred, Non-Goals, and Open Design Space

This section intentionally aggregates:

* explicit non-goals (for now)
* known risks and accepted debt
* future ideas that do not yet justify a phase

**Explicit non-goals (current):**

* Large-scale engine optimization
* Persistent DB-backed history
* Full idempotency across reruns
* ML-based relevance models
* GUI tooling

**Known risks / accepted debt:**

* Exception handling semantics still stabilizing
* Adaptive harvesting logic partial and stage-local
* Selection heuristic intentionally naive
* Determinism across reruns not guaranteed
* Observability flags partially wired

**Deferred future ideas / ops surface:**

* CLI overrides for flags and high-level run intent
* Config layering cleanup (`.env` for secrets / machine state, JSON for run intent)
* Resolved-run snapshot for reproducibility
* Stage-group gating generalization beyond `dry_run`
