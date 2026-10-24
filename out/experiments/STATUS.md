# Big swings: status

Updated: 24 Oct 22:49 CEST (system clock) by master (Claude Code desktop, Opus 5.5), at the
handover to Cursor.
Task: brain/docs/todo/07-big-swings.md. Branch: big-swings. Setup done: yes, commit "swing master: setup".

## Handover to Cursor (22:48)

The owner moved the master role to Cursor at 22:48. The Claude Code master told its six running
lane agents (A, B, D, E, F, G) to commit their current step, write an exact "Next" and stop.
Their last commits may land a few minutes after 22:48. Lane C's agent had already finished.

Before acting, a new master checks:

1. **Times in the files are not reliable.** Several agents wrote guessed times ahead of the
   clock (lane A wrote "23:15" at 22:46). Judge whether a lane is alive by `date`, the lane
   file's modification time (`stat -f '%Sm' out/experiments/X.md`) and `git log --format='%ci %s'`,
   not by the "Updated:" line. Every agent must take times from `date`, never guess them.
2. **Lane B may have a paid run still going**: B2 was started as
   `PYTHONPATH=. uv run python swing/b_recall.py run --cut 0.03 --approved -o ../out/rear-lamp-swing-B-full.json`
   (from `brain/`). Check `ps aux | grep b_recall` before starting lane B again. If it is not
   running, rerunning the same command is safe: finished calls come back from the cache.
3. **`claude -p` is not logged in** for agents (see the log). Unless the owner has run
   `claude /login` since, the $0 routes in lanes B, E, F, G do not work, and those lanes use
   the API within their caps.
4. **Uncommitted files**: lanes leave `brain/swing/*_*.py` and `out/rear-lamp-swing-*` files
   untracked until their step commits. Do not delete them: they belong to the lane and its
   successor commits them.

## Budget

Approved by the owner at 22:41: A $0, B $12, C $0, D $2, E $3, F $5, G $8 (the task's caps,
$30 in all). Hard ceiling for the whole task: **$70 total** (the API account has a €100 limit).
A lane that needs more than its cap asks the master; the master may grant it while the total
stays under $70, and must ask the owner above that. Spent at the handover: $0 recorded by every
lane (lane B's B2 run may have spent some; read its log).

## Lanes

| Lane | State | Last update | Current step | Spend so far | Lane file |
|---|---|---|---|---|---|
| A votes | stopped at 22:47 for the handover | 22:47 (commit c3a0495) | A1 to A4 done; next A5: write the two nominations (files exist, predictions in A.md "Next") and the report | $0 | out/experiments/A.md |
| B maximum recall | waiting for upload (B4, B6); bumper transfer check (about $1.5) was running at 22:47 | 22:47 (commit 64c667d) | B1 to B6 done; transfer check and report open | $2.03 (+ about $1.5 running) | out/experiments/B.md |
| C maximum precision | waiting for upload: out/rear-lamp-swing-C-votes12.json, predicted 101 / 0.556 | 22:45 (commit 24d12c1) | C1 to C4 done, report written; agent finished | $0 | out/experiments/C.md |
| D hedged cuts | running, told to stop at 22:48 | 22:46 (commit 7ef691b) | D1, D2 done; next D3 (rebuild the coarse side without examples, `brain/swing/d_cut.py`, about $1) | $0 | out/experiments/D.md |
| E verbatim rows | stopped at 22:46 for the handover | 22:46 (commit 214998a) | E1, E2 done (v1 316 rows, local 133; v2 300 rows, local 130); next a v3 that fixes four problems (about $0.60), see E.md "Next"; no nomination yet | $1.16 | out/experiments/E.md |
| F row selector | running, told to stop at 22:48 | 22:46 (commit a769e68) | F1 done; next F2, the LLM keep feature (`brain/swing/f_keep.py`, Opus, about $0.75) | $0 | out/experiments/F.md |
| G Sunday feasibility | running, told to stop at 22:48 | 22:42 | G1 in progress (`brain/swing/g_runs.py`, untracked), on the API with Haiku 5.5 | $0 | out/experiments/G.md |

## Upload queue (owner uploads by hand, at most 5 per hour)

Ordered by expected value: first the one file that may beat the 0.682 best, then the files
that answer a question.

| Order | File | Lane | Question it answers | Predicted matched / F2 | Uploaded at | Platform matched / F2 |
|---|---|---|---|---|---|---|
| 1 | `out/rear-lamp-swing-A-votes7.json` (351 rows) | A | Does a vote of 14 runs (7 or more agree, highest word-share row) beat every single run on the platform? | 157 / 0.707 (local 156 / 0.702) | | |
| 2 | `out/rear-lamp-swing-B-ceiling.json` | B | The platform's recall ceiling: every paragraph with a gold row plus every row any run wrote | 174 / 0.464 | | |
| 3 | `out/rear-lamp-swing-C-votes12.json` (149 rows) | C | What precision does the platform give the rows 12 or 13 of 13 runs agree on? (Cannot raise the leaderboard.) | 101 / 0.556 (P 0.68) | | |
| 4 | `out/rear-lamp-swing-B-cut020.json` | B | The same rewrite at the F2-optimal size; with the ceiling, the platform's match count in the tail | 147 / 0.657 | | |
| 5 | `out/rear-lamp-swing-A-votes4.json` (463 rows) | A | Does the platform find more matches in the 112 rows of a lower vote cut than the local judge does? | 163 / 0.669 (local 161 / 0.658) | | |

## Log

- 22:49 Lanes A (after A4, $0), E (after E2, $1.16) stopped for the handover. Lane B finished B1
  to B6 ($2.03) and nominated two files; its bumper transfer check was still running. Queue
  reordered: A-votes7 first.
- 22:48 Owner handed the master role to Cursor. Master told lanes A, B, D, E, F, G to commit and
  stop, corrected two guessed log times, and rewrote this file for the handover.

- 22:45 (first logged as 23:08, a guessed time) Lane C done with its steps, nominated `rear-lamp-swing-C-votes12.json`; queued first, owner told.
- 22:45 (first logged as 23:00, a guessed time) Lane G: `claude -p` answers "Not logged in" from lane agents, so the $0 route through
  `brain/brain/claude_cli.py` is closed until the owner runs `claude /login` in a terminal.
  Lanes use the API within their caps instead. Told B, E, F.
- 22:44 Master started lane agents D, E, F, B, G. All seven lanes have an agent.
- 22:42 Master started lanes A and C ($0), asked the budget, owner answered: caps as written,
  $70 total ceiling. Starting D, E, F, B, G.
- 22:36 Setup: copied the four `brain-model-mix-examples` files into `out/`, added
  `brain/swing/run_costed.py`.
- 22:35 A smoke test of the cost wrapper ran `main`'s defaults and made 23 Sonnet rewrite calls
  ($0.84): `main`'s rewrite prompt changed in `d7683cd`, so the rewrite was not cached. Saved
  as `out/rear-lamp-main-a39acab.json` (388 rows, 146 matched locally, F2 0.636) and added to
  the pool. Not uploaded.
