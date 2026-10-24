# 07 Big swings: find what actually moves recall and precision

## How to use this file

Two roles read this file:

- **The master**: a fresh chat (Claude Code, Cursor or any agent) told "read
  `brain/docs/todo/07-big-swings.md` and act as the master". It follows **Master protocol**,
  starts one lane agent per lane, keeps `out/experiments/STATUS.md` current, and talks to the
  owner (approvals, uploads).
- **A lane agent**: told "read `brain/docs/todo/07-big-swings.md` and run lane X". It follows
  **Lane protocol**, the **Shared brief** and its own lane section.

Everything is written so that work can stop at any point (usage runs out, a chat closes) and a
new master or lane agent can continue from the files alone: `STATUS.md` says where the task
stands, each lane's `out/experiments/<lane>.md` says which of its steps are done and what they
produced. No state lives only in a chat.

Everything happens in **one checkout** (`/Users/troy/Documents/Projects/Industrial-Agents-Certivity`)
on **branch `big-swings`**. No worktrees, no other branches. Lanes write disjoint files, so they
run in parallel without conflicts. Nothing from this task goes to `main` until the owner
decides.

Written Saturday 24 Oct, 22:45 CEST. The team freezes the engine at 02:00 (task 06 then owns
it). The held-out bumper case lands at 08:00. Anything a lane finds after about 01:30 is a
recommendation for Sunday, not a code change.

## Master protocol

### Start or resume (the same steps either way)

1. `cd /Users/troy/Documents/Projects/Industrial-Agents-Certivity && git status -sb && git log --oneline -15`.
   You must be on `big-swings`. If not, and the working tree is clean, `git switch big-swings`;
   otherwise stop and ask the owner.
2. Read `out/experiments/STATUS.md`. If it does not exist, this is a fresh start: create it from
   the template under **Templates**, then do **One-time setup** below.
3. Read every lane file `out/experiments/<lane>.md` that exists. A lane's real state is its
   checklist there, not what `STATUS.md` says; when they disagree, correct `STATUS.md`.
4. Check the budget line in `STATUS.md`. If the owner has not approved lanes yet, ask once
   ("Lanes A, C, D cost $0. B up to $12, E $3, F $5, G $8, D's rebuild $2. Which may spend?")
   and write the answer there, so a later master does not ask again.
