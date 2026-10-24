# Lane E: Verbatim anchoring

State: done. Updated: 24 Oct 23:08 CEST.
Approved spend: $3. Spent: $1.79 (three Sonnet 5.5 API runs: v1 $0.58, v2 $0.58, v3 $0.63).

No file is nominated. The hour already used 4 of 5 upload slots, so this lane does not wait for platform numbers.

## Checklist

- [x] E1 Candidate sentences of each paragraph of `rear-lamp-fable.json`, from
      `brain.obligations.sentences`, with heading path and parent clause. Done 22:41. Files:
      `out/experiments/E-candidates.json`, `brain/swing/e_verbatim.py`. Commit: `214998a`.
      Found: 208 paragraphs, 509 sentences.
- [x] E2 A model writes each row as segments: `source` (verbatim from the paragraph),
      `context` (verbatim from the parent clause or heading path), `added` (free words, meant to
      be at most eight: subject or glue). The script checks every source/context segment
      against the text (case-insensitive), snaps near-copies, flags the rest. Done 22:45 (v1 and
      v2). Files: `out/rear-lamp-swing-E-v1.json` + `.log`, `out/rear-lamp-swing-E-v2.json` +
      `.log`. Spend $1.16.
      Found: v1 316 rows, 133 matched locally (F2 0.618); v2 (extra rules) 300 rows, 130
      matched (F2 0.613). Fable on the same paragraphs: 332 rows, 141 matched.
- [x] E3 Word share against the source, and row count against Fable's 332. Done 23:08.
      Files: `out/rear-lamp-swing-E-v3.json` + `.log` (run finished 23:03, 208 of 208
      paragraphs). v3 spend $0.63. Distribution below. Gold median word share, computed the
      same way against each gold row's own paragraph: 0.966.
- [x] E4 Every row names its subject and keeps its condition. Read 20 v3 rows by hand at
      23:04 (`e_verbatim.py read`, seed 7). Each of those 20 names a subject and keeps the
      condition that governs it. Two rows elsewhere in the file are still broken (below).
- [x] E5 Nomination withheld at 23:08. The owner said not to nominate: 4 of 5 hourly upload
      slots are used. State is done, not waiting for upload.

Next: nothing further in this lane unless the owner frees an upload slot and asks for one.
The file to send, if that happens, is `out/rear-lamp-swing-E-v3.json`. Do not treat its local
137 as a platform prediction. The lexical judge counts more matches on verbatim rows than the
platform has, and fewer on Claude paraphrases.

## Run log rows

| Run | File | Method | Code | Rows | Local matched / F2 | Platform (upload): matched / F2 | Spend |
|---|---|---|---|---|---|---|---|
| 22:43 | `rear-lamp-swing-E-v1.json` | Fable's 208 paragraphs; Sonnet 5.5 writes rows as verbatim segments plus subject/condition (`PROMPTS["v1"]`) | `big-swings`, `brain/swing/e_verbatim.py` | 316 | 133 / 0.618 | not uploaded | $0.58 |
| 22:45 | `rear-lamp-swing-E-v2.json` | as v1 plus rules for telegraphic labels, demonstratives, in-sentence lists, paragraph-wide conditions, imperatives (`PROMPTS["v2"]`) | `big-swings`, `brain/swing/e_verbatim.py` | 300 | 130 / 0.613 | not uploaded | $0.58 |
| 23:03 | `rear-lamp-swing-E-v3.json` | base prompt plus `EXTRA_V3`: list items rebuilt from raw text, small provisos kept whole, device inserted, qualifiers joined (`PROMPTS["v3"]`) | `big-swings`, `brain/swing/e_verbatim.py` | 311 | 137 / 0.640 | not uploaded | $0.63 |

Fable on the same paragraphs, same local judge: 332 rows, 141 matched, F2 0.646.

## Local metrics

`validate.py` checks the submission format. `score_local.py` is regulation and page F1 only.
`eval.score` requirement F2 is the lane's number. All three files pass validation.

| File | Validate | Regulation P / R / F1 | Page P / R / F1 | Requirement matched / F2 |
|---|---|---|---|---|
| v1, 316 rows | pass | 1.000 / 1.000 / 1.000 (4/4/4) | 0.833 / 0.943 / 0.885 (60/53/50) | 133 / 0.618 |
| v2, 300 rows | pass | 1.000 / 1.000 / 1.000 (4/4/4) | 0.847 / 0.943 / 0.893 (59/53/50) | 130 / 0.613 |
| v3, 311 rows | pass | 1.000 / 1.000 / 1.000 (4/4/4) | 0.833 / 0.943 / 0.885 (60/53/50) | 137 / 0.640 |

Page and regulation scores mostly restate the fixed paragraph selection. v2 cites 59 pages
because it dropped every row of one page. v1 and v3 cite the same 60.

### Word share (E3)

Share is the fraction of the row's words that appear in its source paragraph. The median
fraction of each row that is added words is 0, because most rows add none.

| Variant | Rows | Median share | 1.00 | 0.95-0.99 | 0.90-0.94 | 0.80-0.89 | below 0.80 | Added words (sum / rows / over 8 / max) |
|---|---|---|---|---|---|---|---|---|
| v1 | 316 | 1.000 | 241 | 17 | 17 | 10 | 31 | 398 / 57 / 23 / 14 |
| v2 | 300 | 1.000 | 219 | 23 | 20 | 14 | 24 | 564 / 67 / 36 / 20 |
| v3 | 311 | 1.000 | 229 | 23 | 13 | 16 | 30 | 458 / 85 / 19 / 20 |
| gold | 190 | 0.966 | | | | | | |

