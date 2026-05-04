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

## What I ran into

The hardest part of this project wasn't the pipeline — it was the upstream.

YouTube's Data API and discovery surface are not built for what Pulse is
trying to do. They're built for "find videos like the ones this user already
watches," not "give me a clean cross-section of what's resonating around a
theme in a time window." A few things that came out of running this for
real:

- **Rate limits bite before signal does.** The daily quota is generous on
  paper but tight in practice once you're hydrating full metadata for every
  candidate. I was getting throttled before I'd combed through enough
  candidates to find the viable ones.
- **The result set is mostly slop.** Across keywords, the accept rate after
  hard gates was low. Discovery returns a lot of recycled, low-effort, or
  off-theme content even with date and language constraints. The
  oversample-then-filter design exists because the noise floor is that high.
- **Discovery actively works against this use case.** Search results lean
  heavily on engagement and personalization signals that you can't really
  turn off. Asking "what's resonating *in this window*, independent of who
  I am" is not a query the API really wants to answer — you can approximate
  it with `order=date` + region + language, but you're working around the
  product, not with it.

None of this is a complaint about YouTube — they have no incentive to make
bulk theme-sampling easy. But it's the reason a lot of the architectural
choices here are defensive: bound everything, fail loud when the funnel
underperforms, and assume the upstream is going to push back.

This was also the decision point that closed the project. The obvious next
move to push past the funnel limits would have been to lean on scraping,
rotating identities, or other gray-area workarounds. Each of those would
have traded a repeatable, well-behaved system for a brittle one whose
correctness depended on staying one step ahead of detection. I wasn't
willing to make that trade — the value of Pulse was in the architecture and
the artifacts it produced, not in winning an arms race against a platform
I had no business fighting.

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
