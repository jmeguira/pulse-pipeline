# Pulse Check

**Signal-first video discovery, filtering, and compilation.**

Pulse Check is an internal, operator-driven content pipeline designed to tap into internet throughput around a specific
thematic cluster, refine the signal, and produce high-quality compiled outputs. Public consumption is optional and
explicitly not the goal at this stage.

---

## What this is

Pulse Check is a **single-run, state-driven pipeline** that:

- discovers candidate short-form video content,
- filters and deduplicates aggressively,
- scores and selects only what’s worth spending resources on,
- executes expensive steps deterministically,
- records provenance,
- and cleans up after itself.

It is built to be **boring to rerun**, diagnosable when it fails, and extensible without refactoring the core.

---

## Core principles

- **Signal > volume**
  The internet is infinite; discovery must be bounded and intentional.

- **Separate the questions**
  Each stage answers exactly one question:
    - *What exists?*
    - *What is allowed?*
    - *Have we seen this before?*
    - *How good is it?*
    - *What is worth doing work on?*

- **Judgment enters late**
  Hard gates first, ranking later, resource commitment last.

- **Rerun safety is a feature**
  Idempotency and explicit state transitions are not optional.

---

### Stage intent (brief)

- **Discover** — enumerate and hydrate candidates (bounded)
- **Filter** — hard pass/fail gates only
- **Dedup** — remove repeats relative to pool/history
- **Score** — attach score components (never rejects)
- **Select** — choose exactly `target_count`
- **Download / Preprocess / Compile** — artifact-producing execution
- **Persist** — write run outcomes and provenance
- **Clean** — remove temporary/intermediate artifacts

---

## Core domain objects

- **Clip**
  Run-scoped unit of content carrying source, metadata, lifecycle state, and artifact paths.

- **ClipState**
  Defines stage contracts and lifecycle transitions.

- **PipelineContext**
  Holds run configuration and the working clip set for the entire run.

---

## Discovery bounds

Pulse Check enforces explicit limits to prevent runaway ingestion:

- `target_count` — how many clips you ultimately want
- `OVERSAMPLE` — multiplier to ensure a sufficient candidate pool
- `candidate_goal = target_count * OVERSAMPLE`
- `MAX_PAGES` — hard cap on discovery pagination

Diagnostics (evaluated count, accepted count, accept rate) are logged to explain low-yield runs.

---

## Invariants / guardrails

- Discovery is always bounded.
- Filter is hard-gate only; Score never rejects.
- Clip count may only shrink after Filter and Select.
- Execution stages must be idempotent.
- Persist runs **before** Clean.
- Stages must not clobber unrelated clip states on rerun.

---

## Repository structure (high level)

- `domain/` — Clip, ClipState, metadata, stage contracts
- `stages/` — pipeline stage implementations
- `config/` — run configuration and defaults
- `utils/` — shared helpers (date logic, matching, etc.)
- `docs/` — architecture and roadmap
- `main.py` — pipeline entrypoint

---

## Status

This project is **actively evolving** and intentionally internal.
The north star is a sharp, reliable content pipeline. Everything else is secondary.

---

## Naming note

“Pulse Check” is a working name used to replace placeholders and clarify documentation.
It implies *tuning for signal*, not branding commitment.
