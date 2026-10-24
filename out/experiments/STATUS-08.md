# Complex strategies: status

Updated: 25 Oct 00:01 CEST (system clock, `date`) by master (Cursor).
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
| J skip classes on votes7 | running | 23:58 | J3 read the least-bad cut, sunday scores next | $0 | out/experiments/J.md |
| K same filter on votes4 | done | 23:53 | K4: filter does not beat votes7, not nominated | $0 | out/experiments/K.md |
| I table split into votes7 | done | 23:47 | I3 scored, 163 matched, F2 0.716, not nominated | $0 | out/experiments/I.md |
| H vote of three new runs | done | 23:59 | H4: 2 of 3 is 144/0.627, loses to run 1 and to votes7 | $4.34 | out/experiments/H.md |
| L Sonnet 0.85 plus filter | done | 23:58 | L5 scored the weight-0.85 file: 403/136/0.585, best cut 345/130/0.588, not within 5 of votes7 | $0 | out/experiments/L.md |

## Upload queue

Owner at 23:36: do not upload anything to the platform. Local tests only. This includes `out/rear-lamp-swing-A-votes7.json`. Do not nominate a file, do not set a lane to "waiting for upload", and do not ask the owner for a slot.

Score with `tools/validate.py`, `tools/score_local.py`, and `uv run python -m eval.score` from `brain/`.

| Order | File | Lane | Question it answers | Predicted matched / F2 | Uploaded at | Platform matched / F2 |
|---|---|---|---|---|---|---|
| — | none | — | queue closed by the owner | — | — | — |

## Log

- 00:01 Master checked lane L on the weight-0.85 file with `eval.errors`. Unfiltered 403 rows, 136 matched, F2 0.585. Best cut drop 1+2: 345 rows, 130 matched, F2 0.588. Biggest gap to 1.0 is 34 gold rows on paragraphs never cited (adding one row each reaches F2 0.720). Not uploaded. This step spent $0.
- 23:59 Lane H done. Three selections do not reach votes7. Run 1 reused 388/146/0.636. Sonnet weight 0.85: 403/136/0.585 ($3.16). Haiku relevance: 520/138/0.539 ($1.17). Vote 2 of 3: 388/144/0.627. Vote 3 of 3: 253/111/0.548. Both votes lose to run 1. Spend $4.34. Not nominated.
- 23:58 Lane L step 5 done. Weight-0.85 file 403 rows, 136 matched, F2 0.585. Best cut drop 1+2: 345 / 130 / 0.588. Biggest gap to 1.0 is the 34 gold rows on paragraphs never cited (adding one row each reaches F2 0.720). Not within 5 of votes7. Not nominated. Spend $0.
- 23:58 Lane J step 3. No cut still matches 151. Read 15 deleted and 10 unmatched kept rows from drop 1+2 (271 / 142 / 0.689), not adopted. The matched deletions name a test, a level, or a count. Spend $0.
- 23:55 Lane J step 2. Four cuts all lose to votes7. Best is drop 1+2: 271 rows, 142 matched, F2 0.689. Classes catch 86 of 151 outside rows and destroy 43 matches. No cut still matches 151. Spend $0.
- 23:56 Master checked lane K with `eval.errors`. Best cut drop class 1: 407 rows, 158 matched, F2 0.677. Biggest gap to 1.0 is 172 rows outside gold paragraphs (dropping them reaches F2 0.794). Does not beat votes7. Not uploaded. Spend $0.
- 23:56 Lane H wrote `out/rear-lamp-swing-H-sonnet-w85.json` (403 rows, 92 s, $3.16). Restarting lane L to filter that file only. No second paid copy.
- 23:55 Master checked lane L with `eval.errors`. Base is the weight-0.7 file: 388 rows, 146 matched, F2 0.636. Best cut drop 1+2: 315 rows, 138 matched, F2 0.642. Biggest gap to 1.0 on the unfiltered file is 177 rows outside gold paragraphs (dropping them reaches F2 0.747). Not uploaded. The weight-0.85 lamp file is still absent. If lane H writes it, restart L to filter that file only. Do not pay for a second copy.
- 23:53 Lane J step 1. Tagged votes7 with text rules: class hits 63 / 17 / 43 / 24, 139 rows in any class, 40 left ambiguous and not dropped. Spend $0. No model call.
- 23:53 Lane K done. Best cut drop class 1: 407 rows, 158 matched, F2 0.677, against votes7 351 / 156 / 0.702. Five extra matches: one untagged, one class 1, one class 2, two class 3. Not nominated. Spend $0.
- 23:53 Lane L done. Base `out/rear-lamp-main-a39acab.json` (weight 0.7): 388 rows, 146 matched, F2 0.636. Best filter drop 1+2: 315 / 138 / 0.642. votes7 is 351 / 156 / 0.702. Not within 5 matches. Not nominated. Spend $0. The weight-0.85 lamp file was not scored.
- 23:52 Lane K step 2. Four cuts of votes4. Best is drop class 1: 407 rows, 158 matched, F2 0.677. None beats votes7 (351 / 156 / 0.702). Spend $0.
- 23:51 Lane L step 3. Weight-0.7 file 388/146/0.636. Best cut is classes 1+2: 315/138/0.642, 18 matches behind votes7. Spend $0. Weight-0.85 lamp file still absent.
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
