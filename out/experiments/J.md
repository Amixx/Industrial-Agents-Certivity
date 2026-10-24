# Lane J: Delete the expert-skip classes from the 7-vote file

State: running. Updated: 24 Oct 23:58 CEST.
Approved spend: $1 (STATUS-08 at 23:33). Spent: $0. No model call.

## Checklist

- [x] J1 Tag every row of `out/rear-lamp-swing-A-votes7.json` with the four classes.
      Done 24 Oct 23:53 CEST. Files: `out/experiments/J-tags.json`, `brain/swing/j_classes.py`.
      Found: 351 rows. Definite hits: class 1 is 63, class 2 is 17, class 3 is 43, class 4 is 24,
      139 rows in at least one class. 40 rows are ambiguous and are not dropped. Spend $0.
- [x] J2 Sweep: drop class 1, drop 1+2, drop 1+2+3, drop all four.
      Done 24 Oct 23:55 CEST. Files: `out/experiments/J-sweep.json`,
      `out/rear-lamp-swing-J-drop1.json`, `drop12`, `drop123`, `drop1234`, each with a `.log`.
      Found: baseline 351 / 156 / 0.702, 151 outside gold paragraphs. The four classes catch 86
      of those 151 and destroy 43 of the 156 matches. Every cut matches fewer than 151 and
      every F2 is below 0.702. No winning cut. Spend $0.
- [x] J3 Read 15 deleted rows and 10 kept rows that the judge did not match.
      Done 24 Oct 23:58 CEST. File: `out/experiments/J-read.json`. There is no winning cut:
      none of the four still matches 151. The read uses drop 1+2, the highest F2 in the sweep
      (271 rows, 142 matched, 0.689), and it is not adopted. Spend $0.
- [ ] J4 Report whether this is a Sunday rule (text only, no vote required) or whether it only
      works on rows a vote already kept.

Next: write the single-run comparison and close the report. The Sunday scores are already on disk.

## Run log rows

| Run | File | Method | Code | Rows | Local matched / F2 | Platform (upload): matched / F2 | Spend |
|---|---|---|---|---|---|---|---|
| 24 Oct 23:53 | `out/experiments/J-tags.json` | text rules for the four classes, no model | `brain/swing/j_classes.py` | 351 tagged | not a submission | not nominated | $0 |
| 24 Oct 23:55 | `out/rear-lamp-swing-J-drop1.json` | votes7, drop class 1 | `a5413b6` | 288 | 144 / 0.687 | not nominated | $0 |
| 24 Oct 23:55 | `out/rear-lamp-swing-J-drop12.json` | votes7, drop classes 1+2 | `a5413b6` | 271 | 142 / 0.689 | not nominated | $0 |
| 24 Oct 23:55 | `out/rear-lamp-swing-J-drop123.json` | votes7, drop classes 1+2+3 | `a5413b6` | 232 | 124 / 0.625 | not nominated | $0 |
| 24 Oct 23:55 | `out/rear-lamp-swing-J-drop1234.json` | votes7, drop classes 1+2+3+4 | `a5413b6` | 212 | 114 / 0.586 | not nominated | $0 |

## Uploads

| File | Question | Predicted matched / F2 | Uploaded at | Platform matched / F2 |
|---|---|---|---|---|
| none | The owner closed the queue at 23:36. This lane does not nominate. | | | |

## Notes

The tags use the submitted text only. Gold is not an input. A row is dropped later only when a
definite class is in the cut. Ambiguous rows stay in every file.

Definite rules, in short:

1. Test procedure: prepare, immerse, spray, wipe, or measure a sample (allocate samples, salt
   mist, cotton cloth, "shall be measured by the method", test voltage, rotate the sample). A
   pass criterion stays: "no water shall penetrate", "shall not show", "shall not exceed",
   "limits shall be", "no cracking".
