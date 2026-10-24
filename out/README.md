# Benchmarks

How well the requirement engine (`brain/`) does on the rear lamp case with different language
models, and what each run costs. Every benchmark run gets a row in the run log below, on any
branch, and a dated section under Results that says what changed. When a file is uploaded,
add the platform's scores and the upload time to its row and section (see `AGENTS.md`).

## Run log

All times 24 Oct 2026, CEST. Local scores use `brain/eval/score.py` (matched of 190 expert
rows, requirement F2). Platform matched is recall times 190. Code names the commit or branch
that produced the file; branch code is not on `main` unless it says so.

| Run | File | Method | Code | Rows | Local matched / F2 | Platform (upload): matched / F2 | Spend |
|---|---|---|---|---|---|---|---|
| before 18:45 | `brain/out/dev-upload.json` | gpt-5.5 relevance, gpt-5.4-mini rewrite; cited R26 too | `main` | 407 | 138 / 0.591 | (18:45) 145 / 0.621 | not logged |
| 19:49 to 19:57 | `rear-lamp-sonnet.json` | Sonnet 5.5 on every step | `brain-claude-models` @ `fd2777b` | 344 | 131 / 0.593 | (20:10) 140 / 0.634 | $3.08 |
| 19:49 to 19:57 | `rear-lamp-opus.json` | Opus 5.5 on every step | `brain-claude-models` @ `fd2777b` | 338 | 139 / 0.633 | (20:06) 143 / 0.651 | $6.36 |
| 19:49 to 19:57 | `rear-lamp-fable.json` | Fable 5.1 on every step | `brain-claude-models` @ `fd2777b` | 332 | 141 / 0.646 | (20:05) **149 / 0.682**; (20:04, as team-00) 142 / 0.650 | $16.52 |
| | `rear-lamp-deterministic.json` | No LLM | `edc8f1f` | 778 | 112 / 0.364 | (20:23) 107 / 0.348 | $0 |
| | `rear-lamp-main-cli.json` | `main` at `7644efe`: Opus relevance, Sonnet rewrite, through `claude -p` | `kb-stack` | 368 | | (21:05 to 22:16) 143 / 0.634 | subscription |
| | `rear-lamp-kb-deterministic.json` | Obligation base, no LLM | `kb-stack` | 864 | | (21:05 to 22:16) 108 / 0.333 | $0 |
| | `rear-lamp-kb-jev.json` | Obligation base, Jev blend cut 0.25, Opus everywhere | `kb-stack` @ `5f6e476` | 389 | | (21:05 to 22:16) 154 / 0.670 | subscription |
| | `rear-lamp-kb-jev-filter-v4.json` | The above plus requirement filter and minimal-edit rewrite | `kb-stack` @ `1d8b22e` | 342 | / 0.717 | (21:05 to 22:16) 140 / 0.635 | subscription |
| | `rear-lamp-kb-sol-rewrite.json` | Paragraphs of `kb-jev` rewritten by GPT-6.1 Sol | `kb-stack` | 420 | | (21:05 to 22:16) 143 / 0.606 | subscription |
| | `rear-lamp-qwen-split-rewrite.json` | Fable's 208 paragraphs rewritten by qwen3.5:9b, split prompt of `0ccae35` | `dcf1740` | 446 | 137 / 0.568 | (21:47) 133 / 0.551 | $0 |
| 22:00 | `rear-lamp-mix-examples-cut.json` | Opus relevance, Sonnet rewrite with expert examples and the obligation cut | `brain-model-mix-examples` @ `e5e0d25` | 341 | 145 / 0.658 | (22:14) 138 / 0.627 | $1.13 |
| 22:45 | `rear-lamp-kb-v5-rewrite.json` | Paragraphs of `kb-jev` rewritten by Opus; prompt names the device and repeats the condition in every row | `kb-stack` @ `1d8b22e` plus an uncommitted prompt | 363 | 158 / 0.703 | (22:48) 148 / 0.659 | subscription |
| 21:55 | `rear-lamp-deterministic-sibling.json` | No LLM, with sibling routing and the regulation-title rule; decision model refit | `main` @ `b7d6ee2` (reproduced at `a39acab`) | 647 | 111 / 0.394 | (22:57) 106 / 0.377 | $0 |
| 21:33 to 22:14 | `rear-lamp-qwen-split2-rewrite.json` | Fable's 208 paragraphs rewritten by qwen3.5:9b, narrowed table rule and empty-answer fallback | `main` @ `d7683cd`, `eval.rewrite_pass` | 411 | 143 / 0.611 | | $0 |
| 22:15 to 22:28 | `rear-lamp-gemini-relevance.log` | Relevance only: gemini-3.8-flash (free tier) on 425 dev paragraphs; AUC 0.998 (gpt-5.5 0.987) | `main` @ `bb829ec`, `out/scripts/gemini_relevance.py` | n/a | | | $0 |
| 22:30 to 22:49 | `rear-lamp-gemini-relevance.log` | Relevance only: gemini-3.5-flash (free tier) on 1,100 dev paragraphs; AUC 0.974 (gpt-5.5 0.968) | `main` @ `bb829ec`, `out/scripts/gemini_relevance.py` | n/a | | | $0 |

