# Lane H: a vote of three runs we can produce

State: done. Updated: 24 Oct 23:59 CEST.
Approved spend: $6 (owner, 23:33, planned cap; lane maximum $20). Spent: $4.34.

## Checklist

- [x] H1 Reuse Opus relevance, blend weight 0.7, the pipeline cut, if the prompt matches.
      Done 24 Oct 23:49 CEST. File: `out/rear-lamp-main-a39acab.json` (reused).
      Commit: `0b1c87a`. Found: prompt matches. 388 rows, 146 matched, F2 0.636.
      Opus relevance 113/113 cache hits. Sonnet rewrite 23/23 cache hits. Spend $0.
- [x] H2 Sonnet relevance and rewrite, blend weight 0.85.
      Dry-run 23:49, commit `0b1c87a`: 0/113 relevance hits, estimate $2.241 plus about $1.12 rewrite.
      Run 23:55, commit `69e9927`. 301 paragraphs, 403 rows, 136 matched, F2 0.585. Spend $3.162. 92 s.
- [x] H3 Haiku relevance, blend weight 0.85, Sonnet rewrite of the paragraphs Haiku selected.
      Dry-run 23:49: 0/113 relevance hits, estimate $0.112 plus about $1.12 rewrite.
      Run 23:56, commit `a07209e`. 348 paragraphs, 520 rows, 138 matched, F2 0.539. Spend $1.174. 70 s.
- [x] H4 Vote at 2 of 3 and at 3 of 3, representative text from run 2.
      Done 24 Oct 23:57 CEST. Commit: `e28ffbe`. Jaccard 0.5, the votes7 setting.
      2 of 3: 388 rows, 144 matched, F2 0.627. 3 of 3: 253 rows, 111 matched, F2 0.548.
      The historical 14 files are not in this vote. Spend $0.

Next: none. The question is answered below.

## Run log rows

| Run | File | Method | Code | Rows | Local matched / F2 | Platform (upload): matched / F2 | Spend |
|---|---|---|---|---|---|---|---|
| 24 Oct 23:49 | out/rear-lamp-main-a39acab.json | reused: Opus relevance, blend 0.7, Sonnet rewrite, main's prompt (`d7683cd`) | pipeline, already on disk | 388 | 146 / 0.636 | not uploaded | $0 |
| 24 Oct 23:55 | out/rear-lamp-swing-H-sonnet-w85.json | Sonnet 5.5 relevance and rewrite, blend 0.85, Opus profile kept | h_run.py | 403 | 136 / 0.585 | not uploaded | $3.162 |
| 24 Oct 23:56 | out/rear-lamp-swing-H-haiku-rel.json | Haiku 5.5 relevance, blend 0.85, Sonnet rewrite | h_run.py | 520 | 138 / 0.539 | not uploaded | $1.174 |
| 24 Oct 23:57 | out/rear-lamp-swing-H-vote2.json | row vote, 2 of these 3, Jaccard 0.5, text from run 2 | h_vote.py | 388 | 144 / 0.627 | not uploaded | $0 |
| 24 Oct 23:57 | out/rear-lamp-swing-H-vote3.json | row vote, 3 of these 3, same representative | h_vote.py | 253 | 111 / 0.548 | not uploaded | $0 |

## Uploads

None. The best file in this lane is the reused Opus run, 146 matched, F2 0.636. votes7 is 156 / 0.702. Nothing here beats 0.702. The owner closed the upload queue at 23:36.

## Notes

The ledger still said $0 when this lane started. The dry run was finished before any call. At 23:50 the ledger showed the owner's 23:33 answer: lane H may spend, planned cap $6. The dry-run total was $4.59, under that cap, so runs 2 and 3 were made. Actual spend $4.336.

Run 1 was not regenerated. `rewrite.py` last changed in `d7683cd` at 21:44, and the file was written at 22:35. The dry run reproduces that log: UN R148 0.95, UN R48 0.92, UN R150 0.88, UN R10 0.85; weight 0.7 keeps 267 paragraphs; the Sonnet rewrite of that list is 23 cache hits. Profile and regulation review are 2 cached Opus calls. They were hits again on both paid runs.

`h_dry.py` refuses the network and was calibrated to `out/rear-lamp-mix-noimage.log` ($4.65; the rebuild came out $4.689). Haiku rates are `g_runs.py`: $0.10 / $0.50 / $0.01 per million. The paid runs landed next to the estimate:

| Piece | Dry-run | Paid |
|---|---|---|
| Sonnet relevance, 113 batches (114 with one retry) | $2.241, 0 hits | $2.287, 0 hits |
| Sonnet rewrite of the Sonnet selection | $1.12 at the 362-paragraph Opus proxy | $0.875, 301 paragraphs, 0 hits |
| Haiku relevance, 113 batches | $0.112, 0 hits | $0.115, 0 hits |
| Sonnet rewrite of the Haiku selection | $1.12 on the same proxy | $1.059, 348 paragraphs, 0 hits |

