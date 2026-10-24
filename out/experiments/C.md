# Lane C: maximum precision, only rows we are surest of

State: waiting for upload (all four steps done, report written). Updated: 24 Oct 22:45 CEST.
Approved spend: $0. Spent: $0.

## Checklist

- [x] C1 Build three small files (120 to 180 rows): votes of 10 or more, relevance confidence 0.6
      or more in the Fable or kb-jev file, and rows that pass both. Done 22:42. Files:
      `out/experiments/C-pool.json`, `out/experiments/C-buckets.json`,
      `out/rear-lamp-swing-C-{votes10,votes12,votes13,kbjev-top150,both-v6-c05}.json` and `.log`,
      `brain/swing/c_precision.py`. Commit: see `git log -- out/experiments/C.md`.
      Found: votes of 10 or more is 217 rows (over the range), so the vote file is cut at 12
      (149 rows). Confidence 0.6 or more is only 97 rows, so the confidence file is kb-jev's top
      150 by confidence. Best in range: votes 12, 99 matched of 149 locally, P 0.664.
- [x] C2 Local matched for each, unmatched rows sorted into three kinds. Done 22:42. Found: in
      every vote file 90% or more of the misses sit on paragraphs the experts never cite; the
      confidence file instead loses a third of its misses to excess rows in cited paragraphs.
      Wording-only misses are 1 to 7 rows in every file.
- [x] C3 Nominate one file. Done 22:44. `out/rear-lamp-swing-C-votes12.json`, 149 rows,
      predicted platform 101 matched, P 0.68, F2 0.556.
- [x] C4 Read the misses of the top bucket by hand, five most common reasons. Done 22:45. List
      in the report; it goes to lanes E and F.

Next: wait for the owner's upload of `out/rear-lamp-swing-C-votes12.json`; the master writes the
platform numbers into the Uploads table. Nothing else in this lane depends on it.

## Run log rows

