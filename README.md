# Pulse

A state-driven pipeline that samples short-form video around a theme inside a
time window, filters aggressively for signal, and renders the result into a
single compiled artifact.

> **Status: archived.** Pulse ran end-to-end and produced real output. I closed
> it as an experiment after Phase 4 — the architecture got where I wanted it
> to, and the next interesting questions were no longer about the pipeline.

---

## What it actually does

Given a keyword and a date range, Pulse:

1. Searches YouTube for short-form videos published inside the window
2. Hydrates each candidate with full metadata (duration, language, region, licensing, age gates)
3. Filters out anything that fails hard constraints
4. Culls non-English and intra-run duplicates
5. Selects exactly `target_count` clips for execution
6. Downloads, normalizes audio, transforms to a standard frame, and compiles into one video
7. Writes a `clips.json` provenance record next to the output

One run, one artifact. Configurable by `.env` and `flags.json`. Inspectable
between stages. Boring to rerun.

---

## Why I built it the way I did

The interesting design problem here was not "can you stitch videos together"
— that's a weekend. It was: how do you build a pipeline against an *infinite,
noisy* source where most of the work is throwing things away, and you need to
stay sane when reruns disagree with each other?

The shape of the answer ended up being:

**Separate the questions, one per stage.**
Each stage answers exactly one thing: *what exists?*, *what's allowed?*,
*have we seen this before?*, *how good is it?*, *what's worth working on?*.
Mixing those questions is what makes pipelines unmaintainable.

**Judgment enters late.**
Hard gates first (Filter), ranking later (Score), resource commitment last
(Select → Download). Anything expensive happens after the cheap rejections.
This is also why Score is forbidden from rejecting — it would re-tangle the
gating contract.

**Bound the discovery loop.**
The internet is infinite; discovery has to stop somewhere on purpose.
`target_count × OVERSAMPLE = candidate_goal`, capped by `MAX_PAGES`. Every
run logs why it stopped (goal hit, page cap, end of results) so a low-yield
run is diagnosable instead of mysterious.

**Make state explicit.**
Every clip is in exactly one `ClipState` at any time. Stages declare which
state they consume and which they produce. A clip going from `DISCOVERED` to
`COMPILED` leaves a trail of state transitions, not vibes.

**Reruns are a feature, not an emergency.**
Persist before clean. Stages don't clobber unrelated state. Idempotency is
the default rather than an afterthought.

---

## Pipeline shape

```
   ┌──────────── acquisition loop ─────────────┐
   │                                           │
   ▼                                           │
Discover ──► Filter ──► Cull ──► (goal hit?) ──┘
                                     │
                                     ▼
                                  Score
                                     │
                                     ▼
                                  Select
                                     │
                                     ▼
                          Download ──► Transform ──► Compile
                                                       │
                                                       ▼
                                                    Persist
```

Acquisition keeps looping until the eligible pool reaches `candidate_goal`,
the page cap is hit, or YouTube runs out of results. Only then does the run
spend money on downloads.

---

## Repository layout

- `domain/` — `Clip`, `ClipState`, `ClipMetadata`, `PipelineContext`, run config, runtime flags
- `stages/` — one file per pipeline stage; each implements the `Stage` contract
- `clients/` — YouTube API wrapper with retry/backoff
- `config/` — keyword configuration (the primary acquisition surface)
- `utils/` — shared helpers (date logic, prompts, compile/preprocess utilities)
- `main.py` — entrypoint and stage orchestrator
- `roadmap.md` — phase-by-phase build log and parked work

---

## What I'd do next (if I picked it back up)

The roadmap captures the full list, but the live ones at archive time were:

- **Selection quality** — moving from a naive heuristic to lightweight scoring
  (views/day, engagement ratios) and basic diversity constraints. The scaffolding
  is in place; the policy isn't.
- **Editing subtraction** — Phase 5 was halfway through stripping value-negative
  edit work (title cards, transitions, countdowns) so compilation could become a
  neutral container instead of a performance.
- **Determinism across reruns** — accepted debt; the pipeline is rerun-*safe*
  but not yet rerun-*identical*.

---

## Naming

"Pulse" is a working name. It implies tuning for signal, not branding
commitment.
