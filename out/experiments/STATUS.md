# Big swings: status

Updated: 24 Oct 22:42 CEST by master (Claude Code desktop, Opus 5.5).
Task: brain/docs/todo/07-big-swings.md. Branch: big-swings. Setup done: yes, commit "swing master: setup".

## Budget

Approved by the owner at 22:41: A $0, B $12, C $0, D $2, E $3, F $5, G $8 (the task's caps,
$30 in all). Hard ceiling for the whole task: **$70 total** (the API account has a €100 limit).
A lane that needs more than its cap asks the master; the master may grant it while the total
stays under $70, and must ask the owner above that.

## Lanes

| Lane | State | Last update | Current step | Spend so far | Lane file |
|---|---|---|---|---|---|
| A votes | not started | | | $0 | out/experiments/A.md |
| B maximum recall | not started | | | $0 | out/experiments/B.md |
| C maximum precision | not started | | | $0 | out/experiments/C.md |
| D hedged cuts | not started | | | $0 | out/experiments/D.md |
| E verbatim rows | not started | | | $0 | out/experiments/E.md |
| F row selector | not started | | | $0 | out/experiments/F.md |
| G Sunday feasibility | not started | | | $0 | out/experiments/G.md |

## Upload queue (owner uploads by hand, at most 5 per hour)

| Order | File | Lane | Question it answers | Predicted matched / F2 | Uploaded at | Platform matched / F2 |
|---|---|---|---|---|---|---|

## Log

- 22:42 Master started lanes A and C ($0), asked the budget, owner answered: caps as written,
  $70 total ceiling. Starting D, E, F, B, G.
- 22:36 Setup: copied the four `brain-model-mix-examples` files into `out/`, added
  `brain/swing/run_costed.py`.
- 22:35 A smoke test of the cost wrapper ran `main`'s defaults and made 23 Sonnet rewrite calls
  ($0.84): `main`'s rewrite prompt changed in `d7683cd`, so the rewrite was not cached. Saved
  as `out/rear-lamp-main-a39acab.json` (388 rows, 146 matched locally, F2 0.636) and added to
  the pool. Not uploaded.
