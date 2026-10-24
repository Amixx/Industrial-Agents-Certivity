# Lane B: maximum recall, then measure the tail

State: waiting for upload (B4, B6); transfer check running. Updated: 24 Oct 22:47 CEST.
Approved spend: $12. Spent: $2.03 (plus the bumper transfer check, about $1.5, running).

## Checklist

- [x] B1 Rank every candidate paragraph of the four regulations by the cached Opus relevance score.
      Done 22:40. Files: `out/experiments/B-scores.json` (2,805 candidates, blend, LLM and
      decision-model score, gold rows per paragraph), `brain/swing/b_recall.py`. Spend $0 (115
      Opus cache hits, no miss). Found: all 119 gold paragraphs (187 of 190 gold rows; 3 sit on
      labels that are not candidates) have blend >= 0.05, the top 713 paragraphs. The pipeline's
      cut (0.20 plus floor, 267 paragraphs) holds 107 gold paragraphs and 165 gold rows; 0.05 to
      0.20 adds 12 gold paragraphs and 22 gold rows over 468 paragraphs; below 0.05 (1,092
      paragraphs) there is no gold paragraph.
- [x] B2 Rewrite every paragraph down to a very low score (0.03) with `main`'s rewrite prompt.
      Done 22:42 (58 s). Files: `out/rear-lamp-swing-B-full.json` (+ `.log`), cut 0.05 subset
      `out/rear-lamp-swing-B-full005.json`. Spend $2.03 (70 new Sonnet calls, 314k in / 139k
      out; the 23 pipeline batches came from the cache). Found: 1,097 paragraphs, 1,382 rows,
      158 matched locally (F2 0.369). Every match is in the top 812 rows (blend >= 0.06); the
      520 rows below 0.05 match nothing.
