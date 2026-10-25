# Speed and cost experiments on the 0.783 chain

What we tried to make the flagship run cheaper and faster without losing score, what worked and
what did not. Branch `kb-speed`, cut from `checkpoint/0783-consolidate` (kb-stack `1d8b22e` plus
the claude -p harness and the repro chain). Dates are 25 Oct 2026, CEST.

## Caveat: CLI numbers, not API numbers

Every experiment runs through `claude -p` (Claude subscription) or `codex exec` (ChatGPT
subscription), never the API.

- `claude -p` runs with our own system prompt (`--system-prompt`) and with Claude Code's tools,
  settings and MCP servers off, but each call still carries about 800 tokens of harness overhead
  and 2 to 3 s of process start-up. Structured output goes through `--json-schema`.
- `codex exec` carries Codex's own agent prompt, about 18k tokens per call, and receives our system
  prompt as user text. Its outputs can differ from what the same model gives through an API.
- Dollar figures are what `claude -p` reports (`total_cost_usd`, list prices), charged against the
  subscription. Codex reports no cost.
- Model-to-model comparisons inside `claude -p` share the same harness, so they are fair. Codex
  comparisons also measure the agent prompt.
- Each variant is one run. Opus itself varies from run to run (see the noise rows): when one
  stage is re-run fresh, a difference under about 0.015 F2 is noise. A fully fresh chain varies
  more; the cold run below lands 0.038 under the cached one.

## How to run

`repro/speed/chain.py` runs the whole chain on a case: the pipeline (Jev, relative cut 0.20, p_keep
recorded), p_section, the section cut and rules, verbatim text, the merge, the collapse. Any stage
can take another model (`keep=claude-haiku-5-5`, `sections=codex:gpt-6-luna`); the rest come from
the cache. It writes per-stage calls, cache hits, live and cold cost and time to `stats.json`.

```bash
cd brain
CLI_CACHE=~/Personal/Industrial-Agents-Certivity/brain/data/cache BRAIN_CLAUDE_CLI_WORKERS=10 \
  uv run --frozen python ../repro/speed/chain.py OUT ../../Industrial-Agents-Certivity/cases/dev-rear-lamp sections=claude-haiku-5-5
uv run --frozen python -m eval.score OUT/final.json
```

`brain/data/cache` links to `~/Personal/.certivity-llm-cache`, the cache the 0.783 run used;
the section and merge answers sit in the main checkout's cache (`CLI_CACHE`). With Opus on
sections, the saved `repro/p_section.json` scores stand in for the calls, as in the 0.783 chain.
Outputs are in `~/Personal/bench-out/kb-speed/<variant>/`.

## Baseline

`CACHE_ONLY=1` replay on dev rebuilds `repro/consolidate/uploaded-0783.json` row for row: 287 rows,
lexical judge 146 / 190 matched, requirement F2 0.697 (platform 0.783, re-upload 0.793).

What the 0.783 run's pipeline cost when its calls were made (from the cached `.usage.json`):

| Stage | Calls | Effort | Cost | Share |
|---|---|---|---|---|
| relevance | 113 | low | $8.74 | 64% |
| rewrite | 28 | medium | $3.71 | 27% |
| keep (p_keep) | 15 | low | $0.92 | 7% |
| select_regs | 1 | high | $0.15 | 1% |
| profile | 1 | medium | $0.03 | 0% |
| p_section | 30 | default | ~$0.80 (fresh Opus run below) | |
| merge | 1 | default | ~$0.04 | |

Cold total about $14.4 per dev run. Wall time: an earlier ready-for-main run of the same stages at
5 concurrent claude -p processes spent 191 s in rewrite, 37 s in keep and 33 s in sections.

## Results

Local score is `eval.score` (lexical judge) on dev; the platform scores about 0.08 to 0.10 higher.
Live cost is what the variant's new calls cost; time is the stage's span at 10 concurrent processes.

| Variant | Rows | Matched | F2 | Stage cost | Stage time | Verdict |
|---|---|---|---|---|---|---|
| Baseline (cached Opus) | 287 | 146 | 0.697 | | | |
| keep on Opus, fresh run (noise) | 285 | 143 | 0.684 | $0.61 | 21 s | reference |
| keep on Haiku 5.5 | 266 | 130 | 0.634 | $0.02 | 25 s | worse |
| keep on Sonnet 5.5 | 232 | 121 | 0.610 | $0.30 | 13 s | worse |
| p_section on Opus, fresh run (noise) | 279 | 143 | 0.688 | $0.80 | 38 s | reference |
| p_section on Haiku 5.5 | 291 | 145 | 0.690 | $0.03 | 34 s | **as good** |
| p_section on Sonnet 5.5 | 246 | 130 | 0.646 | $0.34 | 21 s | worse |
| rewrite on Haiku 5.5 | 316 | 127 | 0.590 | $0.18 (+$0.80 keep) | 151 s | worse |
| rewrite on Sonnet 5.5 | 301 | 142 | 0.669 | $1.60 (+$0.66 keep) | 87 s | slightly worse |
| keep on Luna (gpt-6-luna, codex) | 242 | 118 | 0.589 | ChatGPT quota | 16 s | worse |
| p_section on Luna | 266 | 129 | 0.629 | ChatGPT quota | 24 s | worse |
| Cold run, all of the below | 294 | 139 | 0.659 | $10.03 total | 4.4 min total | see below |

Relevance is judged before the rewrite, on the paragraphs it selects (`STOP_AFTER_SELECT=1`,
`repro/speed/compare_selected.py`), so a variant costs only its own calls. Dev gold cites 121
paragraphs.

