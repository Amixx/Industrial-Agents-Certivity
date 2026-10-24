# Lane K: the four classes on the 4-vote file

State: running. Updated: 24 Oct 23:48 CEST.
Approved spend: $0 for this run. The ledger at 23:33 allows a planned $1. This run does not use it. Spent: $0.

## Checklist

- [x] K1 Tag `out/rear-lamp-swing-A-votes4.json`. The 112 rows votes7 does not contain are flagged `in_votes7: false`. Done 24 Oct 23:48 CEST. Files: `brain/swing/k_filter.py`, `out/experiments/K-tags.json`.
      Found: 463 rows, classes 1 / 2 / 3 / 4 on 56 / 12 / 100 / 22 rows. Of the 112 extra rows, 63 carry a class, 7 are ambiguous, 43 are neither. Ambiguous rows are not dropped. No model call.
- [ ] K2 Sweep drop 1, drop 1+2, drop 1+2+3, drop all four. Score each against votes7 (156 matched, F2 0.702).
- [ ] K3 The matches votes4 has and votes7 lacks: which class would delete them.
- [ ] K4 Say whether a filtered votes4 beats votes7 with those matches still present.

Next: `BRAIN_LLM= PYTHONPATH=. uv run python swing/k_filter.py sweep` from `brain/`, then `tools/validate.py`, `tools/score_local.py`, and `uv run python -m eval.score`.

## Run log rows

| Run | File | Method | Code | Rows | Local matched / F2 | Platform (upload): matched / F2 | Spend |
|---|---|---|---|---|---|---|---|

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

## Report

Filled in when the sweep is scored.