Empty cells were not recorded when the run was made.

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

### Rewrite-only runs

These hold paragraph selection fixed: they rewrite exactly the 208 paragraphs that
`rear-lamp-fable.json` cites, with a different model or prompt (`brain/eval/rewrite_pass.py`),
so the gap to the Fable row is the rewrite alone.

| File | Rewrite | Requirements | Requirement P / R / F2 | Matched of 190 | Page P / R / F2 | Uploaded |
|---|---|---|---|---|---|---|
| `rear-lamp-qwen-split-rewrite.json` | qwen3.5:9b on Ollama, split prompt of `0ccae35` | 446 | 0.298 / 0.700 / **0.551** | 133 | 0.820 / 0.943 / 0.916 | 24 Oct 21:47 CEST |

- Against Fable's own rewrite of the same paragraphs (0.682, 149 matches) it loses 0.131. It
  writes 34% more rows and matches 16 fewer requirements.
- The prompt of `0ccae35` told the model to split every row of a table. On qwen that turned
  table references into dozens of rows with garbled cell values (UN R148 5.5.1, one gold row,
  became 25) and left 30 of the 208 paragraphs empty, five of them gold. `d7683cd` keeps table
  references whole and falls back to the deterministic rows for an empty answer.
- The run took 37 minutes on an M5 with 16 GB (52 batches of 4 paragraphs, temperature 0,
  thinking off) and cost nothing.

### Branch `kb-stack` runs

Uploaded on 24 Oct between 21:05 and 22:16 CEST. Every LLM step ran through `claude -p` or
`codex exec` on a subscription, so the dollar figures in the logs are what `claude -p` reports,
not a bill. Code is on branch `kb-stack` (not merged).

| File | Configuration | Requirements | Requirement P / R / F2 | Matched of 190 | Page P / R / F1 |
|---|---|---|---|---|---|
| `rear-lamp-main-cli.json` | `main` at `7644efe`: Opus relevance, Sonnet rewrite | 368 | 0.389 / 0.753 / **0.634** | 143 | 0.806 / 0.943 / 0.870 |
| `rear-lamp-kb-deterministic.json` | obligation base, no LLM | 864 | 0.125 / 0.568 / **0.333** | 108 | 0.418 / 0.925 / 0.576 |
| `rear-lamp-kb-jev.json` | `5f6e476`: obligation base, Jev blend cut 0.25, Opus everywhere | 389 | 0.396 / 0.811 / **0.670** | 154 | 0.781 / 0.943 / 0.855 |
| `rear-lamp-kb-jev-filter-v4.json` | `1d8b22e`: the above plus the requirement filter and the minimal-edit rewrite | 342 | 0.409 / 0.737 / **0.635** | 140 | 0.785 / 0.962 / 0.864 |
| `rear-lamp-kb-sol-rewrite.json` | the 214 paragraphs of `rear-lamp-kb-jev.json` rewritten by GPT-6.1 Sol with a prompt that names the device in every row | 420 | 0.340 / 0.753 / **0.606** | 143 | 0.794 / 0.943 / 0.862 |
| `rear-lamp-kb-v5-rewrite.json` | the same 214 paragraphs rewritten by Opus with that prompt | 363 | 0.408 / 0.779 / **0.659** | 148 | 0.781 / 0.943 / 0.855 |

- The minimal-edit rewrite lost 14 matches. Its rows drop the subject and the condition ("Test
  pulse 1 shall be applied ...", "In each direction a tolerance of ±3° shall be allowed."),
  which the platform judge does not match. The local judge scored the same file 0.717, its
  largest error so far.
- Sol's rewrite of the same paragraphs lost 11 matches against Opus's. It wrote 31 more rows,
  over-split a few paragraphs (UN R150 5.1.4.4.1 into 6 extra rows) and left 7 paragraphs
  without a requirement. The model and the prompt both changed, so this does not isolate the
  prompt.
- The same prompt on Opus lost 6 matches against the `kb-jev` rewrite, with 26 fewer rows,
  while the local judge counted 5 more. Both minimal-edit prompts (v4 and this one) scored
  higher locally and lower on the platform: the local judge rewards the regulation's own
  wording, the platform judge does not.
- With the LLM regulation review on, the obligation base changes no selected regulation on dev,
  synth-a06, the plain bumper or the bumper with sensors and fog lamp, against `main`'s
  selection with the same light-source rule. Without the LLM it keeps R150 on synth-a06 and R42
  on the plain bumper, which the lexical ranking alone drops.

### Branch `brain-model-mix-examples`: expert examples and the obligation cut

Run at 22:00, uploaded at 22:14 CEST. Code is on branch `brain-model-mix-examples` at
`e5e0d25` (not merged); the file is `rear-lamp-mix-examples-cut.json` with its log.

Configuration: `main`'s default models at `b7d6ee2` (Opus 5.5 for profile, regulation review
and relevance; Sonnet 5.5 for the rewrite), plus two rewrite changes behind flags:
- `BRAIN_REWRITE_EXAMPLES=1`: each paragraph comes with the three most similar paragraphs the
  dev experts cite (TF-IDF over the text) and the exact expert rows written from them, leaving
  out the paragraph's own regulation so it never sees its own answer.
