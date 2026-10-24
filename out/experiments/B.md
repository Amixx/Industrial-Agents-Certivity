# Lane B: maximum recall, then measure the tail

State: running. Updated: 24 Oct 22:55 CEST.
Approved spend: $12. Spent: $0.

## Checklist

- [x] B1 Rank every candidate paragraph of the four regulations by the cached Opus relevance score.
      Done 22:58. Files: `out/experiments/B-scores.json` (2,805 candidates, blend, LLM and
      decision-model score, gold rows per paragraph), `brain/swing/b_recall.py`. Spend $0 (115
      Opus cache hits, no miss). Found: all 119 gold paragraphs (187 of 190 gold rows; 3 sit on
      labels that are not candidates) have blend >= 0.05, the top 713 paragraphs. The pipeline's
      cut (0.20 plus floor, 267 paragraphs) holds 107 gold paragraphs and 165 gold rows; 0.05 to
      0.20 adds 12 gold paragraphs and 22 gold rows over 468 paragraphs; below 0.05 (1,092
      paragraphs) there is no gold paragraph.
- [ ] B2 Rewrite every paragraph down to a very low score (0.03) with `main`'s rewrite prompt
- [ ] B3 Add the rows only other runs found (union with lane A's pool)
- [ ] B4 Nominate the full file for one upload (recall ceiling, precision floor)
- [ ] B5 Cut the full file into nested subsets by score; P(match) per bucket and the F2-optimal size
- [ ] B6 Second nomination: the file at the F2-optimal size

Next: B2 is running (started 22:59):
`PYTHONPATH=. uv run python swing/b_recall.py run --cut 0.03 --approved -o ../out/rear-lamp-swing-B-full.json`
(log `out/rear-lamp-swing-B-full.log`). If it died, rerun the same command: finished batches
come back from the cache.

## Run log rows

| Run | File | Method | Code | Rows | Local matched / F2 | Platform (upload): matched / F2 | Spend |
|---|---|---|---|---|---|---|---|

## Uploads

| File | Question | Predicted matched / F2 | Uploaded at | Platform matched / F2 |
|---|---|---|---|---|

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
- The tail is rewritten in score order in batches of 12, so the 0.05 file is the 0.03 file
  filtered by `confidence >= 0.05` (only one boundary batch mixes the two).

## Report
