# Lane L: one Sonnet run at weight 0.85, then the four-class filter

State: running. Updated: 24 Oct 23:40 CEST.
Approved spend: $5 in the ledger at 23:33 (planned cap), with the lane row saying not to duplicate H's weight-0.85 run. This lane was launched at $0 and has spent $0. No paid call in this lane.

## Checklist

- [x] L1 The Sonnet weight-0.85 lamp submission does not exist. Do not pay for a second copy.
      Done 24 Oct 23:40 CEST. Files: none new. Commit: (this commit).
      Found: `date` was Sat Oct 24 23:40:10 CEST 2026. `out/rear-lamp-swing-H-*` is absent.
      `out/experiments/H.md` is absent. No lamp file named for weight 0.85.
      The base for the filter is `out/rear-lamp-main-a39acab.json` (Opus relevance, Sonnet
      rewrite, blend weight 0.7, 388 rows). Spend $0.
- [ ] L2 Apply the four classes, with this lane's own rules, to `out/rear-lamp-main-a39acab.json`.
- [ ] L3 Sweep drop class 1, drop 1+2, drop 1+2+3, drop all four. For each: rows, matched, F2,
      and how many deleted rows were matched versus unmatched. Compare with votes7 and lane G.
- [ ] L4 Sunday command, with lane G's measured cost and wall time. Report. The lamp number
      stays on the weight-0.7 file until a weight-0.85 lamp file exists.

Next: write `brain/swing/l_filter.py` and tag `out/rear-lamp-main-a39acab.json`. No API calls.

## Run log rows

| Run | File | Method | Code | Rows | Local matched / F2 | Platform (upload): matched / F2 | Spend |
|---|---|---|---|---|---|---|---|

## Uploads

The owner closed the platform queue at 23:36. This lane does not nominate a file.

| File | Question | Predicted matched / F2 | Uploaded at | Platform matched / F2 |
|---|---|---|---|---|

## Notes

- Weight 0.85 on the lamp is lane H's file. This lane does not start a second copy.
- Until that file exists, every number below is on `out/rear-lamp-main-a39acab.json`.
- The four classes are text rules. Gold is used only after the cut, to count matches.

## Report

Not filled in yet.
