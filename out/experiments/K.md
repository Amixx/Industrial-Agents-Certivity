# Lane K: the four classes on the 4-vote file

State: done. Updated: 24 Oct 23:53 CEST.
Approved spend: $0 for this run. The ledger at 23:33 allows a planned $1. This run does not use it. Spent: $0.

## Checklist

- [x] K1 Tag `out/rear-lamp-swing-A-votes4.json`. The 112 rows votes7 does not contain are flagged `in_votes7: false`. Done 24 Oct 23:48 CEST. Files: `brain/swing/k_filter.py`, `out/experiments/K-tags.json`.
      Found: 463 rows, classes 1 / 2 / 3 / 4 on 56 / 12 / 100 / 22 rows. Of the 112 extra rows, 63 carry a class, 7 are ambiguous, 43 are neither. Ambiguous rows are not dropped. No model call. Commit: `ea9314d`.
- [x] K2 Sweep drop 1, drop 1+2, drop 1+2+3, drop all four. Score each against votes7 (156 matched, F2 0.702). Done 24 Oct 23:52 CEST. Files: `out/rear-lamp-swing-K-drop1.json`, `drop12`, `drop123`, `drop1234`, logs, `out/experiments/K-sweep.json`.
      Found: drop1 407 / 158 / 0.677 (deleted 56, of which 3 matched and 53 unmatched). drop12 395 / 156 / 0.675 (deleted 68: 5 matched, 63 unmatched). drop123 299 / 124 / 0.585 (deleted 164: 42 matched, 122 unmatched). drop1234 281 / 113 / 0.543 (deleted 182: 54 matched, 128 unmatched). None beats 0.702. Spend $0. Commit: `e26a710`.
- [x] K3 The matches votes4 has and votes7 lacks: which class would delete them. Done 24 Oct 23:53 CEST. File: `out/experiments/K-extras.json`.
      Found: 5 gold rows. No class deletes R-0259 (R150 5.1.4.4.1, the numbered Table 3 row). Class 1 deletes R-0300 (Annex 6 Part 6, the 500-hour exposure). Class 2 deletes R-0430 (R48 6.4.4.3, reversing lamp at the rear). Class 3 deletes R-0453 (optional lamps) and R-0125 (manufacturer logo). A sixth extra submitted row, R-0354 (low mount, class 3), matched a gold row votes7 already matches.
- [x] K4 Say whether a filtered votes4 beats votes7 with those matches still present. Done 24 Oct 23:53 CEST.
      Found: no. drop1 keeps 4 of the 5 extra matches and still scores F2 0.677. The cuts that delete the extra matches also delete votes7 matches, and junk remains. The classes are not the votes4 waste.

Next: none. Lane done. No upload.

## Run log rows

| Run | File | Method | Code | Rows | Local matched / F2 | Platform (upload): matched / F2 | Spend |
|---|---|---|---|---|---|---|---|
| 23:52 | `rear-lamp-swing-K-drop1.json` | votes4, drop class 1 (test procedure) | `big-swings` `k_filter.py sweep` | 407 | 158 / 0.677 | not uploaded | $0 |
| 23:52 | `rear-lamp-swing-K-drop12.json` | votes4, drop classes 1 and 2 | `big-swings` `k_filter.py sweep` | 395 | 156 / 0.675 | not uploaded | $0 |
| 23:52 | `rear-lamp-swing-K-drop123.json` | votes4, drop classes 1, 2 and 3 | `big-swings` `k_filter.py sweep` | 299 | 124 / 0.585 | not uploaded | $0 |
| 23:52 | `rear-lamp-swing-K-drop1234.json` | votes4, drop all four classes | `big-swings` `k_filter.py sweep` | 281 | 113 / 0.543 | not uploaded | $0 |

## Uploads

None. The owner closed the platform queue at 23:36. This lane does not nominate a file.

| File | Question | Predicted matched / F2 | Uploaded at | Platform matched / F2 |
|---|---|---|---|---|

## Notes

Tagging is lexical, in `brain/swing/k_filter.py`. It does not open the gold file. `sweep` and `extras` open the gold only to score a cut that is already fixed.