- [x] B3 Add the rows only other runs found (union with lane A's pool). Done 22:45. Files:
      `brain/swing/b_tail.py`, `out/rear-lamp-swing-B-union.json` (1,636 rows). Spend $0.
      Found: 254 of A's 949 clusters (in the four regulations) have no row of ours within
      Jaccard 0.5 on the same paragraph; adding their medoids lifts local matched 158 -> 169
      (P(match) of a pool row 0.043). Union at blend >= 0.05: 1,116 rows, 169 matched.
- [x] B4 Nominate the full file for one upload. Done 22:46. File:
      `out/rear-lamp-swing-B-ceiling.json` (union, blend >= 0.05; 1,116 rows, local 169, F2
      0.450). Predicted platform 174 matched (range 168 to 180), F2 0.464.
- [x] B5 Nested cuts by score, P(match) per bucket, F2-optimal size. Done 22:45 (local judge;
      platform calibration waits for the B4 and B6 uploads). Found: P(match) per row is 0.60
      above 0.4, 0.42 at 0.3 to 0.4, 0.16 to 0.21 at 0.2 to 0.3, 0.07 to 0.10 at 0.15 to 0.2,
      and 0.02 or less below 0.15. Keeping buckets while P > F2/5 (about 0.13) stops at blend
      0.20: 358 rows, 142 matched, F2 0.635. The local F2 is flat (0.625 to 0.646) from 320 to
      440 rows, so the optimum is a range, not a point. Table under Notes.
- [x] B6 Second nomination: the file at that F2-optimal size. Done 22:46. File:
      `out/rear-lamp-swing-B-cut020.json` (358 rows, local 142, F2 0.635). Predicted platform
      147 matched, F2 0.657.

Next: transfer check on the bumper silver labels (running, log
`out/experiments/B-transfer-bumper-plain.log`; rerun: from `brain/`,
`B_MODE=run B_CASE=data/synthetic/bumper-plain PYTHONPATH=. uv run python swing/b_transfer.py`,
cached after the first run). Then the report. When the platform numbers for B4 and B6 come back,
fill the calibration line under Notes: platform matches in the tail = ceiling minus cut020.

## Run log rows

| Run | File | Method | Code | Rows | Local matched / F2 | Platform (upload): matched / F2 | Spend |
|---|---|---|---|---|---|---|---|
| 22:41 | `rear-lamp-swing-B-full.json` | `main`'s Opus relevance (cached) and Sonnet rewrite prompt (`d7683cd`), every paragraph with blend >= 0.03 (1,097) | `big-swings`, `swing/b_recall.py` | 1,382 | 158 / 0.369 | not uploaded | $2.03 |
| 22:45 | `rear-lamp-swing-B-full005.json` | The above, blend >= 0.05 | `swing/b_tail.py cut` | 862 | 158 / 0.487 | not uploaded | $0 |
| 22:45 | `rear-lamp-swing-B-union.json` | `B-full` plus 254 medoids of lane A clusters it does not cover | `swing/b_tail.py union` | 1,636 | 169 / 0.353 | not uploaded | $0 |
| 22:45 | `rear-lamp-swing-B-ceiling.json` | The union, blend >= 0.05 | `swing/b_tail.py cut` | 1,116 | 169 / 0.450 | nominated | $0 |
| 22:45 | `rear-lamp-swing-B-cut020.json` | `B-full`, blend >= 0.20 (the pipeline's cut without its floor) | `swing/b_tail.py cut` | 358 | 142 / 0.635 | nominated | $0 |

## Uploads

| File | Question | Predicted matched / F2 | Uploaded at | Platform matched / F2 |
|---|---|---|---|---|
| `out/rear-lamp-swing-B-ceiling.json` | The platform's recall ceiling: every paragraph that holds a gold row, plus every row any other run wrote | 174 / 0.464 | | |
| `out/rear-lamp-swing-B-cut020.json` | Same rewrite at the F2-optimal size; with the ceiling it gives the platform's match count in the tail (blend < 0.20 plus pool rows), locally 27 matches over 758 rows | 147 / 0.657 | | |

## Notes

- B1 paragraph table (blend score = decision model and Opus relevance, `relevance.blend`):

  | Blend in | Paragraphs | Cumulative | Gold paragraphs | Cum. | Gold rows | Cum. |
  |---|---|---|---|---|---|---|
  | 0.50 to 1 | 20 | 20 | 19 | 19 | 29 | 29 |
  | 0.30 to 0.50 | 106 | 126 | 69 | 88 | 109 | 138 |
  | 0.20 to 0.30 | 119 | 245 | 19 | 107 | 27 | 165 |
  | 0.15 to 0.20 | 101 | 346 | 6 | 113 | 14 | 179 |
  | 0.10 to 0.15 | 125 | 471 | 3 | 116 | 4 | 183 |
  | 0.07 to 0.10 | 118 | 589 | 1 | 117 | 2 | 185 |
  | 0.05 to 0.07 | 124 | 713 | 2 | 119 | 2 | 187 |
  | 0.03 to 0.05 | 384 | 1,097 | 0 | 119 | 0 | 187 |
  | below 0.03 | 1,708 | 2,805 | 0 | 119 | 0 | 187 |

- B2 cost estimate before the run (`plan --cut 0.03`): the 267 pipeline paragraphs are 23
  cached batches; the 830 tail paragraphs are 70 new Sonnet batches, about 263k input tokens.
  At the reference rate ($0.85 for 267 paragraphs) that is about $2.70; cap $12.
- B5 curve, `B-full` (one rewrite, no pool rows), each cut matched on its own by the local
  judge (`b_tail.py curve`):

  | Blend >= | Rows | Matched | Local F2 | Rows added | Matches added | P(match) of added rows |
  |---|---|---|---|---|---|---|
  | 0.50 | 50 | 30 | 0.185 | 50 | 30 | 0.60 |
  | 0.40 | 122 | 73 | 0.414 | 72 | 43 | 0.60 |
  | 0.30 | 228 | 117 | 0.592 | 106 | 44 | 0.42 |
  | 0.25 | 278 | 125 | 0.602 | 50 | 8 | 0.16 |
  | 0.20 | 358 | 142 | **0.635** | 80 | 17 | 0.21 |
  | 0.175 | 420 | 148 | 0.627 | 62 | 6 | 0.10 |
  | 0.15 | 462 | 151 | 0.618 | 42 | 3 | 0.07 |
  | 0.125 | 512 | 152 | 0.598 | 50 | 1 | 0.02 |
  | 0.10 | 582 | 153 | 0.570 | 70 | 1 | 0.01 |
  | 0.07 | 716 | 156 | 0.528 | 134 | 3 | 0.02 |
  | 0.05 | 862 | 158 | 0.487 | 146 | 2 | 0.01 |
  | 0.03 | 1,382 | 158 | 0.369 | 520 | 0 | 0 |

  Finer, by row count: 323 rows (blend 0.223) 140 matched F2 0.646; 364 rows 142 0.632; 401
  rows 146 0.629; 440 rows 150 0.625; 481 rows 151 0.608. Ranking by the Opus score alone is
  worse (best 0.624 at 354 rows) and the decision model alone much worse (best 0.446), so the
  blend is the right ranking.
- The pool rows (union minus full, same cut): +10 matches for 190 rows at blend >= 0.20, +11 for
  254 at >= 0.05. They are worth about 0.04 a row: below F2/5 at any cut.
- Platform calibration (fill in after the uploads): ceiling platform matched minus cut020
  platform matched = platform matches in the tail; local says 27 (169 - 142). If the platform
  finds clearly more (say 35 or more), its P(match) in the 0.15 to 0.20 bucket clears 0.13 and
  the optimal cut moves down to about 0.15.
- `claude -p` is not logged in for lane agents (master, 22:43); everything here ran on the API.
- The tail is rewritten in score order in batches of 12, so the 0.05 file is the 0.03 file
  filtered by `confidence >= 0.05` (only one boundary batch mixes the two).

## Report