| Relevance on | Paragraphs | Gold paragraphs | Same as Opus | Cost | Time | Verdict |
|---|---|---|---|---|---|---|
| Opus 5.5 (cached, the 0.783 run) | 330 | 118 | 330 | $8.74 when made | | |
| Haiku 5.5 | 326 | 113 | 253 | $0.18 | 83 s | loses 5 gold paragraphs |
| Sonnet 5.5 | 268 | 110 | 239 | $2.98 | 78 s | loses 8 |
| Luna (codex) | 256 | 104 | 223 | ChatGPT quota | 147 s | loses 14 |

Spend for the variants above: about $9.25 reported by claude -p, plus ChatGPT quota for Luna. The cold run below added $10.03.

## Findings

- **Prompt caching off in `claude -p` (done, identical output).** Claude Code writes every prompt to
  a one-hour cache at twice the input price, and one-shot calls never read it back.
  `DISABLE_PROMPT_CACHING=1` in `claude_cli` halves the input cost: the same 15 Opus keep calls cost
  $0.61 fresh against $0.92 when first made. Expected saving on a cold run: about a third of the
  input cost, roughly $3 of $14.
- **Sonnet is stricter, not just weaker.** On keep and p_section, Sonnet gives lower probabilities
  than Opus, so the fixed section cut (p_keep * sqrt(p_section) >= 0.3535, tuned on Opus) removes
  more rows and recall drops. Haiku's calibration happens to sit closer to Opus on p_section.
- **Keep needs Opus.** Both cheaper models lose 13 to 25 matches.
- **Rewrite on Haiku is both worse and slower** (long outputs; 151 s against 87 s for Sonnet).
  Sonnet's rewrite is close (142 against 143 to 146 for Opus) and halves that stage's cost; it is
  the only borderline case worth a second sample.
- **Relevance, 64% of the cost, has no cheaper substitute.** Every cheaper model drops gold
  paragraphs, and a paragraph that relevance drops never reaches the list.
- **Luna through Codex is the weakest everywhere** (keep 0.589, p_section 0.629, relevance 104 of
  121 gold paragraphs). It is quick per call despite Codex's 18k-token agent prompt.
- **Haiku is fine for p_section.** 145 matched against 143 to 146 for Opus, for $0.03 instead of
  $0.80. One dev sample; not checked on a bumper.
- **10 concurrent claude -p processes work.** No call failed at 10 in any run (Opus, Sonnet,
  Haiku), so `BRAIN_CLAUDE_CLI_WORKERS` now defaults to 10 instead of 5. Stage times at 10: keep
  21 s, p_section 38 s (Opus) or 34 s (Haiku), merge 6 to 8 s.
- **`codex exec` hung on an open stdin.** Run from a background job, every call waited on stdin
  for 12 minutes; `codex_cli` now passes `stdin=DEVNULL`.

## What changed on `kb-speed`

| Change | Output | Effect |
|---|---|---|
| `DISABLE_PROMPT_CACHING=1` in `claude_cli` | identical | input billed once instead of twice |
| `BRAIN_CLAUDE_CLI_WORKERS` default 5 → 10 | identical | stages that wait on waves of calls run about twice as fast |
| `codex_cli` stdin closed | identical | codex calls no longer hang in background jobs |

Recommended for the next run but not wired in, since p_section is a script outside `brain/`: run
p_section on Haiku (`sections=claude-haiku-5-5` in `chain.py`).

## Cold run with all of it

One dev run, 04:13 to 04:17 CEST, with an empty Claude cache: caching off, 10 workers, p_section on
Haiku, every other stage on Opus (`repro/speed/results/cold-run.stats.json`). The Jev cache stayed
warm, since the TypeSafe key is not available to these runs. Jev's questions depend on the profile
and the regulation pick, and a fresh profile came out slightly different. So those two answers came
from the 0.783 run's cache, and their cost and time are from a first attempt that ran them live.

| Stage | Calls | Cost then | Cost now | Time now |
|---|---|---|---|---|
| profile + regulation pick | 2 | $0.18 | $0.15 | 43 s |
| relevance | 113 | $8.74 | $6.09 | 110 s |
| rewrite | 27 | $3.71 | $3.13 | 104 s (191 s at 5 workers) |
| keep | 15 | $0.92 | $0.60 | 15 s |
| p_section (Haiku) | 29 | ~$0.80 | $0.03 | 29 s |
| merge | 1 | ~$0.04 | $0.03 | 5 s |
| **Total** | | **~$14.4** | **$10.03** | **~5 min** |

That is 30% cheaper. The pipeline ran in 232 s, and the cut and merge in 34 s more.

The score is lower: 294 rows, 139 of 190 matched, F2 0.659, against 0.697 for the cached run.
Neither caching nor the worker count changes what the model returns. The loss is in Opus's fresh
relevance pick:

- It selected 320 paragraphs, not 330.
- 110 of the 121 gold paragraphs reached the pipeline's output, against 116 cached.
- After the cut, 106 gold paragraphs remained, against 113.

So the 0.783 run is a good draw of the same chain. A fresh rerun of it should be expected to land
a few points lower, whatever the settings.

## Not tried

- Relevance batches of 50 instead of 25: half the calls, so less per-call overhead and possibly
  less thinking. Changes the scores, so it needs an Opus relevance run (about $6) to judge.
- Rewrite on Opus at low effort instead of medium.
- A second sample of the Sonnet rewrite and of the Haiku p_section, and either on a bumper.
- A second fresh Opus relevance run, to size relevance's run-to-run spread on its own.
