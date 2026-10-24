# Lane J: Delete the expert-skip classes from the 7-vote file

State: running. Updated: 24 Oct 23:53 CEST.
Approved spend: $1 (STATUS-08 at 23:33). Spent: $0. No model call.

## Checklist

- [x] J1 Tag every row of `out/rear-lamp-swing-A-votes7.json` with the four classes.
      Done 24 Oct 23:53 CEST. Files: `out/experiments/J-tags.json`, `brain/swing/j_classes.py`.
      Found: 351 rows. Definite hits: class 1 is 63, class 2 is 17, class 3 is 43, class 4 is 24,
      139 rows in at least one class. 40 rows are ambiguous and are not dropped. Spend $0.
- [ ] J2 Sweep: drop class 1, drop 1+2, drop 1+2+3, drop all four. For each file write rows,
      matched, F2, and how many deleted rows were matched versus unmatched.
- [ ] J3 Read 15 deleted rows and 10 kept rows that the judge did not match. The winning cut is
      the best F2 that still matches at least 151.
- [ ] J4 Report whether this is a Sunday rule (text only, no vote required) or whether it only
      works on rows a vote already kept.

Next: `cd brain && BRAIN_LLM= PYTHONPATH=. uv run python swing/j_classes.py sweep`

## Run log rows

| Run | File | Method | Code | Rows | Local matched / F2 | Platform (upload): matched / F2 | Spend |
|---|---|---|---|---|---|---|---|
| 24 Oct 23:53 | `out/experiments/J-tags.json` | text rules for the four classes, no model | `brain/swing/j_classes.py` | 351 tagged | not a submission | not nominated | $0 |

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

## Report

Not filled in yet.