Votes4 has 463 rows. Exact `(regulation, paragraph, text)` overlap with votes7 is 351, so the extra set is 112 rows. Tag counts on all 463 rows, then on those 112:

| Set | Rows | Class 1 | Class 2 | Class 3 | Class 4 | Any class | Ambiguous | Neither |
|---|---|---|---|---|---|---|---|---|
| votes4 | 463 | 56 | 12 | 100 | 22 | 182 | 25 | 258 |
| extra, not in votes7 | 112 | 29 | 2 | 32 | 7 | 63 | 7 | 43 |

A row can carry more than one class, so the class columns are not a partition. 43 of the 112 extra rows match no class and are not ambiguous. They stay in every cut.

Ambiguous rows are not dropped. On the extra set they are: the ESA "shall be tested" for emissions with no procedure step (R-0012), both "the test method shall limit / ensure" sentences (R-0045, R-0046), the triangular retro-reflector "shall be red" (R-0322, colour is in lane C's list and not in the shared brief), and the closed-circuit tell-tale presence line (R-0411). The other ambiguous notes are on rows votes7 already keeps. Full text is in `K-tags.json`.

Two definition bugs fixed before any score, from the wording alone:

- "After the water immersion test, no water shall penetrate" was tagged as the immersion procedure. It is the pass criterion. The pass pattern now includes "no water shall" and "shall not penetrate".
- "non-replaceable" matched the replaceable-source rule, because the hyphen is a word boundary. The rule now rejects `non-replaceable`. Lane C's replaceable-source case ("with the exception of lamps with non-replaceable light sources") is still class 3. A sentence whose only light source is non-replaceable is not.
- A bare "according to Regulation No. 37" or "as specified in paragraph 3.2.10" was tagged as a pointer when the demand was to state an approval number or to refuse approval. A pointer now has to be the obligation: conform, comply, fulfil, meet the requirements of a paragraph, a table with no value of its own, type-approved according to, or deemed to comply.

Shared-definition note, not edited in lane J: class 2 in the shared brief keeps widths, heights and angles, and does not mention colour. Lane C's hand read dropped colour and one retro-reflector height. This lane does not drop colour, and it does not drop a height or angle that carries a number. It does drop "the height shall be measured from the highest point" as class 1, because that sentence has no height.

43 extra rows are untagged. Many are real limits (pulse voltages, candela tables, visibility angles) or installation sentences that are longer than a one-liner (median plane, 150 mm / 850 mm window height, "no special requirement"). A model call would only relabel the ambiguous and untagged rows. This run stops before that call.

## Official local scores

24 Oct 23:52 CEST. `uv run python ../tools/validate.py` from `brain/` (system Python has no jsonschema). `tools/score_local.py` for regulation and page F1. `uv run python -m eval.score` for requirement matched and F2, and for page F2. Votes7 baseline, from lane A: 351 rows, 156 matched, F2 0.702.

| File | Validate | Regulation P / R / F1 | Page P / R / F1 (cited / expected / matched) | Page F2 | Requirement matched / F2 |
|---|---|---|---|---|---|
| drop1 | OK, 407 | 1.000 / 1.000 / 1.000 (4/4/4) | 0.778 / 0.925 / 0.845 (63/53/49) | 0.891 | 158 / 0.677 |
| drop12 | OK, 395 | 1.000 / 1.000 / 1.000 (4/4/4) | 0.778 / 0.925 / 0.845 (63/53/49) | 0.891 | 156 / 0.675 |
| drop123 | OK, 299 | 1.000 / 1.000 / 1.000 (4/4/4) | 0.778 / 0.925 / 0.845 (63/53/49) | 0.891 | 124 / 0.585 |
| drop1234 | OK, 281 | 1.000 / 1.000 / 1.000 (4/4/4) | 0.767 / 0.868 / 0.814 (60/53/46) | 0.846 | 113 / 0.543 |

Deleted rows are counted against the original votes4 assignment (161 matched). The new file's matched count fell by the same number, so no remaining row picked up a gold row the deleted row had held.

Why F2 is not 1.0, from `eval.errors`. Lift is the F2 change. "Drop outside" is the oracle that removes rows on paragraphs the experts never cite. "Recover cited" adds the missed gold rows on paragraphs the file already cites and does not add rows. "Cite skipped" adds one matching row per gold row on a paragraph the file never cites.

| File | F2 | Drop outside | Recover cited | Cite skipped | Largest |
|---|---|---|---|---|---|
| drop1 | 0.677 | +0.117 to 0.794 | +0.094 to 0.771 | +0.037 to 0.714 | rows outside gold paragraphs (172 of them) |
| drop12 | 0.675 | +0.112 to 0.787 | +0.100 to 0.775 | +0.041 to 0.716 | rows outside gold paragraphs (164) |
| drop123 | 0.585 | +0.064 to 0.649 | +0.118 to 0.703 | +0.165 to 0.750 | gold paragraphs never cited (41 gold rows) |
| drop1234 | 0.543 | +0.057 to 0.600 | +0.154 to 0.696 | +0.185 to 0.727 | gold paragraphs never cited (45 gold rows) |

drop123 and drop1234 miss paragraphs because class 3 and class 4 deleted rows that were the file's only citation. On drop1 and drop12 the gap is still the outside rows.

## Report

**Answer.** The four classes are not the votes4 waste. Dropping test-procedure rows, the only cut that helps, leaves 407 rows, 158 matched, F2 0.677, two matches above votes7 and 0.025 F2 below it. Adding the variant class then deletes matches: 42 of the 164 deleted rows were matched, and F2 falls to 0.585.

**Table.** Votes7 is 351 rows, 156 matched, F2 0.702. Votes4 is 463, 161, 0.658. The 112 extra rows are 73 on paragraphs the experts never cite and 39 on paragraphs they do. Of those 73, the rules tag 50 (class 1: 27, class 2: 0, class 3: 24, class 4: 5) and leave 20 with no class and no ambiguous flag.

| Cut | Rows | Matched | F2 | Against votes7 | Deleted matched / unmatched |
|---|---|---|---|---|---|
| drop class 1 | 407 | 158 | 0.677 | +2 matched, F2 0.677 vs 0.702 | 3 / 53 |
| drop 1+2 | 395 | 156 | 0.675 | same matches, 44 more rows | 5 / 63 |
| drop 1+2+3 | 299 | 124 | 0.585 | 32 matches gone | 42 / 122 |
| drop all four | 281 | 113 | 0.543 | 43 matches gone | 54 / 128 |

The five gold rows votes4 matches and votes7 does not, and the class that deletes the submitted row:

| Submitted | Where | Class | Deleted from |
|---|---|---|---|
| R-0259 | UN R150 5.1.4.4.1, Table 3 values in the row | none | no cut |
| R-0300 | UN R150 Annex 6 Part 6, 500-hour exposure | 1 and 4 | every cut |
| R-0430 | UN R48 6.4.4.3, reversing lamp at the rear | 2 | drop12 onward |
| R-0453 | UN R48 6.7.4.2.1, optional lamps | 3 | drop123 onward |
| R-0125 | UN R148 4.5.5, manufacturer logo | 3 | drop123 onward |

drop1 still holds 4 of those 5 and does not clear 0.702. That is not a win. drop123 deletes four of the five and still has 112 rows outside gold paragraphs. That is the loss the brief described: the classes are not the votes4 waste. Class 2 catches none of the 73 outside-gold extra rows. Both of its extra hits sit on gold paragraphs, and one of them is an extra match.

**Nominated upload.** None. No file beats 0.702, and the owner closed the platform queue at 23:36.

**Transfer check.** Not run. The filter is text rules on a lamp vote file. It was not applied to the bumper labels or the synthetic retro-reflector.

**Sunday.** Not a method. It needs no model call and runs in seconds, and it does not beat the 7-vote file. Lowering the vote to 4 and then deleting these classes spends the five extra matches, or keeps them and keeps too many rows. Spend $0.
