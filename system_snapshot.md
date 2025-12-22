# Pulse Check — One-Page System Snapshot

## Purpose

Pulse Check is an **internal, state-driven content pipeline** that ingests high-throughput internet video around a
thematic cluster, aggressively refines for signal, and produces compiled outputs. Reliability, bounded behavior, and
rerun safety take precedence over polish.

---

## Execution Model

- **Single-run, operator-driven**
- **Sequential stages**
- **Explicit ClipState transitions**
- **Bounded acquisition loop**

All run-scoped data flows through a shared `PipelineContext`.

---

## Core Objects

**PipelineContext**

- `run_config`
- `clips` (working set)

**Clip**

- source
- state (`ClipState`)
- metadata (`ClipMetadata`)
- artifact paths (as produced)

**ClipState (conceptual)**
DISCOVERED → ELIGIBLE → SELECTED → DOWNLOADED → PROCESSED → COMPILED
REJECTED / FAILED (terminal)

States define stage contracts, not UI meaning.

---

## Pipeline (Current Design)

Discover
→ Filter
→ Dedup
→ Score
→ Select
→ Download
→ Preprocess
→ Compile
→ Persist
→ Clean


---

## Stage Responsibilities

- **Discover** — enumerate + hydrate candidates (bounded)
- **Filter** — hard pass/fail only (intrinsic constraints)
- **Dedup** — remove repeats relative to pool/history
- **Score** — attach score components (never rejects)
- **Select** — choose exactly `target_count`
- **Download / Preprocess / Compile** — artifact-producing, idempotent
- **Persist** — record run outcomes and provenance
- **Clean** — remove temporary/intermediate artifacts (after Persist)

---

## Acquisition Loop

Loop **Discover → Filter → Dedup** until:

- eligible deduped pool ≥ `candidate_goal`, or
- bounds exhausted

Only then proceed to Score and beyond.

---

## Discovery Bounds & Safety

- `target_count`
- `OVERSAMPLE`
- `candidate_goal = target_count * OVERSAMPLE`
- `MAX_PAGES`
- `batch_size`

Diagnostics per run:

- evaluated count
- accepted count
- accept rate
- explicit exit reason

---

## Rerun Safety Invariants

- Discovery is always bounded
- Filter is hard-gate only; Score never rejects
- Clip count may only shrink after Filter and Select
- Execution stages must be idempotent
- Persist runs **before** Clean
- Stages must not clobber unrelated clip states

---

## Design Philosophy

- Signal > volume
- Separate discovery, judgment, and execution
- Bounded loops over infinite sources
- Boring reruns are success
- Clarity over cleverness

---

## Status

Internal system under active development.
Public exposure is optional and explicitly out of scope for now.
