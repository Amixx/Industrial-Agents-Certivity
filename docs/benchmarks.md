# Benchmarks

How well the requirement engine (`brain/`) does on the rear lamp case with different language
models, and what each run costs. Add a row whenever you benchmark a new model or a change
that affects the score.

## What is measured

**Case.** The rear lamp (`cases/dev-rear-lamp`) is the only case with expert answers: 190
requirements from 4 regulations (R148, R48, R150, R10) on 53 pages. Every run below is one
full pass on that case.

**The loop.** One run is:

1. `brain.pipeline` reads the spec and the exploded view and writes the submission JSON.
2. `tools/validate.py` checks the file against the platform format.
3. `tools/score_local.py` scores regulation and page level against `expected.json`.
4. `brain/eval/score.py` adds F2 and the requirement-level proxy.

**Scores.** The judges use F2, which weights recall four times as much as precision: a missed
requirement costs more than an extra one. All scores in the tables are F2.

| Level | What counts as a match | Scored by |
|---|---|---|
| Regulation | The cited regulation is in the answer | `tools/score_local.py` (official matching) |
| Page | Same regulation, version and page, or the same paragraph | `tools/score_local.py` (official matching) |
| Requirement | The requirement says the same thing as an expected one | The platform's LLM judge, after upload |

The requirement score in the tables is a local stand-in for the platform judge
(`brain/eval/judge.py`): word overlap within the same regulation, zero for opposite meaning,
a penalty for mismatched numbers. Use it to compare our own runs, not as the platform score.

**Cost.** The pipeline logs the tokens and dollars of every run. Responses are cached in
`brain/data/cache/llm/`, so rerunning a step is free, and the cost reported for a rerun is
what the cached responses cost when they were made. List prices in USD per million tokens:

| Model | Input | Output | Cache read |
|---|---|---|---|
| Claude Sonnet 5.5 (`claude-sonnet-5-5`) | 2 | 10 | 0.20 |
| Claude Opus 5.5 (`claude-opus-5-5`) | 4 | 20 | 0.20 |
| Claude Fable 5.1 (`claude-fable-5-1`) | 10 | 50 | 0.25 |

## Results

Each Claude row runs one model on every step: product profile, regulation review, paragraph
relevance and rewrite. Relevance cut-off 0.20.

| Date | Model | Requirements | Regulation F2 | Page F2 | Requirement F2 (proxy) | Requirement recall | Calls | Tokens in / out | Cost |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-24 | None (deterministic) | 778 | 1.000 | 0.723 | 0.364 | 0.589 | 0 | 0 | $0 |
| 2026-10-24 | Sonnet 5.5 | 344 | 1.000 | 0.901 | 0.593 | 0.689 | 137 | 844k / 158k | $3.08 |
| 2026-10-24 | Opus 5.5 | 338 | 1.000 | 0.894 | 0.633 | 0.732 | 138 | 867k / 159k | $6.36 |
| 2026-10-24 | Fable 5.1 | 332 | 1.000 | 0.906 | 0.646 | 0.742 | 136 | 860k / 173k | $16.52 |

All three models selected exactly the 4 expected regulations. Fable 5.1 scored highest on every
level and missed the fewest requirements (49 of 190, against 51 for Opus 5.5 and 59 for Sonnet
5.5), at about 2.6 times the cost of Opus. Opus 5.5 is 0.04 above Sonnet 5.5 on requirement F2
for about twice the cost. These are single runs, so read the gaps against the variance note
below.

Saved outputs: `brain/out/dev-rear-lamp.json` (deterministic) and `brain/out/dev-<model>.json`.
All of them pass `tools/validate.py`.

### Earlier run

`brain/out/dev-llm.json` came from an older version of the pipeline: Opus for profile,
review and relevance with cut-off 0.10, and Sonnet for the rewrite. It selected R26 as a fifth
regulation. Rescored with today's proxy: regulation F2 0.952, page F2 0.877, requirement F2
0.591, requirement recall 0.726. Its cost was not tracked.

## Run-to-run variance

The same model on the same case does not give the same output. A first Sonnet 5.5 run cited
69 pages (page F2 0.872) where the run in the table cited 60 (page F2 0.901). Treat
differences of a few points between single runs as noise. For a decision that depends on a
small gap, run each model more than once on fresh caches.

## Reproduce

From `brain/`, with `ANTHROPIC_API_KEY` and `BRAIN_LLM=anthropic` in `brain/.env` (see
`brain/.env.example`):

```bash
BRAIN_MODEL=sonnet uv run python -m brain.pipeline ../cases/dev-rear-lamp -o out/dev-sonnet.json
uv run python ../tools/validate.py out/dev-sonnet.json
uv run python ../tools/score_local.py out/dev-sonnet.json
uv run python -m eval.score out/dev-sonnet.json
```

`BRAIN_MODEL` takes `sonnet`, `opus`, `fable`, `haiku` or a full model id. A rerun reads the
cache and costs nothing; to measure a model again, move `brain/data/cache/llm` aside first.

Paid runs need the owner's approval and a cost estimate first (see `CLAUDE.md`). Measured cost
of one rear lamp run: Sonnet 5.5 about $3, Opus 5.5 about $6.50, Fable 5.1 about $16.50.
