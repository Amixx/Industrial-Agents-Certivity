# Lane D: Hedged granularity, two cuts per likely paragraph

State: running. Updated: 24 Oct 22:46 CEST.
Approved spend: $2. Spent: $0.

## Checklist

- [x] D1 Natural experiment: union of `rear-lamp-mix.json` (split everything) and
      `rear-lamp-mix-examples-cut.json` (obligation cut), exact duplicates removed. Done 22:46.
      Files: `brain/swing/d_hedge.py`, `out/rear-lamp-swing-D-mix-cut-union.json`. Commit: see
      git log "swing D: steps 1 and 2". Spend $0.
      Found: union 660 rows, 155 matched, F2 0.546 (fine alone 395 / 148 / 0.641, coarse alone
      341 / 145 / 0.658). The cuts share 139 matched gold rows; either matches 154. +7 matches
      for +265 rows (0.03 per row, the break-even is about 0.13).
- [x] D2 Hedge selectively. Done 22:46. Files: `out/rear-lamp-swing-D-mix-cut-{union-near06,
      diff-fine,rel0.5-coarse,rel0.5-or-diff,first-near0.4}.json`,
      `out/rear-lamp-swing-D-fable-mix-first-near0.4.json`, `...-fable-mix-first-near0.5.json`,
      `...-kbjev-mix-first-near0.45.json`. Spend $0.
      Found: no selective hedge of the two Sonnet cuts beats a single cut (best 0.642 at
      relevance 0.6, coarse elsewhere; hedging only on gold paragraphs, an oracle, still loses:
      155 at 551). Hedging a coarser base from another model with the split rows that are not
      near duplicates (similarity < 0.4 to every base row on the paragraph) does win locally:
      Fable + split 359 rows / 150 / 0.670 (from 332 / 141 / 0.646); kb-jev + split
      442 / 164 / 0.682 (from 389 / 153 / 0.666).
- [ ] D3 Rebuild the coarse side without examples (`brain/swing/d_cut.py`, Sonnet, about $1).
- [ ] D4 Nominate the best hedged file, prediction first.

Next: D3, write `brain/swing/d_cut.py` and dry-run it for the cache-hit count and token estimate.

## Run log rows

| Run | File | Method | Code | Rows | Local matched / F2 | Platform (upload): matched / F2 | Spend |
|---|---|---|---|---|---|---|---|

## Uploads

| File | Question | Predicted matched / F2 | Uploaded at | Platform matched / F2 |
|---|---|---|---|---|

## Notes

## Report
