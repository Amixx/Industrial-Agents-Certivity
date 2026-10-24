# Lane L: one Sonnet run at weight 0.85, then the four-class filter

State: running. Updated: 24 Oct 23:47 CEST.
Approved spend: $5 in the ledger at 23:33 (planned cap), with the lane row saying not to duplicate H's weight-0.85 run. This lane was launched at $0 and has spent $0. No paid call in this lane.

## Checklist

- [x] L1 The Sonnet weight-0.85 lamp submission does not exist. Do not pay for a second copy.
      Done 24 Oct 23:40 CEST. Files: none new. Commit: b4bfc30.
      Found: `date` was Sat Oct 24 23:40:10 CEST 2026. `out/rear-lamp-swing-H-*` is absent.
      `out/experiments/H.md` is absent. No lamp file named for weight 0.85.
      The base for the filter is `out/rear-lamp-main-a39acab.json` (Opus relevance, Sonnet
      rewrite, blend weight 0.7, 388 rows). Spend $0.
- [x] L2 Apply the four classes, with this lane's own rules, to `out/rear-lamp-main-a39acab.json`.
      Done 24 Oct 23:47 CEST. Files: `brain/swing/l_filter.py`, `out/experiments/L-tags.json`.
      Commit: this commit. Found: 388 rows, 141 tagged. Class hits: 1 procedure 55,
      2 installation one-liner 18, 3 optional or absent variant 66, 4 pointer 16.
      A row can carry more than one class. Spend $0. No gold text in the rules.
- [ ] L3 Sweep drop class 1, drop 1+2, drop 1+2+3, drop all four. For each: rows, matched, F2,
      and how many deleted rows were matched versus unmatched. Compare with votes7 and lane G.
- [ ] L4 Sunday command, with lane G's measured cost and wall time. Report. The lamp number
      stays on the weight-0.7 file until a weight-0.85 lamp file exists.

Next: from `brain/`, `BRAIN_LLM= PYTHONPATH=. uv run python swing/l_filter.py sweep ../out/rear-lamp-main-a39acab.json`, then score each cut with `tools/validate.py`, `tools/score_local.py`, and `uv run python -m eval.score`. No API calls.

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
- The four classes are text rules in `brain/swing/l_filter.py`. Gold is used only after a cut, to count matches.
- Class 1 is a step that prepares, immerses, sprays, wipes, or measures a sample, including which sample group is sent to which test. A sentence that states the pass or fail stays.
- Class 2 is orientation, count, bare presence, or "at the rear", and only when the sentence has no width, height, or angle. Colour rows stay. They state a value.
- Class 3 is a sentence that exists only for equipment it introduces as optional, alternative, or absent (LED substitute, light-source module, control gear outside the body, reciprocal incorporation, fail-safe, optional lamps, TOP mark, low mounting check, interdependent or movable installation, a supply the sentence itself calls special). A base-lamp rule that merely excepts that equipment stays.
- Class 4 is a row whose only demand is a table, paragraph, section, or annex, and which states no value of its own. "Shall meet the requirements" with no such target stays.

## Report

Not filled in yet.
