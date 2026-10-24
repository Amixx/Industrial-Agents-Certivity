# 07 Big swings: find what actually moves recall and precision

## How to use this file

Seven independent lanes, A to G. Each lane is one agent in its own git worktree on its own
branch, cut from branch `big-swings` (this file's branch), never from `main`. Give an agent the
**Shared brief** plus **one lane** section. The lanes read the same files but write different
ones, so they run in parallel without conflicts. Lane branches merge back into `big-swings`
only; nothing from this task goes to `main` until the owner decides.

Written Saturday 24 Oct, 22:45 CEST. The team freezes the engine at 02:00 (task 06 then owns
it). The held-out bumper case lands at 08:00. Anything a lane finds after about 01:30 is a
recommendation for Sunday, not a code change.

## Shared brief

You are joining a hackathon team mid-event (Certivity challenge, Munich). Read
`brain/docs/todo/README.md` (event, rules, tools) and `out/README.md` (every run so far, with
platform scores) before anything else. Paths below are from the repo root.

### Why this task exists

Five hours of tuning moved the dev score by a few points. Model swaps (Sonnet, Opus, Fable),
prompt rules (split everything, obligation cut, minimal edits), expert examples, a
consolidation pass and paragraph cut-offs all land between 0.62 and 0.68 on the platform. The
leader is at 0.762. We are making local optimizations around one design: pick paragraphs, write
every obligation in them. This task swings far in opposite directions to learn what drives
recall and what drives precision on the platform's judge, then keeps what carries over to a
bumper.

### The score, in one line

On dev, with 190 expert rows: **F2 = 5 x matched / (760 + rows submitted).**

- One more match is worth about +0.0045 F2 at our size. One more wasted row costs about
  -0.0006. **One match is worth about 7 wasted rows.**
- So a row is worth adding when its chance of matching is above F2 / 5, about **0.14** at
  today's level. Rows with a 20% chance of matching should be in the file.
- Targets: 0.70 needs about 160 matched at 380 rows. The leader's 0.762 is about 170 matched
  at 356 rows. 0.80 is about 180 at 365.

| Matched \ rows | 300 | 350 | 400 | 500 | 700 |
|---|---|---|---|---|---|
| 150 | 0.708 | 0.676 | 0.647 | 0.595 | 0.514 |
| 160 | 0.755 | 0.721 | 0.690 | 0.635 | 0.548 |
| 170 | 0.802 | 0.766 | 0.733 | 0.675 | 0.582 |
| 180 | 0.849 | 0.811 | 0.776 | 0.714 | 0.616 |

### What we know (24 Oct, all on the rear lamp dev case)

Platform scores, best first (full table and provenance in the run log of `out/README.md`):

| File in `out/` | Rows | Platform matched | Platform F2 |
|---|---|---|---|
| `rear-lamp-fable.json` | 332 | 149 (142 on a second upload of the same rows) | 0.682 |
| `rear-lamp-kb-jev.json` | 389 | 154 | 0.670 |
| `rear-lamp-opus.json` | 338 | 143 | 0.651 |
| `rear-lamp-kb-jev-filter-v4.json` | 342 | 140 | 0.635 |
| `rear-lamp-main-cli.json` | 368 | 143 | 0.634 |
| `rear-lamp-sonnet.json` | 344 | 140 | 0.634 |
| `rear-lamp-mix-examples-cut.json` | 341 | 138 | 0.627 |
| `brain/out/dev-upload.json` | 407 | 145 | 0.621 |
| `rear-lamp-kb-sol-rewrite.json` | 420 | 143 | 0.606 |
| `rear-lamp-qwen-split-rewrite.json` | 446 | 133 | 0.551 |
| `rear-lamp-deterministic.json` | 778 | 107 | 0.348 |

Findings that should shape every lane:

1. **Recall headroom exists; selection is the bottleneck.** Across 14 model-written files (the
   10 in the table plus 4 from branch `brain-model-mix-examples`), 184 of the 190 expert rows are
   matched by at least one run (local judge). No single run passes 158 locally or 154 on the
   platform.
2. **Agreement between runs predicts a match.** Rows of the Fable file that 10 or more of 13
   other runs also wrote (same paragraph, lexical similarity 0.6 or more) match 58% of the
   time; rows echoed by 0 to 2 runs match 11%. Voting over 13 of those runs (all but the
   consolidated file; 991 distinct rows), with no new model call, gives locally:

   | Keep rows written by at least N runs | Rows | Matched | Local F2 | Estimated platform F2 |
   |---|---|---|---|---|
   | 3 | 518 | 165 | 0.646 | 0.665 |
   | 4 | 424 | 158 | 0.667 | 0.688 |
   | 5 | 370 | 154 | 0.681 | 0.704 |
   | 6 | 328 | 145 | 0.666 | 0.689 |

   The estimate adds the +5 matches the platform usually gives Claude-style text. Not yet
   uploaded.
3. **The experts keep the regulation's words.** For the median expert row, 97% of its words
   appear in its source paragraph; 161 of 190 rows reuse at least 90%. They keep the subject
   and the condition ("When tested in accordance with ...", "The rear position lamp shall ...").
4. **The platform judge is not the lexical judge.** Two style changes the local judge rewarded
   lost on the platform: the minimal-edit rewrite that dropped subject and condition
   (`kb-jev-filter-v4`: local 158, platform 140) and the obligation cut that merges rows
   (`mix-examples-cut`: local 145, platform 138). The lexical judge counts 4 to 9 fewer matches
   than the platform on Claude-style rows and more on verbatim or terse rows. Never decide
   between two writing styles on the local judge alone.
5. **Where the waste is** (`mix-examples` file, 394 rows, 151 matched locally): 177 rows from
   paragraphs the experts never cite, mostly one row each across 114 paragraphs; 60 rows that
   over-split cited paragraphs; 6 rows that differ only in wording. A higher paragraph cut-off
   loses matches faster than rows (0.25 instead of 0.20: 131 matched at 284 rows, worse).
6. **Things that did not help:** a bigger model (Sonnet 140, Opus 143, Fable 149 matched, at
   $3, $6.36, $16.52), a consolidation pass that drops umbrella rows (the experts keep them:
   lost 5 matches for 13 rows), dropping the exploded view (relevance kept 47 more paragraphs,
   F2 fell).
7. **The platform is noisy.** The same Fable rows scored 142 and 149. Gaps under about 5
   matches are noise unless repeated.

### Measuring

- **Local, free:** `uv run python -m eval.score <file>` (lexical judge, from `brain/`),
  `uv run python -m eval.errors <files>` (where rows are lost), `eval.model_judge` (through
  `claude -p`, not calibrated yet, see task 01). Use them to rank variants of the **same**
  writing style.
- **Platform, scarce:** only the owner uploads, by hand, 5 per hour, `team-06`, case
  `dev-rear-lamp`. On dev the leaderboard keeps the best upload, so a bad upload costs nothing
  but the slot. Each lane may nominate **at most two** files for upload, each with a predicted
  matched count written down before the upload. Put the nominated files in `out/` and name them
  in your lane write-up; the owner uploads and pastes back the platform's numbers, which you
  record.
- **Transfer check, required before recommending anything for Sunday:** the silver bumper
  labels (`brain/data/bumper-labels/`, paragraph level, R42, R127, R26, GTR 9) and the
  synthetic lamp case `synthetic/cases/synth-a03-rear-retro-reflector` (its own gold). A method
  that wins only on dev is not a result.

### Setting up your worktree

From the main checkout (`/Users/troy/Documents/Projects/Industrial-Agents-Certivity`):

```bash
git worktree add ../certivity-swing-<lane> -b swing-<lane>-<short-name> big-swings
cd ../certivity-swing-<lane>/brain
uv sync --extra llm
ln -s /Users/troy/Documents/Projects/Industrial-Agents-Certivity/brain/data/cache data/cache
ln -s /Users/troy/Documents/Projects/Industrial-Agents-Certivity/brain/.env .env
uv run python -m brain.ingest
```

The cache is shared on purpose: every cached LLM answer (Opus relevance for the lamp, every
rewrite so far) is free to reuse, and writes are atomic. `brain/.env` sets `BRAIN_LLM`; pass
`BRAIN_LLM=` (empty) on any command that must stay free.

Files from branch `brain-model-mix-examples` that are not on `main` (useful for the pool):

```bash
for f in mix mix-examples mix-noimage mix-examples-cut-consolidated; do
  git show brain-model-mix-examples:out/rear-lamp-$f.json > ../out/rear-lamp-$f.json
done
```

### Money and models

- No paid API call without the owner's yes on a written estimate (tokens, price, repeats).
  Each lane below has a cap; above it, ask. Prices per million tokens: Sonnet 5.5 $2 in / $10
  out, Opus 5.5 $4 / $20, Fable 5.1 $10 / $50, Haiku 5.5 cheaper still (check), Jev $0.042
  input only.
- Reference costs on the lamp: Opus relevance over all 2,900 candidate paragraphs $4.65; a
  Sonnet rewrite of 267 paragraphs $0.85 (about $0.003 per paragraph); a full Opus + Sonnet run
  from an empty cache about $5.50.
- `brain/brain/claude_cli.py` runs prompts through `claude -p` on the subscription, cached in
  `data/cache/claude_cli/`, with the API key removed. Use it for offline work (judging,
  tagging, rewrite passes) to keep the API bill at zero.
- The pipeline on `main` has no cost log. A wrapper that prints calls, cache hits and dollars
  per model is at the end of this file; copy it into your lane's folder.

### Rules

1. **No dev gold text in any prompt or few-shot example**, not even from other regulations.
   `BRAIN_REWRITE_EXAMPLES` on branch `brain-model-mix-examples` breaks this rule (it shows dev
   gold rows from the other three regulations); do not build on it.
2. **Stay in your files.** New code goes in `brain/swing/<lane>.py` (or `brain/eval/` for
   evaluation scripts). Change `brain/brain/*.py` only behind a flag that is off by default,
   and only where your lane says so.
3. **Record every run** (the `AGENTS.md` rule): save `out/rear-lamp-swing-<lane>-<variant>.json`
   with its `.log`, and keep your write-up in `out/experiments/<lane>.md`, with run-log rows in
   the same columns as the table in `out/README.md` (time CEST, file, method, branch and
   commit, rows, local matched and F2, platform matched and F2 with upload time, spend). Do not
   edit `out/README.md`: lanes would conflict there. The coordinator folds your rows in.
4. **Commit on your branch only.** Checks before each commit, from `brain/`:
   `uv run pytest -q && uv run ruff check . && uv run ruff format --check . && uv run mypy`.
   Do not merge into or push to `main`, and do not push your branch unless the owner asks.
   Follow `DESIGN.md`, including its list of AI-isms.
5. **Report in this shape** at the end of `out/experiments/<lane>.md`: the answer to your
   lane's question in two sentences, the curve or table behind it, the nominated upload(s) with
   predicted and (once uploaded) platform numbers, the transfer check, and whether it can run
   on the bumper on Sunday within the 5-hour window and at what cost.

## Lanes

### A. Vote ensemble: pool every run, keep what many runs agree on

**Question.** How far does agreement across independent runs go as a selector, and which
wording should represent a cluster?

**Cap:** $0 (all offline on existing files).

1. Pool every model-written dev file (the 10 in the table plus the 4 branch files). Cluster
   rows per (regulation, paragraph) by similarity; try lexical similarity 0.5, 0.6, 0.7 and a
   number-aware variant (two rows with different numbers never cluster).
2. Sweep the vote threshold, and weighted votes (weight each run by its platform matched, or
   by run family so that near-identical runs, such as the two Fable uploads, count once).
3. Choose the representative text: the Fable row, the Opus row, the row closest to the source
   sentence (highest word share), the longest, the medoid. Remember finding 3 and 4: the
   platform likes the regulation's own words with subject and condition kept.
4. Sunday question: subsample k of the 13 runs (k = 3, 4, 6, 8) many times and plot F2 against
   k. How many cheap runs (Sonnet, Haiku, different temperatures or prompts) give most of the
   gain? Diversity matters more than count: measure it.
5. Nominate the best threshold and representative as one upload, and one more aggressive
   variant (lower threshold, more rows).

### B. Maximum recall: write everything, then measure the tail

**Question.** What is the platform's recall ceiling when we submit almost everything, and how
fast does the chance of a match fall with the relevance score? This sets the F2-optimal file
size from data instead of a cut-off tuned by hand.

**Cap:** $12 on the API, or $0 through `claude -p`.

1. Use the cached Opus relevance scores (free: they are in the shared cache) to rank all
   candidate paragraphs of the four regulations.
2. Rewrite every paragraph down to a very low score (try 0.03) with `main`'s rewrite prompt,
   using `eval/rewrite_pass.py` or a script that calls `brain.rewrite.with_llm` on the set.
   Expect 700 to 1,200 rows.
3. Add the 6 rows only other runs found (union with lane A's pool if it exists; otherwise build
   the union of existing files yourself).
4. Nominate the full file for one upload. Its platform recall is the ceiling; its precision is
   the floor.
5. Offline, cut the full file into nested subsets by relevance score and compute matched per
   score bucket (local judge, then calibrate the scale with the one platform number). Write
   down P(match) per bucket and the F2-optimal size: keep a bucket while its match rate is
   above F2 / 5.
6. Second nomination: the file at that F2-optimal size.

### C. Maximum precision: only rows we are surest of

**Question.** If we keep only the most certain rows, what precision does the platform give? If
the most certain 150 rows match only 60%, the precision ceiling is wording and granularity, not
paragraph choice, and the effort should move there.

**Cap:** $0.

1. Build three small files (120 to 180 rows) from existing outputs: rows with votes of 10 or
   more (lane A's pool, or build it), rows with relevance confidence 0.6 or more in the Fable
   or kb-jev file, and rows that pass both.
2. For each, compute local matched and, for unmatched rows, sort them into: paragraph not
   cited by the experts; paragraph cited but row count exceeds the expert's; wording only.
3. Nominate one file. Predicted platform precision is the interesting number.
4. Read the misses of the top bucket by hand and write down the five most common reasons the
   expert would not list them. That list is input for lanes E and F.

### D. Hedged granularity: two cuts per likely paragraph

**Question.** One match is worth about 7 wasted rows, and the matching is one to one, so does
writing a fine and a coarse version of the same paragraph beat choosing one?

**Cap:** $2.

1. Natural experiment, free: `rear-lamp-mix.json` (split everything) and
   `rear-lamp-mix-examples-cut.json` (obligation cut) come from the same 267 paragraphs. Their
   union, with exact duplicates removed, is the hedged file. Score it.
2. Hedge selectively: both cuts only where the paragraph's relevance is high (0.5 or more) or
   where the two cuts differ in row count; one cut elsewhere.
3. The cut file used dev gold examples (rule 1). For anything you recommend, rebuild the coarse
   side without examples: `BRAIN_REWRITE_CUT=obligation` alone on branch
   `brain-model-mix-examples` (about $1, relevance cached).
4. Nominate the best hedged file. Prediction first.

### E. Verbatim anchoring: the regulation's sentence, completed, never reworded

**Question.** Does a row that is the regulation's own sentence, with only the missing subject
and condition added, beat a model paraphrase on the platform?

**Cap:** $3, or $0 through `claude -p`.

1. Start from `brain/brain/rewrite.py`'s deterministic splitter and `brain/brain/obligations.py`
   to get candidate sentences of each selected paragraph (hold selection fixed: the paragraphs
   of `rear-lamp-fable.json`, as `eval/rewrite_pass.py` does).
2. Let a model only decide, per sentence: drop (no obligation), keep as is, or prepend the
   condition and subject from the parent clause and heading path. It may not change the
   sentence's own words. Split only where the source has a list or table with its own values.
3. Measure the word share against the source (target: like the gold, median about 0.97) and
   the row count against Fable's 332.
4. Unlike `kb-jev-filter-v4` (which dropped subject and condition and lost 14 matches), every
   row must name its subject and keep its condition. Read 20 rows by hand before nominating.
5. Nominate one file. This is the lane where the local judge is least trustworthy, so the
   upload matters most.

### F. Requirement-level selector over a wide pool

**Question.** Can a judgement on each written row ("would the expert list contain this row for
this product?") beat paragraph relevance plus votes?

**Cap:** $5, or $0 through `claude -p`.

1. Pool: lane A's pool if it has been written to `out/experiments/A-pool.json`, else build
   the union of existing files yourself.
2. Features per row: votes, paragraph relevance score, regulation, word share against the
   source, length, number count, modality, whether it cites another paragraph, the row's
   position in its paragraph, and an LLM or Jev answer to "would an expert list this row"
   (branch `kb-stack` has a requirement filter in `brain/keep.py` to start from).
3. Fit a logistic model leaving one regulation out, never in-sample. Choose the cut that
   maximises expected F2 from the predicted probabilities (keep rows above F2 / 5, iterate),
   not a fixed threshold.
4. Report AUC per regulation, the expected and local F2, and which features carry the weight.
   Features that only make sense for a lamp disqualify the model for Sunday.
5. Nominate one file.

### G. Sunday feasibility of the winners

**Question.** Which of the swings can run on an unseen bumper in the 08:00 to 13:00 window,
and what does that cost?

**Cap:** $8.

1. Wait for nothing: start with lane A's idea, because it needs only several runs. On
   `brain/data/synthetic/bumper-plain` and `bumper-sensors-fog`, time and price k cheap runs
   (Sonnet or `claude -p`, varied prompts) and the vote.
2. Check paragraph recall and precision of the voted file against the silver bumper labels,
   next to a single run's.
3. Write the exact Sunday commands for the best feasible variant, with wall-clock time and
   cost, as a proposal for task 06 (do not edit the runbook yourself).

## Cost wrapper

Save as `brain/swing/run_costed.py` and run with
`PYTHONPATH=. uv run python swing/run_costed.py ../cases/dev-rear-lamp --team-id team-06 -o ...`
from `brain/`. It wraps `brain.pipeline.main` and prints calls, cache hits and dollars per
model.

```python
"""Run brain.pipeline and log calls, cache hits and dollars per model."""
import sys
import threading
from collections import defaultdict

import anthropic.resources.beta.messages as M

from brain import llm

PRICE = {"claude-sonnet-5-5": (2, 10, 0.2), "claude-opus-5-5": (4, 20, 0.2),
         "claude-fable-5-1": (10, 50, 0.25)}
usage = defaultdict(lambda: [0, 0, 0, 0])  # calls, in, out, cache read
hits = defaultdict(int)
lock = threading.Lock()
orig = M.Messages.create


def create(self, **kw):
    r = orig(self, **kw)
    u = r.usage
    with lock:
        a = usage[kw["model"]]
        a[0] += 1
        a[1] += u.input_tokens + (u.cache_creation_input_tokens or 0)
        a[2] += u.output_tokens
        a[3] += u.cache_read_input_tokens or 0
    return r


M.Messages.create = create
orig_cj = llm.complete_json


def cj(system, content, schema, *, tier="bulk", **kw):
    payload = {"provider": llm.provider(), "model": llm.model_for(tier), "system": system,
               "content": content, "schema": schema, "effort": kw.get("effort", "medium")}
    if llm._cache_path(payload).exists():
        with lock:
            hits[llm.model_for(tier)] += 1
    return orig_cj(system, content, schema, tier=tier, **kw)


llm.complete_json = cj
from brain.pipeline import main  # noqa: E402

code = main(sys.argv[1:])
total = 0.0
for m, (c, i, o, cr) in usage.items():
    pi, po, pc = PRICE.get(m, (0, 0, 0))
    cost = (i * pi + o * po + cr * pc) / 1e6
    total += cost
    print(f"[cost] {m}: {c} new calls, {i:,} in / {o:,} out / {cr:,} cache read; ${cost:.2f}",
          file=sys.stderr)
for m, h in hits.items():
    print(f"[cost] {m}: {h} cache hits", file=sys.stderr)
print(f"[cost] total new spend ${total:.2f}", file=sys.stderr)
sys.exit(code)
```

## Results

Each lane writes to `out/experiments/<lane>.md`. The coordinator summarises here.