Among the 85 v3 rows that add any words, the added words are 0.133 of the row at the median
(mean 0.185). v3 segments: 471 verbatim, 1 snapped, 2 unverified.

## Uploads

| File | Question | Predicted matched / F2 | Uploaded at | Platform matched / F2 |
|---|---|---|---|---|

None. Nomination withheld at 23:08.

## Notes

- `claude -p` returned "Not logged in", so all three runs used the API (Sonnet 5.5 through
  `brain.llm`, cached). A rerun of the same variant reads `brain/data/cache/llm/` at $0.
  v3 answered 208 of 208. Log: `out/rear-lamp-swing-E-v3.log`.
- The local lexical judge is the least trustworthy measure for this style. It zeroes a row
  when a later "not" is missing, and two earlier style changes it liked lost on the platform.
  v3's 137 is the number to record, and it is a poor stand-in for a platform count.
- v3 fixes, checked against the paragraphs v2 lost:
  1. R148 3.3.3.5 is split into "shall bear" rows, each opening with "In case replaceable
     light source module(s) is/are used". v2 had dropped the items.
  2. R48 6.10.7 is "The electrical connections of the rear position lamp shall be in
     accordance with paragraph 5.11", with the however-clause joined. The label colon is gone.
  3. R148 5.2.7 names the device from the heading. Word share falls to 0.375 because the
     heading is the long category line, not the two words "rear position lamp".
  4. R48 5.3 joins the ±3° tolerance with ", and", keeping "shall be allowed". R48 5.9.2
     stays one row, proviso included. R10 Annex 10 2 joins the "not subject to starting
     profile" exemption.
- Still broken, so the eight-word cap is not met in code: R48 6.10.8 reads "a mandatory
  losed-circuit tell-tale" and a second row starts "Rear position lamp however, a tell-tale
  indicating failure is mandatory". 19 rows use more than eight added words (max 20), mostly
  geometric-visibility angles. One of the 20 hand-read rows, R48 6.7.5, keeps the stop lamp
  and the above-2,100 mm exception and also leaves the marker "(b)" in the sentence.
- The 20 hand-read rows (seed 7) and what they name: R48 5.7.2.3 single lamps; R150 3.3.4.1
  retro-reflective devices; R48 6.4.4.3 reversing lamp, with the side-fit exception; R148
  3.3.4.4 the main body, under the shared-lens condition; R148 4.6.1.1 the wired group of
  light sources; R10 6.4.2.2 the vehicle, during the Annex 6 tests (the sentence says "shall"
  twice); R148 4.8.2.1 the lamp, when a control gear is present; R48 5.24 the tell-tale,
  during replacement; R10 Annex 7 2.1 the current, if it can be adjusted; R148 4.2 the
  requirements of the installation regulations; R10 3.2.10 the applicant, when the ESA is a
  light source; R150 5.1.4.1 the applicant, when applying for approval; R148 3.3.3.5 the lamp,
  in case a replaceable module is used; R148 4.8.1.2 the measurements, for a lamp with modules
  or non-replaceable sources; R48 6.7.5 the vertical angle of the stop lamp, with the
  above-2,100 mm exception; R48 6.7.4.1 the offset of an S3 or S4 lamp; R148 4.5.5 the logo,
  on the applicant's request, item (b) of that list; R150 Annex 6 Part 2 1.1 the device, for
  the water immersion; R148 4.8.1.9 the apparent surface, with the category 5 and 6 exception;
  R10 6.6.2.2 the measured value on the ESA.

## Report

A row that keeps the regulation's own sentence and only adds the missing subject and condition does not beat Fable's paraphrase on the local requirement judge: v3 has 137 matches and F2 0.640 on 311 rows, and Fable has 141 matches and F2 0.646 on 332 rows from the same paragraphs. That judge is the least trustworthy one for this style, and no file was uploaded, so the platform half of the question is still open.

| Variant | Rows | Local matched | Local F2 | Median word share |
|---|---|---|---|---|
| v1 verbatim | 316 | 133 | 0.618 | 1.000 |
| v2 verbatim | 300 | 130 | 0.613 | 1.000 |
| v3 verbatim | 311 | 137 | 0.640 | 1.000 |
| Fable paraphrase | 332 | 141 | 0.646 | |

v3 is the verbatim file to keep. It restores the marking list, names the device, and joins the tolerance and the starting-profile exemption. It is 4 local matches behind Fable and 21 rows shorter. Regulation F1 is 1.000 for all three files. Page F1 is 0.885 for v1 and v3, 0.893 for v2.

Nominated uploads: none. Predicted platform matched and F2: not written, because nothing was nominated.

Transfer check: not run. The method holds paragraph selection fixed and then spends one Sonnet pass. On this lamp that pass was 208 paragraphs, 26 calls, about a minute, $0.63. A bumper of about that size fits the Sunday window once the paragraphs are chosen. It was not scored against the silver bumper labels.

Sunday: feasible as a second pass over an already selected paragraph set, at about $0.003 per paragraph on this run's price. It does not choose paragraphs, so it does not replace a selector. Total spent on the lane: $1.79 of the $3 cap.