All 24 Oct, CEST, branch `big-swings`, code `brain/swing/c_precision.py` (commit of this file).
No model calls. Method for every row: 13-run vote pool (finding 2's 13 files), leader clustering
per (regulation, paragraph) at judge similarity 0.6, at most one row per run per cluster;
representative text is the Fable row, else kb-jev, else the next run by platform matched.

| Run | File | Method | Code | Rows | Local matched / F2 | Platform (upload): matched / F2 | Spend |
|---|---|---|---|---|---|---|---|
| 22:42 | `rear-lamp-swing-C-votes13.json` | clusters written by all 13 runs | `big-swings`, `swing/c_precision.py` | 105 | 71 / 0.410 | not uploaded | $0 |
| 22:42 | `rear-lamp-swing-C-votes12.json` | clusters written by 12 or 13 runs | `big-swings`, `swing/c_precision.py` | 149 | 99 / 0.545 | nominated | $0 |
| 22:42 | `rear-lamp-swing-C-votes10.json` | clusters written by 10 or more runs | `big-swings`, `swing/c_precision.py` | 217 | 118 / 0.604 | not uploaded | $0 |
| 22:42 | `rear-lamp-swing-C-kbjev-top150.json` | kb-jev's 150 rows with the highest relevance confidence (0.505 or more) | `big-swings`, `swing/c_precision.py` | 150 | 82 / 0.451 | not uploaded | $0 |
| 22:42 | `rear-lamp-swing-C-both-v6-c05.json` | clusters with 6 or more votes and Fable or kb-jev confidence 0.5 or more | `big-swings`, `swing/c_precision.py` | 120 | 78 / 0.443 | not uploaded | $0 |

## Uploads

| File | Question | Predicted matched / F2 | Uploaded at | Platform matched / F2 |
|---|---|---|---|---|
| `out/rear-lamp-swing-C-votes12.json` (149 rows) | What precision does the platform give the rows 12 or 13 of 13 runs agree on? Local says 0.66, with almost every miss on a paragraph the experts skip. | 101 / 0.556 (P 0.68; anything from 96 to 106 is within the platform's noise) | | |

## Notes

- Commands, from `brain/`, all free:
  `BRAIN_LLM= PYTHONPATH=. uv run python swing/c_precision.py pool` (writes `C-pool.json`),
  `... build votes12` (prints every variant, writes the named ones), `... misses <file>`
  (unmatched rows with the gold rows of the same paragraph), `... transfer` (bumper check).
- Lane A's pool (`A-pool.json`, Jaccard 0.5, average linkage) arrived after C1. Cross-check with
  its `votes_13`: 12 or more votes is 169 rows, 108 matched, P 0.639, misses 55 not cited,
  1 excess, 5 wording; 13 votes is 119 rows, 78 matched, P 0.655. Same picture as C's own pool.
- `conf06` (the literal "confidence 0.6 or more" file, kb-jev plus Fable) has 97 rows, 52 matched,
  P 0.536. The kb-jev confidence is a paragraph score, so it picks gold paragraphs well (81% of
  the top 150 rows are in gold paragraphs) but cannot tell one row of a paragraph from another:
  34 of its 68 misses are surplus rows in cited paragraphs.
- Grid of votes times kb-jev confidence (scratch, not saved): the best precision near 100 rows is
  12 votes and confidence 0.45 (95 rows, 72 matched, P 0.758); near 150 rows nothing beats
  votes 12 alone. The local precision ceiling is about 0.75 at 100 rows and 0.66 at 150.

## Report

**Answer.** The 149 rows that 12 or 13 of 13 runs agree on match 66% locally (predicted 68% on
the platform), and 46 of their 50 misses are correct, well-written requirements on paragraphs the
experts did not cite; wording accounts for 3 misses and over-splitting for 1. So the precision
ceiling is the experts' paragraph choice, not wording or granularity: the misses are systematic
omissions (test-procedure steps, orientation and count one-liners, optional variants) that a
selector can learn, while rewording the rows would recover at most 3.

**Table** (local judge, 190 gold rows; unmatched rows split into paragraph not cited by the
experts / surplus rows on a cited paragraph / wording only):

| File | Rows | Matched | P | F2 | Not cited | Surplus | Wording |
|---|---|---|---|---|---|---|---|
| votes 13 | 105 | 71 | 0.676 | 0.410 | 32 | 0 | 2 |
| votes 12 | 149 | 99 | 0.664 | 0.545 | 46 | 1 | 3 |
| votes 11 | 181 | 110 | 0.608 | 0.584 | 58 | 8 | 5 |
| votes 10 | 217 | 118 | 0.544 | 0.604 | 82 | 12 | 5 |
| kb-jev top 150 by confidence | 150 | 82 | 0.547 | 0.451 | 27 | 34 | 7 |
| kb-jev and Fable confidence 0.6 or more | 97 | 52 | 0.536 | 0.303 | 14 | 26 | 5 |
| votes 6 and confidence 0.5 or more | 120 | 78 | 0.650 | 0.443 | 21 | 18 | 3 |
| votes 12 and kb-jev confidence 0.45 or more | 95 | 72 | 0.758 | 0.421 | 21 | 1 | 1 |

Votes fix granularity (surplus rows fall to 0 or 1 at 12 votes); confidence fixes paragraph
choice (fewer rows off gold paragraphs) but not granularity. Even both together stop at about
0.75.

**Why the experts would not list the top bucket's misses** (all 50 misses of votes 12, read by
hand; the first four are paragraph choice):

1. **Test procedure, not a requirement on the product** (14 rows). Sample allocation into test
   groups (R150 5.1.3.1, six rows), how to immerse, salt-spray or wipe the sample (R150 Annex 6
   Part 2 1.1, Part 4 2, Annex 7 Part 1 1.1), how to measure (R150 5.1.4.2, 5.1.5.1, R10 Annex 10
   3, R148 4.8.2.1). The experts keep the pass criterion of the same test (Annex 6 Part 4 1, 3,
   4.1) and drop the steps.
2. **Vehicle installation one-liners for orientation, count, presence and position in length**
   (12 rows, all R48). "Shall be oriented rearwards" (6.4.6.1, 6.7.6, 6.10.6, 6.14.6), "two in
   number" (6.10.2, 5.16.1), "shall be present" (6.14.1), "at the rear of the vehicle" (6.7.4.4,
   6.14.4.3), the colour list (5.15, two rows), and the retro-reflector's height (6.14.4.2). The
   experts cite most sibling paragraphs with numbers (width, geometric visibility) and skip these.
