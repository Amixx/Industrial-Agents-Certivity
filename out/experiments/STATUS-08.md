# Complex strategies: status

Updated: 24 Oct 23:50 CEST (system clock, `date`) by master (Cursor).
Task: brain/docs/todo/08-complex.md. Branch: big-swings. Setup done: yes (07 setup commit "swing master: setup"; this ledger created at 23:29).
Lanes A to G are finished. Do not edit their files except to read them. Do not edit `out/experiments/STATUS.md`.

## Budget

Approved by the owner at 23:33: all five lanes may spend. Per-lane maximum $20. Event ceiling $70, of which the swings spent $14.92. Remaining before this task: $55.08.
Planned caps inside that answer: J $1, K $1, I $1, H $6, L $5 ($14 together; event total about $28.92 if each uses its plan).
A lane that would pass its planned cap stops, writes the estimate, and waits. The master may grant more up to $20 for that lane while the event total stays at or under $70.
`claude -p` is not logged in. Paid steps use the API inside the lane cap. Dry-run or count cache hits before calling a step free.

## Lanes

| Lane | State | Last update | Current step | Spend so far | Lane file |
|---|---|---|---|---|---|
| J skip classes on votes7 | running | 23:33 | rules first; $1 approved if a model call is required | $0 | out/experiments/J.md |
| K same filter on votes4 | running | 23:48 | K1 tagged, sweep next, no model call | $0 | out/experiments/K.md |
| I table split into votes7 | done | 23:47 | I3 scored, 163 matched, F2 0.716, not nominated | $0 | out/experiments/I.md |
| H vote of three new runs | running | 23:33 | dry-run, then the three runs if the estimate is within $6 | $0 | out/experiments/H.md |
| L Sonnet 0.85 plus filter | running | 23:47 | L2: four classes tagged on the weight-0.7 file, 141 of 388 rows | $0 | out/experiments/L.md |

## Upload queue

Owner at 23:36: do not upload anything to the platform. Local tests only. This includes `out/rear-lamp-swing-A-votes7.json`. Do not nominate a file, do not set a lane to "waiting for upload", and do not ask the owner for a slot.

Score with `tools/validate.py`, `tools/score_local.py`, and `uv run python -m eval.score` from `brain/`.

| Order | File | Lane | Question it answers | Predicted matched / F2 | Uploaded at | Platform matched / F2 |
|---|---|---|---|---|---|---|
| — | none | — | queue closed by the owner | — | — | — |

## Log

- 23:50 Master checked lane I with `eval.errors`: 379 rows, 163 matched, F2 0.716. Biggest gap to 1.0 is the 151 rows outside gold paragraphs (dropping them reaches F2 0.825). Not uploaded.
- 23:48 Lane K step 1. Tagged votes4 with lexical class rules. 112 extra rows flagged. Spend $0. No model call.
- 23:47 Lane I done. Union 379 rows, 163 matched, F2 0.716. Matches gained 7, all on UN R10 6.9.1. Missed on a cited paragraph 16 (votes7 was 23). Spend $0. Not nominated: owner closed the queue.
- 23:47 Lane L step 2. Tagged `out/rear-lamp-main-a39acab.json`: 141 of 388 rows, class hits 55 / 18 / 66 / 16. Spend $0. Weight-0.85 lamp file still absent.
- 23:45 Lane I: step I2, 28 value lines added to votes7 (379 rows). Annex 9 3.1 already split, so those three lines were dropped. Spend $0.
- 23:40 Lane L step 1. Sonnet weight-0.85 lamp file is not on disk (no `out/rear-lamp-swing-H-*`). Spend stays $0. Filter starts on `out/rear-lamp-main-a39acab.json`.
- 23:40 Owner: build all five, score them only locally, and report here the rows, matched count, and F2 for each. For each file, name the single biggest reason F2 is not 1.0 (190 matched rows and 190 submitted rows). Use `eval.errors`: compare the F2 lift from dropping rows outside gold paragraphs, from recovering gold rows missed on a cited paragraph, and from citing gold paragraphs the file skips. The largest lift is the cause.
- 23:38 Lane I: running, step I1, four EMC paragraphs listed, no rows emitted, spend $0.
- 23:36 Owner: do not upload anything to the platform, only test locally. Queue closed, including votes7. Lanes keep scoring with validate.py, score_local.py, and eval.score.
- 23:33 Owner: max $70 overall, max $20 per lane. All five may spend. Planned caps stand (J $1, K $1, I $1, H $6, L $5). Agents were launched at $0; a lane that reads this file may now spend up to its planned cap. H and L still dry-run before any new call.
- 23:29 Ledger created. Asked the owner which lanes may spend. Started J, K, I, H, L at $0. Order of value: J, K, I, H, L. Engine freeze for task 06 is 02:00. A result after about 01:30 is a recommendation, not a code change. Agents: J 6b4acdae, K 6d903bb6, I b94a5ba5, H 9c188f65, L 009c0255.
