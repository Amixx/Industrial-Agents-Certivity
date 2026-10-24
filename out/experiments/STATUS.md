# Big swings: status

Updated: 24 Oct 23:07 CEST (system clock, `date`) by master (Cursor).
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
stays under $70, and must ask the owner above that. Spend at 23:05, from lane files and the uncommitted logs of E and G:
A $0, B $3.71, C $0, D $0.82, E $1.79 ($1.16 plus a finished v3 run at $0.63), F $1.25,
G $2.25 ($1.72 committed, plus an uncommitted Sonnet blend at $0.26 and one fog Haiku run at $0.27).
Total about $9.82 of the $70 ceiling.

## Lanes

| Lane | State | Last update | Current step | Spend so far | Lane file |
|---|---|---|---|---|---|
| A votes | done | 22:58 (commit d930515) | report written. votes7: 351 rows, 156 matched, F2 0.702. votes4: 463 rows, 161 matched, F2 0.658. Both valid. | $0 | out/experiments/A.md |
| B maximum recall | done locally; upload held | 22:58 (commit b58b7d9) | five files scored. ceiling 1,116 rows, 169 matched, F2 0.450. cut 0.20: 358 rows, 142 matched, F2 0.635. | $3.71 | out/experiments/B.md |
| C maximum precision | done; upload held | 22:58 (commit b04b377) | local scores added to the five precision files. No platform upload. | $0 | out/experiments/C.md |
| D hedged cuts | done | 23:03 (commit 50d1b04) | best hedge 360 rows, 155 matched, F2 0.692. Hand read: the extra matches are shorter copies, not new obligations. | $0.82 | out/experiments/D.md |
| E verbatim rows | restarted at 23:07 after an abort | E.md still at 22:47; v3 file written, not committed | v3 finished: 311 rows, 137 matched, F2 0.640, $0.63. The agent died while scoring. Restarted to score v1–v3, write the report, and commit. No second paid run. | $1.79 | out/experiments/E.md |
| F row selector | done | 23:02 (commit 959a605) | votes-logit: 356 rows, 154 matched, F2 0.690. AUC 0.892. Word share left out. | $1.25 | out/experiments/F.md |
| G Sunday feasibility | running (agent live at 23:05) | 23:02 (commit b77e297) | plain bumper: Haiku vote, Sonnet F2 0.789, Opus-ref F2 0.686. Uncommitted: Sonnet weight 0.85 ($0.26) and fog Haiku seed 0 ($0.27). G2 and G3 still open. Do not start a second agent. | $2.25 | out/experiments/G.md |

## Upload queue (held)

The owner is at 4 of 5 platform uploads this hour (22:54). Do not ask for an upload until the
owner says a slot is free. Until every lane has local results, score with `tools/validate.py`,
`tools/score_local.py` (regulation and page), and `uv run python -m eval.score` (requirement
matched count and F2). The rows below stay as candidates, not as a request to upload.

| Order | File | Lane | Question it answers | Predicted matched / F2 | Uploaded at | Platform matched / F2 |
|---|---|---|---|---|---|---|
| 1 | `out/rear-lamp-swing-A-votes7.json` (351 rows) | A | Does a vote of 14 runs (7 or more agree, highest word-share row) beat every single run on the platform? | 157 / 0.707 (local 156 / 0.702) | | |
| 2 | `out/rear-lamp-swing-B-ceiling.json` | B | The platform's recall ceiling: every paragraph with a gold row plus every row any run wrote | 174 / 0.464 | | |
| 3 | `out/rear-lamp-swing-C-votes12.json` (149 rows) | C | What precision does the platform give the rows 12 or 13 of 13 runs agree on? (Cannot raise the leaderboard.) | 101 / 0.556 (P 0.68) | | |
| 4 | `out/rear-lamp-swing-B-cut020.json` | B | The same rewrite at the F2-optimal size; with the ceiling, the platform's match count in the tail | 147 / 0.657 | | |
| 5 | `out/rear-lamp-swing-A-votes4.json` (463 rows) | A | Does the platform find more matches in the 112 rows of a lower vote cut than the local judge does? | 163 / 0.669 (local 161 / 0.658) | | |

## Log

- 23:07 Lane E's agent aborted during scoring, before the report. Restarted it on the existing v3 file. Lane G's fog Haiku runs are still in progress; left alone. B and C completions were already recorded.
- 23:05 A, B, C, D and F have local validate, score_local and requirement F2 in their reports.
  E's v3 run finished ($0.63, 137 matched, F2 0.640) and G's Sonnet blend and first fog run
  finished; both agents were still writing at 23:05, so they were left running. No upload asked.
- 22:54 Owner: no more platform uploads this hour (4 of 5 used). Lanes must finish on local
  validate.py, score_local.py, and eval.score, and must not stop before those metrics are in
  the lane report. Cursor master restarted A, B, D, E, F, G at 22:52 and C at 22:54, and sent
  that instruction to each running agent.
- 22:50 Lanes B (done, $3.71), D (after D3, $0.82), F (after most of F3, $1.25) stopped. Lane G paused
  at 22:49 after part of G1 ($0.41). Claude Code master hit its usage limit here; Cursor takes over.

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
