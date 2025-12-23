# Product Roadmap — Pulse

---

## 🧭 Compass — Current Orientation

**What Pulse is**

- A system that **samples what’s resonating now** within a topic and renders it as video.
- Not predictive. Not exhaustive. **Observational and lightweight** by design.

**What matters right now**

- Maintain a **wide top-of-funnel** and learn from real outputs.
- Optimize for **signal discovery**, not framework completeness.
- Bias toward **shipping artifacts** over architectural elegance.

**What Pulse is not (yet)**

- Not a generalized engine for scale.
- Not a precision relevance model.
- Not an editorially perfected product.

**Operating principles**

- One run produces one video.
- Prefer derived state over duplicated counters.
- Expand scope **only at points of friction**.
- Treat search as a hinting system; shape downstream.
- Preserve readability to reduce cognitive load.

---

## Status Summary (Current)

- Pipeline **already produces and uploads videos**
- MVP script proven; pipeline formalized afterward
- Multiple successful end-to-end runs and uploads
- Current focus: **acquisition quality + control tightening**, not basic viability

---

## Phase 0 — MVP Proven (✅ Complete)

**Goal:** Prove end-to-end feasibility

- Single-script MVP:
    - Query YouTube
    - Download clips
    - Compile video
    - Upload successfully
- Manual configuration
- Multiple successful uploads

**Outcome:** System viability confirmed

---

## Phase 1 — Pipeline Formalization (✅ Largely Complete)

**Goal:** Turn MVP into a maintainable pipeline

- Stage-based pipeline introduced
- Context-driven execution
- Explicit orchestrator
- Acquire → Assemble flow
- Multiple verified pipeline states

**Outcome:** Working pipeline with clear structure

---

## Phase 2 — Acquisition Tightening (🟡 In Progress)

**Goal:** Improve top-of-funnel signal quality without narrowing too early

- Refined Discover stage:
    - Date-bounded popularity sampling
    - Shorts bias (`videoDuration="short"`)
    - Configurable ordering (`viewCount` vs `relevance`)
    - Language & region bias
- Introduced `keyword_config`:
    - Include / exclude terms
    - Composable query builder
- Clarified acquisition state:
    - `pages_processed`
    - `discovered`, `rejected`, `culled`
- Filter / Cull temporarily bypassable to preserve momentum

**Outcome:** Wide but better-shaped candidate pool

---

## Phase 3 — Signal Shaping (🔜 Next)

**Goal:** Reduce junk, improve consistency

- Implement Filter stage (cheap hard rejects)
- Implement Cull stage (run-scoped dedup)
- Minimal reason codes
- Persist `clips.json` for inspection

**Outcome:** Cleaner pool entering selection

---

## Phase 4 — Selection & Scoring Improvements (🔜 Later)

**Goal:** Pick better clips, not more clips

- Lightweight scoring (views/day, engagement ratios)
- Selection policies (top-N, simple diversity)
- Keyword-specific tuning

**Outcome:** Higher-quality compilations with minimal added complexity

---

## Phase 5 — Editorial & UX Polish (🟢 Optional / Later)

**Goal:** Improve viewer experience

- Title / description generation
- Transitions and pacing polish
- Intro / outro standardization
- Thematic consistency per keyword

---

## Explicit Non-Goals (for now)

- Large-scale engine optimization
- Persistent DB-backed history
- Full idempotency across reruns
- ML-based relevance models
- GUI tooling

These are **earned later**, not now.

---

## One-line internal definition

> Pulse samples what’s resonating now, renders it honestly, and gets out of the way.