5. For each lane, decide from its file:
   - **not started**: start a lane agent (below).
   - **running**: its file was updated in the last 15 minutes. Leave it. If it has not been
     updated for longer, treat its agent as dead (a resumed master always assumes the previous
     chat's agents are gone) and start a new lane agent with the resume message.
   - **waiting for upload**: make sure the owner has the file name and prediction (below).
   - **done**: check its report (Lane protocol step 6) before marking it done in `STATUS.md`.
6. Write `STATUS.md` after every change of state, with the time. Commit it (step 7).
7. Commit only paths you own (`out/experiments/STATUS.md`, `out/README.md`, this file's
   Results section): `git add <paths> && git commit -m "swing master: <what>"`. If git reports
   `index.lock`, wait a few seconds and retry; another agent is committing.

### One-time setup (fresh start only)

From the repo root:

```bash
mkdir -p out/experiments brain/swing
for f in mix mix-examples mix-noimage mix-examples-cut-consolidated; do
  git show brain-model-mix-examples:out/rear-lamp-$f.json > out/rear-lamp-$f.json
done
cd brain && uv sync --extra llm && ls data/corpus | head -3   # corpus exists; else: uv run python -m brain.ingest
```

Commit the four files with `STATUS.md` ("swing master: setup"). They complete the pool of 15
model-written dev files that lanes A, B, C, D and F use. (Setup was done at 22:36 on 24 Oct,
commit "swing master: setup"; a resumed master skips this.)

### Starting a lane agent

If your tool can start sub-agents (Claude Code's Agent tool, Cursor agents, separate chats),
start one per lane, all in this checkout (no worktree isolation), in this order of value:
A, C, D, E, F, B, G. Give each exactly this message, with the letter filled in:

> Read `brain/docs/todo/07-big-swings.md` in `/Users/troy/Documents/Projects/Industrial-Agents-Certivity`
> and run lane X, following "Lane protocol". Resume from `out/experiments/X.md` if it exists.
> Approved spend for this lane: $N (from `out/experiments/STATUS.md`).

If your tool cannot start sub-agents, run the lanes yourself one after another in the same
order, following Lane protocol for each, so a later master can still resume any of them.

### Uploads

Only the owner uploads, by hand, at most 5 per hour. When a lane marks a file "waiting for
upload", tell the owner: the path, the predicted matched count and F2, and which question the
upload answers. Keep a queue in `STATUS.md`, best expected value first, at most 5 per hour.
When the owner pastes the platform's numbers back, write them into the lane's file (its upload
table) and into `STATUS.md`, with the upload time.

### Finishing

When every lane is done, or at 01:30 at the latest: write a summary in **Results** at the end of
this file (what drives recall, what drives precision, which variant to use on Sunday and what
it costs), and fold every lane's run-log rows into the run log of `out/README.md`. Commit.
Tell the owner the recommendation and which lanes' files are worth keeping.

## Lane protocol

1. **Find your state.** Open `out/experiments/<lane>.md`. If it does not exist, create it from
   the lane template under **Templates**, with one checklist line per step of your lane
   section (A1, A2, ...). Set the lane's row in `STATUS.md` to "running" with the time.
2. **Verify before trusting.** For every checked step, check that the files it lists exist
   (`ls`) and that its commit is in `git log`. Uncheck any step whose output is missing.
3. **Continue at the first unchecked step.** Rerunning a step that made LLM calls is cheap:
   finished calls come back from the cache in `brain/data/cache/`. Do not start a paid step
   without the lane's approved spend in `STATUS.md`.
4. **After every step:** check it off with the time, the files it wrote, the numbers it found and
   the spend so far, and write the next step in "Next". Then commit your own paths only:
   `git add out/experiments/<X>.md out/experiments/<X>-* out/rear-lamp-swing-<X>-* brain/swing/<x>_* && git commit -m "swing <X>: step <n>, <what>"`
   (for lane A: `out/experiments/A.md out/experiments/A-* out/rear-lamp-swing-A-* brain/swing/a_*`).
   Add only paths that exist; `git add` fails on a pattern that matches nothing.
   Never `git add -A`, never switch branches, stash, reset or rebase: other agents share the
   checkout. On `index.lock`, wait and retry.
5. **Uploads.** When you nominate a file, write its predicted matched count and F2 in your upload
   table, set your status to "waiting for upload" in your file and in `STATUS.md`, and carry on
   with any step that does not depend on the result. The master brings the platform's numbers
   back into your file.
6. **Done.** Fill in the report at the end of your file (Rules, item 5), set your status to
   "done" in your file and `STATUS.md`, and commit.

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

### The shared checkout

All agents work in `/Users/troy/Documents/Projects/Industrial-Agents-Certivity` on branch
`big-swings`. Run Python from `brain/` (`uv run ...`). The corpus (`brain/data/corpus/`) and the
LLM cache (`brain/data/cache/`) are already there: every cached answer (Opus relevance for the
lamp over all 2,900 paragraphs, every rewrite so far) is free to reuse, and cache writes are
atomic, so parallel runs are safe. `brain/.env` sets `BRAIN_LLM=anthropic`; prefix any command
that must stay free with `BRAIN_LLM=`.

The pool of dev files is in `out/`: the 10 model-written files in the table above, four from
branch `brain-model-mix-examples` (`rear-lamp-mix.json`, `rear-lamp-mix-examples.json`,
`rear-lamp-mix-noimage.json`, `rear-lamp-mix-examples-cut-consolidated.json`), and
`rear-lamp-main-a39acab.json` (`main`'s current defaults: Opus relevance, Sonnet rewrite with
the prompt of `d7683cd`; 388 rows, 146 matched locally, not uploaded). Never switch to that branch; read anything else from it with
`git show brain-model-mix-examples:<path>`.

### Money and models

- No paid API call without the owner's yes on a written estimate (tokens, price, repeats).
  Each lane below has a cap; above it, ask. Prices per million tokens: Sonnet 5.5 $2 in / $10
  out, Opus 5.5 $4 / $20, Fable 5.1 $10 / $50, Haiku 5.5 cheaper still (check), Jev $0.042
  input only.
- Reference costs on the lamp: Opus relevance over all 2,900 candidate paragraphs $4.65; a
  Sonnet rewrite of 267 paragraphs $0.85 (about $0.003 per paragraph); a full Opus + Sonnet run
  from an empty cache about $5.50.
- What is cached for the lamp: Opus relevance for every candidate paragraph, and Sonnet rewrites
  of the 267 selected paragraphs with `main`'s current rewrite prompt (`d7683cd`). Any change to
  a prompt, the paragraph set or the model makes new calls: check with a dry run or the cost
  wrapper's cache-hit count before calling a step free.
- `brain/brain/claude_cli.py` runs prompts through `claude -p` on the subscription, cached in
  `data/cache/claude_cli/`, with the API key removed. Use it for offline work (judging,
  tagging, rewrite passes) to keep the API bill at zero.
- The pipeline on `main` has no cost log. `brain/swing/run_costed.py` (see the end of this
  file) wraps it and prints calls, cache hits and dollars per model. Put the spend of every
  paid step in your lane file.

### Rules

1. **No dev gold text in any prompt or few-shot example**, not even from other regulations.
   `BRAIN_REWRITE_EXAMPLES` on branch `brain-model-mix-examples` breaks this rule (it shows dev
   gold rows from the other three regulations); do not build on it.
2. **Stay in your files.** Lane X writes only: `out/experiments/X.md` (its progress file),
   `out/experiments/X-*` (its data, such as `A-pool.json`), `out/rear-lamp-swing-X-*`
   (submissions and logs, for example `out/rear-lamp-swing-A-votes5.json`) and
   `brain/swing/x_*` (Python, lowercase letter, for example `brain/swing/a_votes.py`). Do not edit `brain/brain/*.py`, `brain/eval/*.py` or any shared file:
   import from them, or copy what you need into your own module and patch at runtime.
3. **Record every run** (the `AGENTS.md` rule): save `out/rear-lamp-swing-X-<variant>.json`
   with its `.log`, and keep run-log rows in your lane file in the same columns as the table in
   `out/README.md` (time CEST, file, method, commit, rows, local matched and F2, platform
   matched and F2 with upload time, spend). Do not edit `out/README.md`: the master folds your
   rows in at the end.
4. **Commit on `big-swings` only, your own paths only** (Lane protocol step 4). Before a commit
   that adds code, run from `brain/`: `uv run ruff check swing && uv run ruff format --check swing`.
   Do not push, and never touch `main`. Follow `DESIGN.md`, including its list of AI-isms.
5. **Report in this shape** at the end of `out/experiments/<lane>.md`: the answer to your
   lane's question in two sentences, the curve or table behind it, the nominated upload(s) with
   predicted and (once uploaded) platform numbers, the transfer check, and whether it can run
   on the bumper on Sunday within the 5-hour window and at what cost.

## Lanes

### A. Vote ensemble: pool every run, keep what many runs agree on

**Question.** How far does agreement across independent runs go as a selector, and which
wording should represent a cluster?

**Cap:** $0 (all offline on existing files).

1. Pool every model-written dev file in `out/` (the 10 in the table plus the 4 branch files).
   Cluster rows per (regulation, paragraph) by similarity; try lexical similarity 0.5, 0.6, 0.7
   and a number-aware variant (two rows with different numbers never cluster). Write the pool
   as soon as it exists to `out/experiments/A-pool.json` (one record per cluster: regulation,
   paragraph, page, member rows with their source file, vote count): lanes B, C and F read it.
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
   side without examples. Do not switch branches: copy the `_SPLIT_OBLIGATION` text and the
   `_system()` replacement from `git show brain-model-mix-examples:brain/brain/rewrite.py` into
   `brain/swing/d_cut.py`, patch `brain.rewrite._SYSTEM` at runtime, and rewrite the 267
   paragraphs of `rear-lamp-mix.json` (about $1 with Sonnet, relevance cached).
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

## Templates

### `out/experiments/STATUS.md` (the master's ledger)

```markdown
# Big swings: status

Updated: <date time CEST> by <master chat or tool>
Task: brain/docs/todo/07-big-swings.md. Branch: big-swings. Setup done: <yes/no, commit>.

## Budget

Approved by the owner at <time>: A $0, B $<n>, C $0, D $<n>, E $<n>, F $<n>, G $<n>.
(Write "not asked yet" until the owner answers.)

## Lanes

| Lane | State | Last update | Current step | Spend so far | Lane file |
|---|---|---|---|---|---|
| A votes | not started / running / waiting for upload / done / blocked: <why> | <time> | A3 | $0 | out/experiments/A.md |
| ... one row per lane, A to G ... |

## Upload queue (owner uploads by hand, at most 5 per hour)

| Order | File | Lane | Question it answers | Predicted matched / F2 | Uploaded at | Platform matched / F2 |
|---|---|---|---|---|---|---|

## Log

- <time> <what happened: lane started, step done, upload result, agent restarted after a stop>
```

### `out/experiments/<lane>.md` (one per lane)

```markdown
# Lane <X>: <title>

State: <running / waiting for upload / done / blocked: why>. Updated: <time CEST>.
Approved spend: $<n>. Spent: $<n>.

## Checklist

- [x] X1 <step as in the lane section>. Done <time>. Files: <paths>. Commit: <hash>.
      Found: <numbers in one or two lines>.
- [ ] X2 <step>
- ...

Next: <the exact next action, with the command if there is one>.

## Run log rows

| Run | File | Method | Code | Rows | Local matched / F2 | Platform (upload): matched / F2 | Spend |
|---|---|---|---|---|---|---|---|

## Uploads

| File | Question | Predicted matched / F2 | Uploaded at | Platform matched / F2 |
|---|---|---|---|---|

## Notes

<anything a successor needs: decisions, dead ends, half-finished runs and how to resume them>

## Report

<filled in at the end: Rules, item 5>
```

## Cost wrapper

Already on the branch as `brain/swing/run_costed.py`. Run it from `brain/` instead of
`python -m brain.pipeline`, with the same arguments:
`PYTHONPATH=. uv run python swing/run_costed.py ../cases/dev-rear-lamp --team-id team-06 -o ...`.
It prints calls, cache hits and dollars per model. Its source, for reference:

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

Written 24 Oct 23:14 CEST, from the lane reports. Every score below is local. The hour was already at 4 of 5 platform uploads, so nothing from this task was uploaded. Requirement matched and F2 on the lamp come from `eval.score` (190 expert rows). Regulation and page figures come from `tools/score_local.py`. Lane G's F2 is paragraph precision and recall against 67 silver bumper paragraphs, not the lamp judge. Spend is $14.92 of the $70 ceiling: A $0, B $3.71, C $0, D $0.82, E $1.79, F $1.25, G $7.35.

**What drives recall.** Selection, not a bigger rewrite model and not a longer tail. Writing every paragraph down to blend 0.03 reaches 158 local matches in 1,382 rows (F2 0.369). The chance of a match is about 0.42 per row at blend 0.3 to 0.4, about 0.2 at 0.2 to 0.3, and 0.02 or less below 0.15, so the F2-optimal cut of that one rewrite stops at blend 0.20 (358 rows, 142 matched, F2 0.635). Rows that only other runs found match at about 0.04 each. Agreement across runs is the recall tool that does pay: keeping clusters that 7 or more of 14 runs wrote, worded from a writer that keeps the subject and condition, matches 156 of 190 in 351 rows (F2 0.702). Three diverse runs capture about half of the gain from 1 run (about 0.63) to 14 runs (0.702). Diversity has to come from different paragraph selection. Rewrite-prompt variants on the same cached relevance sit close together and add little. On the bumper the same lesson shows up as the blend weight: the lamp-fitted decision model at weight 0.7 holds recall down, and Sonnet at weight 0.85 reaches paragraph recall 0.85 on the plain bumper and 0.79 on the fog bumper.

**What drives precision.** Agreement on the row, not a finer or coarser cut and not a closer paraphrase. The 149 rows that 12 or 13 of 13 runs wrote match 99 locally (precision 0.66, F2 0.545) and cite pages at precision 0.917. Of their 50 misses, 46 sit on paragraphs the experts never cite: test-procedure steps, installation one-liners, variants the spec does not have, and pointer rows. Wording accounts for about 4. A fine cut and a coarse cut of the same paragraphs match the same gold rows. The best local hedge (360 rows, 155 matched, F2 0.692) is shorter copies of sentences the coarse cut already wrote. A verbatim row, the regulation's sentence plus a subject and condition, scores 137 / 0.640 against Fable's 141 / 0.646 on the same paragraphs. The local judge is the wrong one for that comparison, and it was not uploaded. A logistic selector on log(votes) and an Opus keep score ties the plain vote (154 matched, F2 0.690, AUC 0.892) and does not beat it. Word share lifts the local score by picking near-verbatim rows the lexical judge over-counts.

**Sunday.** Use one Sonnet 5.5 run for relevance and rewrite, blend weight 0.85, with the regulations from the 08:30 review passed as `--only` to `brain/swing/g_runs.py`. On the plain bumper that file scores paragraph precision 0.79, recall 0.85, F2 0.838, about 60 seconds and about $1.15 from a cold cache. On the fog bumper the same command took 134 seconds and $4.33, with precision 0.74, recall 0.79, F2 0.779. A vote of Haiku runs moves F2 by less than 0.03 on both bumpers. The pipeline's own blend weight of 0.7 scored 0.789 on the plain bumper, behind 0.85. The 14-run lamp vote cannot be built on an unseen bumper in the morning. If a second run fits, spend it on a different relevance model, not on another rewrite of the same paragraphs.

**When a platform slot is free.** The file most likely to beat the current best (Fable, 149 matched, F2 0.682) is `out/rear-lamp-swing-A-votes7.json`: 351 rows, local 156 matched, F2 0.702, predicted about 157 / 0.707. It cannot be the Sunday method. It answers whether agreement survives the platform judge.

**Files worth keeping.** The seven reports in `out/experiments/`. `brain/swing/g_runs.py` is the Sunday command. `brain/swing/a_votes.py` and `a_sweep.py` are the vote, for a day when several runs already exist. Lane C's miss list (test procedure, installation one-liners, absent variants, pointer rows) is the selector's feature list. Lane B's blend curve is the argument against writing the tail. The hedge files, the verbatim files, and the Haiku bumper votes are the negative results.
