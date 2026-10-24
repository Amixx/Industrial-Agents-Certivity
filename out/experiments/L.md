# Lane L: one Sonnet run at weight 0.85, then the four-class filter

State: done. Updated: 24 Oct 23:53 CEST.
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
      Commit: c036e8c. Spend $0. All four pass `tools/validate.py`. Requirement numbers are
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
- [x] L4 Sunday command, with lane G's measured cost and wall time. Report. The lamp number
      stays on the weight-0.7 file until a weight-0.85 lamp file exists.
      Done 24 Oct 23:53 CEST. `date` was Sat Oct 24 23:53:10 CEST 2026. Still no
      `out/rear-lamp-swing-H-*` and no `out/experiments/H.md`. The weight-0.85 lamp file
      was not scored. Spend $0. No upload nominated.

Next: none. Lane done.

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

The bumper winner plus this skip filter does not come within 5 matches of votes7. On `out/rear-lamp-main-a39acab.json` (Opus relevance, Sonnet rewrite, blend weight 0.7, the only lamp base on disk) the unfiltered file is 388 rows, 146 matched, F2 0.636, already 10 short of votes7, and the best cut is 315 rows, 138 matched, F2 0.642.

The Sonnet weight-0.85 lamp submission was not on disk at 23:53. This lane did not pay for a second copy. Every lamp number below is the weight-0.7 file. Scored 24 Oct 23:50 CEST with `tools/validate.py`, `tools/score_local.py`, and `uv run python -m eval.score` from `brain/`. `eval.errors` is the gap split. Spend $0.

| Cut | Rows | Matched | F2 | Deleted matched | Deleted unmatched | Deleted outside gold paragraphs |
|---|---|---|---|---|---|---|
| unfiltered, weight 0.7 | 388 | 146 | 0.636 | | | |
| drop class 1 | 333 | 140 | 0.640 | 6 | 49 | 44 |
| drop 1+2 | 315 | 138 | 0.642 | 8 | 65 | 58 |
| drop 1+2+3 | 259 | 115 | 0.564 | 31 | 98 | 81 |
| drop all four | 247 | 110 | 0.546 | 36 | 105 | 87 |
| votes7, rescored | 351 | 156 | 0.702 | | | |

Regulation precision, recall and F1 are 1.000 on every file (4 / 4 / 4). Page F2 from `eval.score`: unfiltered 0.894, drop 1 and drop 1+2 both 0.879, drop 1+2+3 0.849, all four 0.836, votes7 0.904.

Classes 1 and 1+2 raise F2 by 0.004 and 0.006, because the unmatched rows they delete outnumber the matches, and then stop. That rise is smaller than the noise of about 5 matches. Class 3 deletes 31 matches against 98 unmatched rows and F2 falls to 0.564. The six matches class 1 removes are measurement-setup and pulse-application rows, not the immersion and wipe steps. Class 2 removes two further matches, both counts: two stop lamps fitted, and two retro-reflectors.

Why F2 is not 1.0 on the unfiltered file, from `eval.errors`, each lever closed on its own: dropping the 177 rows outside gold paragraphs reaches F2 0.747 (lift 0.111, and one of those rows was matched, so the kept file is 145 matched in 211 rows). Matching the 25 gold rows missed on a cited paragraph, with no new row, reaches 0.745 (lift 0.109). Adding the 19 gold rows on paragraphs the file never cites, one row each, reaches 0.707 (lift 0.071). The largest lift is the rows outside gold paragraphs. On the best cut the order changes: the 28 on-cited misses are then the larger remaining lift (0.772 if the row count stays), because the filter has already spent some of the outside rows and some matches.

Lane G, paragraph F2 against 67 silver bumper paragraphs, not this requirement judge: plain Sonnet weight 0.85 is P 0.79, R 0.85, F2 0.838 (143 rows). Plain Sonnet weight 0.7 is F2 0.789. Fog Sonnet weight 0.85 is P 0.74, R 0.79, F2 0.779. The lamp weight-0.7 requirement F2 of 0.636 and the bumper paragraph F2 are different scores. What they share is that one Sonnet run is the file, and this filter does not turn that run into the 14-run vote.

**Upload.** None. The owner closed the queue at 23:36. The best local F2 here is 0.642, which does not beat 0.702.

**Transfer.** The filter was not run on the bumper. Lane G already scored the unfiltered Sonnet weight-0.85 run on both bumpers. This lane has no bumper number for the filter.

**Sunday.** Run the unfiltered Sonnet weight-0.85 command. Do not append this filter: on the lamp it does not come within 5 matches of votes7. From `brain/`, after the 08:30 review, put the kept regulation ids in `--only`:

```bash
PYTHONPATH=. uv run python swing/g_runs.py run \
  data/synthetic/bumper-sensors-fog \
  --name sonnet-w85 \
  --rel-model claude-sonnet-5-5 \
  --rw-model claude-sonnet-5-5 \
  --weight 0.85 \
  --only "UN R10" "UN R48" "UN R149" "UN R148" "UN R127" "UN GTR 9" "UN R42" "UN R26"

uv run python ../tools/validate.py ../out/experiments/G-bumper-sensors-fog-sonnet-w85.json
```

Replace the case path and the `--only` list with the held-out case and the review. Lane G measured the fog bumper at 134 s and $4.33, paragraph F2 0.779 on the four labelled regulations, 519 rows in the file. The same models and weight on the plain bumper, with `--only "UN R42" "UN R26" "UN R127" "UN GTR 9"`, scored paragraph F2 0.838. That run was 21 s and $0.257 because relevance was cached. A cold run of that size is about 60 s and about $1.15. `--weight` has to go through `g_runs.py`. The four-cut sweep in this lane took from 23:49:43 to 23:49:46 CEST and cost $0. The filter command, if someone still wants the file that scored 0.642 on the weight-0.7 lamp, is:

```bash
BRAIN_LLM= PYTHONPATH=. uv run python swing/l_filter.py cut SUBMISSION --drop 1,2 -o FILTERED.json
```

The lamp number in this report uses `out/rear-lamp-main-a39acab.json`. The Sunday weight-0.85 lamp file was not scored.
