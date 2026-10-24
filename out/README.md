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

### Platform scores

Each file in this folder was uploaded to the dev case on the submission platform on 24 Oct
2026, between 20:05 and 20:23 CEST. The requirement level is the platform's model judge.
Matched is recall times 190. The platform shows F1 for pages; page F2 here is computed from its
page precision and recall.

| File | Model | Requirements | Requirement P / R / F2 | Matched of 190 | Page P / R / F2 | Regulation P / R |
|---|---|---|---|---|---|---|
| `rear-lamp-deterministic.json` | None (deterministic) | 778 | 0.138 / 0.563 / **0.348** | 107 | 0.400 / 0.906 / 0.723 | 1.00 / 1.00 |
| `rear-lamp-sonnet.json` | Sonnet 5.5 | 344 | 0.407 / 0.737 / **0.634** | 140 | 0.817 / 0.925 / 0.901 | 1.00 / 1.00 |
| `rear-lamp-opus.json` | Opus 5.5 | 338 | 0.423 / 0.753 / **0.651** | 143 | 0.790 / 0.925 / 0.894 | 1.00 / 1.00 |
| `rear-lamp-fable.json` | Fable 5.1 | 332 | 0.449 / 0.784 / **0.682** | 149 | 0.781 / 0.943 / 0.905 | 1.00 / 1.00 |

All three models selected exactly the 4 expected regulations. Fable 5.1 scored highest on
requirements: 0.048 above Sonnet 5.5 for 5.4 times the cost, and 0.031 above Opus 5.5 for 2.6
times the cost. Opus 5.5 is 0.017 above Sonnet 5.5 for about twice the cost. These are single
runs, so read the gaps against the variance note below.

Where the extra matches come from, by the local judge (`brain/eval/judge.py`):

| Model | Rows from paragraphs not in the gold (match nothing) | Gold rows missed on a selected paragraph | Gold rows missed on a paragraph not selected |
|---|---|---|---|
| Sonnet 5.5 | 175 | 26 | 33 |
| Opus 5.5 | 160 | 37 | 14 |
| Fable 5.1 | 155 | 34 | 15 |

The stronger models choose paragraphs better: fewer wasted rows and fewer missed paragraphs.
The misses on selected paragraphs stay at 26 to 37 for every model. Those come from the
rewrite splitting less finely than the gold (one gold row per table row, list item or optional
case), which a larger model does not fix.

### Cost per run

From the pipeline logs (`rear-lamp-<model>.log`).

| Model | Calls | Tokens in / out | Cost |
|---|---|---|---|
| None (deterministic) | 0 | 0 | $0 |
| Sonnet 5.5 | 137 | 844k / 158k | $3.08 |
| Opus 5.5 | 138 | 867k / 159k | $6.36 |
| Fable 5.1 | 136 | 860k / 173k | $16.52 |

### Local proxy against the platform

The same files scored offline with `brain/eval/score.py`, next to the platform. The last row is
the earlier OpenAI upload (`brain/out/dev-upload.json`: gpt-5.5 relevance, gpt-5.4-mini
rewrite).

| File | Matched, platform | Matched, local judge | Requirement F2, platform | Requirement F2, local judge |
|---|---|---|---|---|
| `rear-lamp-deterministic.json` | 107 | 112 | 0.348 | 0.364 |
| `rear-lamp-sonnet.json` | 140 | 131 | 0.634 | 0.593 |
| `rear-lamp-opus.json` | 143 | 139 | 0.651 | 0.633 |
| `rear-lamp-fable.json` | 149 | 141 | 0.682 | 0.646 |
| `brain/out/dev-upload.json` | 145 | 138 | 0.621 | 0.591 |

The local judge ranks the three Claude runs in the platform's order. On model-written text it
finds 4 to 9 fewer matches than the platform; on the deterministic file's verbatim sentences it
finds 5 more. Use it to rank changes worth more than about 5 matches, and upload to the dev case
for closer calls. Regulation and page levels match the platform, since both use
`tools/score_local.py`.

### Which code produced the files

- **Claude runs:** commit `fd2777b` on branch `brain-claude-models` (troy, 24 Oct 19:58), which
  is `edc8f1f` on `main` plus the `BRAIN_MODEL` switch, streamed Claude requests and cost
  logging. The runs are from 19:49 to 19:57. The files moved here in `f018379` and reached
  `main` in `d730a11`; `5d9ae13` set `team_id` to `team-06` for the upload.
- **Deterministic run:** the no-LLM path at `edc8f1f`, which later commits on `main` have not
  changed. A rerun on `main` gives the same 778 requirements, row for row.
- **Prompts in these runs:** the domain-neutral relevance prompt with cut-off 0.20, and the
  rewrite prompt with parent clauses. Three of that rewrite prompt's four few-shot examples are
  dev gold answers (UN R48 6.4.4.2, UN R48 5.7.1, UN R150 4.1.1), which flatters the dev score by
  a few rows.

Each run's submission and log are in this folder: `rear-lamp-deterministic.json`, and
`rear-lamp-<model>.json` with `rear-lamp-<model>.log` (the pipeline log, which ends with the
token count and cost). All submissions pass `tools/validate.py`.

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

`BRAIN_MODEL` and the cost log exist only on branch `brain-claude-models` (`fd2777b`), not on
`main`. On `main`, set `BRAIN_MODEL_STRONG` and `BRAIN_MODEL_BULK` to the same model id instead;
the run then logs no cost.

From `brain/` on that branch, with `ANTHROPIC_API_KEY` and `BRAIN_LLM=anthropic` in `brain/.env`
(see `brain/.env.example`):

```bash
out=../out/rear-lamp-sonnet
BRAIN_MODEL=sonnet uv run python -m brain.pipeline ../cases/dev-rear-lamp -o $out.json 2> $out.log
uv run python ../tools/validate.py $out.json
uv run python ../tools/score_local.py $out.json
uv run python -m eval.score $out.json
```

`BRAIN_MODEL` takes `sonnet`, `opus`, `fable`, `haiku` or a full model id. A rerun reads the
cache and costs nothing; to measure a model again, move `brain/data/cache/llm` aside first.

Paid runs need the owner's approval and a cost estimate first (see `CLAUDE.md`). Measured cost
of one rear lamp run: Sonnet 5.5 about $3, Opus 5.5 about $6.50, Fable 5.1 about $16.50.