3. **Conditional on a variant the spec does not have** (13 rows). LED substitute light sources
   and replaceable sources (R148 3.3.3.3), control gear outside the lamp body (3.3.3.6), a
   position lamp reciprocally incorporated with the stop lamp (4.8.3.5, two rows), Class IA/IB
   "TOP" marking and mounting below 750 mm (R150 3.3.4.2, 5.1.4.5), temporary fail-safe
   replacement and its tell-tale (R48 5.24, two rows), special power supply voltages (5.27.1,
   5.27.2), parts of the lamp hidden by the body (5.28.3), one approval mark on grouped lamps
   (R150 3.3.6.1.2).
4. **Pointer rows that only refer to a table or to other sections** (7 rows). "Shall provide the
   minimum luminous intensity ... as specified in Table 4" (R148 5.2.2, 5.5.2), "shall conform to
   paragraphs 4. and 5." (R148 4.1), "shall comply with sections 5. and 6. of Regulations 48, 53,
   74 or 86" (R150 4), the visibility checks that only verify 5.10.1 (R48 5.10.4.1, 5.10.4.2),
   the reversing lamp's visibility angles (R48 6.4.5.1, which the experts do not cite at all).
5. **Right paragraph, but the wording dropped or changed the subject or condition** (4 rows: the
   local judge's 3 wording misses and its 1 surplus row). "The sequential number" without
   "four to six-digit ... part of the approval number" (R148 3.3.2.2); "no water shall
   penetrate" where the expert wrote "shall prevent water from penetrating" (R150 Annex 6 Part 2
   1.2, zeroed by the negation rule); the reversing-lamp-only row where the expert merged
   reversing and manoeuvring lamps (R148 Annex 8 1.2.1); a second row on R150 5.1.3.2.2 next to
   the matched one. The platform probably matches the first three, hence the prediction of 101.

For lane F (row selector): reasons 1 to 4 are features a row-level model can see from the text
alone (test-procedure verbs and "sample", "oriented"/"in number"/"shall be present", an "If"/
"Where" condition naming a feature absent from the spec, "as specified in Table"/"paragraphs X
and Y"). For lane E (verbatim rows): only reason 5 is about wording, and it is 4 rows of 149.

**Nominated upload.** `out/rear-lamp-swing-C-votes12.json`, 149 rows. Predicted platform 101
matched, P 0.68, F2 0.556 (5 x 101 / (760 + 149)). It cannot raise the leaderboard score; it
measures the platform's precision on agreed rows. If the platform gives P 0.75 or more, the local
judge is underrating agreed rows and lane A's thresholds should move lower. Platform numbers: not
uploaded yet.

**Transfer check.** Votes cannot be checked on the bumper yet: there is one LLM bumper run
(`brain/out/bumper-plain-llm.json`, 105 rows), so no pool to vote over (lane G builds one). The
confidence half transfers as far as the silver labels can tell: the top third of that run by
relevance confidence (0.28 to 0.64) is 35 of 35 rows on silver-cited paragraphs, the middle third
24 of 35, the bottom third 13 of 35. This is optimistic, since the silver labels and the
relevance score both come from Opus. Agreement with the no-LLM bumper run
(`bumper-plain.json`) does not predict a cited paragraph (36 of 55 versus 36 of 50). The
synthetic retro-reflector case has no pool of runs, so it was not checked.

**Sunday.** Nothing in this lane is a method to submit on Sunday: a 150-row file gives up about
60 matches for a precision gain worth far less (F2 0.545 locally against 0.60 to 0.68 for the
full files). What carries over is the miss list above: reasons 1 to 4 are rules or features a
selector can apply to a bumper run at no cost and in seconds, and the vote filter needs k runs
(lane A and G give its cost).