- `BRAIN_REWRITE_CUT=obligation`: replaces the split-everything rule of `0ccae35` with one row
  per obligation, splitting only table rows, list items with their own values and optional
  cases.

| | Requirements | Requirement P / R / F1 / F2 | Matched of 190 | Page P / R / F1 | Regulation P / R |
|---|---|---|---|---|---|
| Platform | 341 | 0.405 / 0.726 / 0.520 / **0.627** | 138 | 0.831 / 0.925 / 0.875 | 1.00 / 1.00 |
| Local judge | 341 | 0.425 / 0.763 / 0.546 / 0.658 | 145 | 0.831 / 0.925 / 0.875 | 1.00 / 1.00 |

- 11 matches and 0.055 below Fable, and below the plain Opus run.
- The platform found 7 fewer matches than the local judge, where the Claude runs above scored 4
  to 9 more. The cut merges rows the experts keep apart; word overlap still counts a merged row,
  but the platform judge wants the same scope, condition and constraint. Like the minimal-edit
  rewrite on `kb-stack`, a style change that the local judge rewards lost on the platform.
- Relevance answers came from the cache of the Opus run, so the run paid only for the Sonnet
  rewrite ($1.13). From an empty cache it costs about $5.50.
- One upload; identical files have scored up to 7 matches apart.

### 24 Oct, 21:30 to 22:50: narrowed table rule, deterministic routing, Gemini relevance

- **qwen3.5:9b rewrite with the narrowed table rule** (`rear-lamp-qwen-split2-rewrite.json`).
  The same 208 paragraphs as `rear-lamp-qwen-split-rewrite.json`, with `d7683cd`: a paragraph
  that points at a table stays one requirement, and an empty model answer keeps the
  deterministic rows. Rows fall from 446 to 411 and inside gold paragraphs from 276 to 207;
  local matches rise from 137 to 143 (Fable's own rewrite: 141). Not uploaded yet. The local
  judge overcounted the previous qwen file by 4, so expect a platform score a little below the
  local one. The run lost 5 batches when the Ollama server stopped at 22:04; the rerun took the
  other 47 from the cache and recomputed those 5 (see the log).
- **Deterministic path with sibling routing** (`rear-lamp-deterministic-sibling.json`). The
  feature changes of `b7d6ee2`: sections next to one that names the product count as other
  devices, and a regulation whose title names the product (R42) counts as about it. On dev 647
  rows instead of 778, page F2 0.758 instead of 0.723, local requirement F2 0.394 instead of
  0.364. This is the Sunday fallback when no model is available. Uploaded 22:57: requirement
  P 0.164 / R 0.558 / F2 0.377 (106 matches), page P 0.480 / R 0.887 / F2 0.758, regulations
  1.00 / 1.00. Against the old deterministic file (0.348, 107 matches from 778 rows) it keeps
  the same matches with 131 fewer rows. The local judge counted 5 too many, as it does on
  verbatim text, so the upload confirmed the expected floor and added no new information.
  Without a model the path stays at about 0.35 to 0.38; the model-backed runs score 0.62 to
  0.68.
- **Gemini relevance** (`rear-lamp-gemini-relevance.log`, write-up in `brain/docs/gemini.md`).
  Paragraph level only, no submission. Gemini 3.5 Flash reaches AUC 0.974 on 1,100 dev
  paragraphs (gpt-5.5 0.968 on the same ones), but the free tier allows about 20 requests per
  model per day, and UN R48 was not reached.

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
| `rear-lamp-qwen-split-rewrite.json` | 133 | 137 | 0.551 | 0.568 |
| `rear-lamp-mix-examples-cut.json` | 138 | 145 | 0.627 | 0.658 |

The local judge ranks the three Claude runs in the platform's order. On their rewrites it finds
4 to 9 fewer matches than the platform. It finds more than the platform on the deterministic
file's verbatim sentences (5 more) and on qwen's short split rows (4 more). Its error depends on
the writing style, so it cannot compare two rewrite styles; upload to the dev case for that, or
use a model judge calibrated against these rows (`brain/docs/todo/01-model-judge.md`). Regulation and page levels match the platform, since both use
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

- **Rewrite-only qwen run:** the rewrite prompt and `llm.py` of `0ccae35` (split rules,
  temperature 0 for local models), qwen3.5:9b through Ollama 0.40.10 at a 16k context, on the
  paragraphs of `rear-lamp-fable.json`. The harness became `brain/eval/rewrite_pass.py` in
  `dcf1740`.

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