2. Installation one-liner: orientation ("oriented rearwards" or "towards the rear"), count
   ("in number", "two devices and one"), bare presence ("shall be mandatory" or "shall be
   present", not a tell-tale), or "at the rear" as the position in length. A row that also
   states a width, height, angle, or other value is not dropped.
3. The sentence exists to cover equipment it introduces as optional or absent: LED substitute,
   replaceable light source or module, control gear outside the body, oscillator or switches
   the sentence says are missing, fail-safe, optional lamps, optional side-marker, REESS,
   traction battery, TOP only if necessary, marking material or plates, the low-mount sentence
   on its own, a special power supply, a Regulation 37 source, an optional tell-tale.
4. The only demand is a table or "conform to paragraphs / sections", and the row states no
   value of its own. A pass result after the test stays ("After undergoing the tests").

Colour one-liners ("shall be red", "shall be white") are not tagged. Lane C grouped them with
installation one-liners. The shared brief names orientation, count, presence, and "at the rear".

Ambiguous, listed in `J-tags.json`, not dropped (40 rows):

- Class 1, 10 rows: the obligation to undergo emission tests, a 20 dB correction, an RI check
  that states its angles, a 200 mm aperture, a 100 cm2 area, how installed height is measured
  (2), a shift of the observation direction, "resistance shall be checked", and conditions
  "based on ISO 11452-1".
- Class 2, 1 row: "one device mandatory" together with a length of 6,000 mm.
- Class 3, 23 rows: reciprocally incorporated (11), non-replaceable light source (6), hidden by
  vehicle parts (3), a separable lens, one lens for several devices, a restricted light-source
  category. The product combines functions and uses LED modules, and these sentences do not say
  the equipment is optional or absent.
- Class 4, 6 rows: "to verify paragraphs" that also state 25 m or 0.25 cd (3), and reversing-lamp
  visibility that restates the angles and points at paragraph 2.10.7 (3).

STATUS-08 allows $1 for a model judgement of those 40. This step does not spend it. The sweep
uses the definite tags.

Sweep, local judge, 24 Oct 23:55 CEST. All four files pass `tools/validate.py`. Requirement
matched and F2 are from `eval.score`. Page P/R/F1 are from `score_local.py`.

| Cut | Rows | Matched | F2 | Matched deleted | Unmatched deleted | Page P / R / F1 |
|---|---|---|---|---|---|---|
| votes7 | 351 | 156 | 0.702 | | | |
| drop 1 | 288 | 144 | 0.687 | 12 | 51 | 0.842 / 0.906 / 0.873 |
| drop 1+2 | 271 | 142 | 0.689 | 14 | 66 | 0.842 / 0.906 / 0.873 |
| drop 1+2+3 | 232 | 124 | 0.625 | 33 | 86 | 0.855 / 0.887 / 0.870 |
| drop 1+2+3+4 | 212 | 114 | 0.586 | 43 | 96 | 0.846 / 0.830 / 0.838 |

Of the 151 rows on paragraphs the experts never cite, the four classes catch 86. They destroy
43 of the 156 matches. A row can be in more than one class, so the class rows below add to more
than 86 and 43.

| Class | Outside gold paragraphs | Matched | Unmatched, inside a gold paragraph |
|---|---|---|---|
| 1 test procedure | 46 | 12 | 5 |
| 2 installation one-liner | 14 | 2 | 1 |
| 3 optional or absent equipment | 21 | 19 | 3 |
| 4 pointer | 10 | 13 | 1 |

Break-even is about seven unmatched rows per match. Class 1 deletes about four unmatched rows
per match. Class 3 deletes about one. Class 4 deletes more matches than outside rows. None of
the four cuts still matches 151, so there is no winning cut. The least-bad F2 is drop 1+2 at
0.689, still under 0.702, with 142 matches.

Why F2 is not 1.0 (counterfactual lift, one change at a time). On votes7 the largest lift is
dropping the 151 outside rows (+0.110, to about 0.812). Recovering the 23 gold rows missed on
a cited paragraph is close (+0.104). Citing the gold paragraphs the file skips is smaller
(+0.042). After drop 1, drop 1+2, and drop 1+2+3 the largest remaining lift is recovering gold
rows missed on a cited paragraph, because the cut deleted matches. After all four classes the
largest lift is citing the gold paragraphs the file now skips (+0.187), just ahead of recovering
on-cited misses (+0.170).

## Read of drop 1+2

No cut still matches 151, so nothing is adopted. The 15 deleted rows are from drop 1+2, which has
the highest F2 in the sweep and still loses to the unfiltered file. Fourteen of the fifteen had
been matched. The tenth kept rows are unmatched rows that this cut still holds. Full text is in
`out/experiments/J-read.json`.

The matched deletions are requirements that name a test, a level, or a count.

- "Shall be tested by the method ... for the levels given in Table 1", immunity "tested by the
  method described in Annex 9", and immunity "with the test levels given in Tables 3a and 3b".
  The rule heard "tested by the method" and dropped the sentence that says which test applies.
- The pulses and the starting profile "shall be applied to the supply lines". That is the test
  the judge had matched, not a lab choreography line.
- Test voltage 6.75 V, 13.5 V or 28 V. Measurements from 20 to 6,000 MHz. Colour measured inside
  the distribution grid. CIE Illuminant A at an angle of divergence of 1/3°. These carry values.
- "Shall be rotated ... to the position of minimum RI, which must conform" is a procedure and a
  pass criterion in the same row. Dropping the row drops the pass.
- The saline-mist recipe, 5 parts salt in 95 parts water at 35 °C, was matched. A procedure
  sentence can be the row the judge keeps.
- The two matched count rows are not a bare "two in number". One names Class IA or IB and the
  retro-reflector regulation. The other names two S1 or S2 devices and one S3 or S4 device.
- The unmatched deletion in the fifteen is the clean case: radiation "shall be measured by the
  method described in Annex 7", with no limit of its own.

The ten kept unmatched rows are a mix. Some are outside the four classes and still unmatched:
the 30 to 1,000 MHz limit for ALSE and OATS, the Annex 3 percentage grid, night-time colour
limited to white, red or amber, a lamp on a movable component that must return to position, and
the retro-reflector height of 250 mm to 900 mm (heights stay, and this one did not match).
Others are class 3, so this cut kept them: voltage marking for a secondary operating mode, a
replaceable source that fits only in the correct position, and lamps approved for replaceable
categories 37, 99 or 128. The 25 m visibility check stayed because it states a distance, which
kept it out of class 4. An ESA that is a light source, and must carry an approval number or a
non-interchangeability report, was not called optional equipment.

The definite rules are already enough to see the failure. The 40 ambiguous rows were not dropped,
and the cuts still destroy matches.

## Report

Not filled in yet.
