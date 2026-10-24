# Lane L: one Sonnet run at weight 0.85, then the four-class filter

State: running. Updated: 24 Oct 23:51 CEST.
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
      Commit: 9584eab. Found: 388 rows, 141 tagged. Class hits: 1 procedure 55,
      2 installation one-liner 18, 3 optional or absent variant 66, 4 pointer 16.
      A row can carry more than one class. Spend $0. No gold text in the rules.
- [x] L3 Sweep drop class 1, drop 1+2, drop 1+2+3, drop all four. For each: rows, matched, F2,
      and how many deleted rows were matched versus unmatched. Compare with votes7 and lane G.
      Done 24 Oct 23:50 CEST. Files: `out/rear-lamp-swing-L-drop1.json`, `drop12`, `drop123`,
      `drop1234`, their `.log` files, `out/experiments/L-sweep.json`, `out/experiments/L-official.txt`.
      Commit: this commit. Spend $0. All four pass `tools/validate.py`. Requirement numbers are
      `eval.score`. Deleted matched and unmatched are the local judge on the unfiltered file.

      | Cut | Rows | Matched | F2 | Deleted | Deleted matched | Deleted unmatched | Of which outside gold paragraphs |
      |---|---|---|---|---|---|---|---|
      | unfiltered weight 0.7 | 388 | 146 | 0.636 | | | | |
      | drop 1 | 333 | 140 | 0.640 | 55 | 6 | 49 | 44 |
      | drop 1+2 | 315 | 138 | 0.642 | 73 | 8 | 65 | 58 |
      | drop 1+2+3 | 259 | 115 | 0.564 | 129 | 31 | 98 | 81 |
      | drop all four | 247 | 110 | 0.546 | 141 | 36 | 105 | 87 |
      | votes7 | 351 | 156 | 0.702 | | | | |

      votes7 rescored in the same run: 351 rows, 156 matched, F2 0.702. The unfiltered file is
      10 matches short of it. The best filtered file (drop 1+2) is 18 short. None is within 5.
      Classes 1 and 1+2 raise F2 by 0.004 and 0.006. Class 3 pulls F2 down to 0.564.
      Lane G's bumper numbers are paragraph F2, not this judge: plain Sonnet weight 0.85 is
      0.838 (P 0.79, R 0.85), plain Sonnet weight 0.7 is 0.789, fog Sonnet weight 0.85 is 0.779.
- [ ] L4 Sunday command, with lane G's measured cost and wall time. Report. The lamp number
      stays on the weight-0.7 file until a weight-0.85 lamp file exists.

Next: write the Sunday command from lane G, fill the report, set state to done. The weight-0.85 lamp file is still absent, so the report stays on the weight-0.7 file.

## Run log rows

| Run | File | Method | Code | Rows | Local matched / F2 | Platform (upload): matched / F2 | Spend |
|---|---|---|---|---|---|---|---|
| 24 Oct 23:50 | out/rear-lamp-main-a39acab.json | existing weight 0.7 file, rescored, not produced here | | 388 | 146 / 0.636 | not uploaded | $0 |
| 24 Oct 23:50 | out/rear-lamp-swing-L-drop1.json | drop class 1, text rules | l_filter.py | 333 | 140 / 0.640 | not uploaded | $0 |
| 24 Oct 23:50 | out/rear-lamp-swing-L-drop12.json | drop classes 1 and 2 | l_filter.py | 315 | 138 / 0.642 | not uploaded | $0 |
| 24 Oct 23:50 | out/rear-lamp-swing-L-drop123.json | drop classes 1, 2 and 3 | l_filter.py | 259 | 115 / 0.564 | not uploaded | $0 |
| 24 Oct 23:50 | out/rear-lamp-swing-L-drop1234.json | drop classes 1, 2, 3 and 4 | l_filter.py | 247 | 110 / 0.546 | not uploaded | $0 |

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