Weight 0.85 with cached Opus scores would have kept 362 paragraphs, and those 31 rewrite batches were all misses. The real selections were smaller and still missed every rewrite batch. The cached rewrites are exactly the weight-0.7 list.

Scored with `tools/validate.py` (all four new files valid) and `uv run python -m eval.score`, which includes the regulation and page levels from `tools/score_local.py`. `eval.errors` at 23:57:

| File | Rows | Outside gold paragraphs | Missed on a cited paragraph | Gold rows on paragraphs never cited | F2 | F2 if outside rows are dropped |
|---|---|---|---|---|---|---|
| Run 1, Opus 0.7 | 388 | 177 | 25 | 19 | 0.636 | 0.747 |
| Run 2, Sonnet 0.85 | 403 | 204 | 23 | 31 | 0.585 | 0.693 |
| Run 3, Haiku 0.85 | 520 | 327 | 22 | 30 | 0.539 | 0.714 |
| Vote, 2 of 3 | 388 | 177 | 28 | 18 | 0.627 | 0.742 |
| Vote, 3 of 3 | 253 | 95 | 24 | 55 | 0.548 | 0.605 |

Why F2 is not 1.0. The three lifts are: drop every row outside a gold paragraph (the oracle printed above); turn the on-cited misses into matches without adding rows; add one matching row for each gold row on a paragraph the file never cites.

| File | Lift from dropping outside rows | Lift from recovering on-cited misses | Lift from citing the skipped gold rows | Largest |
|---|---|---|---|---|
| Run 1 | 0.111 | 0.109 | 0.071 | outside rows |
| Run 2 | 0.108 | 0.099 | 0.114 | paragraphs never cited |
| Run 3 | 0.175 | 0.086 | 0.102 | outside rows |
| 2 of 3 | 0.115 | 0.122 | 0.068 | on-cited misses |
| 3 of 3 | 0.057 | 0.118 | 0.230 | paragraphs never cited |

## Report

Three runs we can produce on Sunday do not reach most of the 14-run gain. votes7 is 156 matched and F2 0.702. The 2-of-3 vote is 144 / 0.627, and the 3-of-3 vote is 111 / 0.548. The best of the three single runs is the reused Opus file at weight 0.7, 146 / 0.636, and both votes lose to it. The 0.702 figure is a property of that 14-file pool. It is not what these three selections produce.

| File | Rows | Matched | F2 | Against votes7 |
|---|---|---|---|---|
| votes7 (lane A, not in this vote) | 351 | 156 | 0.702 | — |
| Run 1, Opus relevance, weight 0.7 | 388 | 146 | 0.636 | −10 matches |
| Run 2, Sonnet relevance and rewrite, weight 0.85 | 403 | 136 | 0.585 | −20 matches |
| Run 3, Haiku relevance, Sonnet rewrite, weight 0.85 | 520 | 138 | 0.539 | −18 matches |
| Vote, 2 of 3, text from run 2 | 388 | 144 | 0.627 | −12 matches |
| Vote, 3 of 3, text from run 2 | 253 | 111 | 0.548 | −45 matches |

From run 1 (0.636) to votes7 (0.702) is 0.066 F2 and 10 matches. The 2-of-3 vote is below run 1, so it takes none of that gain. From run 2 (0.585) the same distance is 0.117 and 20 matches. The 2-of-3 vote picks up 8 matches and 0.042 F2, about a third of the way, not most of it. The 3-of-3 vote loses to run 2 alone (111 against 136). The 2-of-3 vote does not: 144 beats run 2's 136. Beating the Sonnet run is not the same as beating the best run. Agreement here mostly copied run 1 (388 rows, 177 of them outside gold paragraphs, two fewer matches).

On the lamp, Sonnet at blend weight 0.85 is worse than Opus at 0.7. It cites 31 gold rows' paragraphs that it never reaches, against 19 for the Opus file, and it adds outside rows (204 against 177). That is the flood the relevance comment already estimated for weight 0.85 on this product. Lane G's weight 0.85 result was on the bumper, where the decision model is weak. These two cases disagree. A three-run vote is not the Sunday method, and on the lamp the single run to beat is still Opus relevance at weight 0.7, not the Sonnet weight-0.85 run.

**Uploads.** None.

**Transfer.** Not run again. The lamp result does not by itself change the bumper recommendation in lane G. It does say that a vote of one rewrite prompt across three relevance settings failed to move the lamp.

**Sunday.** One Sonnet run at weight 0.85 remains lane G's bumper command. This lane does not replace it with a vote. Building the vote on the lamp cost $4.34 and about three minutes (92 s and 70 s), because Opus relevance and the weight-0.7 rewrite were cached and the other two relevance passes were not. On a cold bumper those relevance passes are the expensive part, and the vote still lost to the best single file.
