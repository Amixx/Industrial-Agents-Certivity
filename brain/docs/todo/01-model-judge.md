# 01 Calibrate a model judge against the platform

## Prompt

You are joining a hackathon team mid-event (Certivity challenge, Munich). Read
`brain/docs/todo/README.md` first: it has the event, the scores, the rules and the tools. Work
from `brain/`.

**Why this task exists.** Every other task needs to compare variants that differ by a few
matched requirements, and the only exact judge is the platform, which allows 5 uploads per
hour. The local lexical judge (`eval/judge.py`: token overlap, one-to-one within a regulation)
is too coarse: against the platform it is off by -5 to +9 matches. A model judge
(`eval/model_judge.py`, through `claude -p` on the subscription, cached) exists but has never
been checked against the platform.

**Ground truth you have.** Six dev files scored by the platform, with the number of gold
requirements each matched (recall times 190):

| File | Rows | Platform matches | Local lexical judge |
|---|---|---|---|
| `../out/rear-lamp-deterministic.json` | 778 | 107 | 112 |
| `../out/rear-lamp-sonnet.json` | 344 | 140 | 131 |
| `../out/rear-lamp-opus.json` | 338 | 143 | 139 |
| `out/dev-upload.json` | 407 | 145 | 138 |
| `../out/rear-lamp-fable.json` | 332 | 149 | 141 |
| `../out/rear-lamp-qwen-split-rewrite.json` | 446 | 133 | 137 |

The lexical judge's error changes sign with the writing style: it undercounts the Claude and
gpt rewrites and overcounts verbatim text and qwen's short split rows. A good model judge has
to be right across styles, because task 02 compares exactly that. Hold one file out as a
check; do not tune on all of them. Later dev uploads are added to `../out/README.md`.

**What to do.**
1. Read `eval/model_judge.py`, `eval/judge.py` and the platform's rule in
   `../docs/CHALLENGE.md` ("same scope, condition and constraint").
2. Run the model judge on the six files as it is. Report matches per file next to the
   platform. The calls go through `claude -p` on the logged-in subscription; confirm that this
   costs nothing extra before running, and estimate the number of calls first.
3. Find where it disagrees. Typical causes to check:
   - the candidate set: only the top 4 by lexical similarity plus same-paragraph rows are
     judged, so a true match outside them is never seen;
   - strictness: does it accept a split row that states one of two constraints of a gold row,
     a merged row that states both, or a row whose subject is "the lamp" where gold says "the
     stop lamp"?
   - the one-to-one assignment.
4. Change one thing at a time (candidate set, prompt, model) and rerun. Verdicts are cached,
   so only new pairs cost calls.
5. Keep the lexical judge as it is: it is the free fallback.

**Acceptance.**
- Within ±3 matches of the platform on every file, including the held-out one, and the same
  order as the platform.
- A rerun on an unchanged file is free (cached) and takes under a minute.
- `uv run python -m eval.model_judge <file>` documented in `README.md` ("Evaluate"), with the
  calibration table.

**Deliverables.** The calibration table and every configuration you tried under "Results"
below; the code change; one line in `brain/docs/todo/README.md` saying the judge is ready and
how far to trust it.

**Do not.** Edit files other tasks own (see the README table). Upload to the platform yourself
without agreeing it with the team: uploads are shared, 5 per hour.

## Results

Done on 24 Oct. `uv run python -m eval.model_judge <files>` prints the lexical judge, the model
judge and the platform estimate (model matches plus 4) side by side.

**How it judges.** Sonnet 5.5 through `claude -p`. Candidates per gold row: same regulation, the
8 most similar rows by token overlap, plus rows citing the same paragraph, its parent or a child.
Every pair is graded 0 to 4 on its own, in shuffled batches of 40 that mix gold rows; pairs
graded 3 or 4 are matched one to one.

**Calibration** on the 16 dev uploads with a platform score (matches; error is estimate minus
platform):

| File | Rows | Platform | Lexical | Model | Estimate | Error |
|---|---|---|---|---|---|---|
| `out/dev-upload.json` | 407 | 145 | 138 | 138 | 142 | −3 |
| `rear-lamp-sonnet.json` | 344 | 140 | 131 | 129 | 133 | −7 |
| `rear-lamp-opus.json` | 338 | 143 | 139 | 130 | 134 | −9 |
| `rear-lamp-fable.json` | 332 | 149 and 142 | 141 | 137 | 141 | −4.5 |
| `rear-lamp-deterministic.json` | 778 | 107 | 112 | 106 | 110 | +3 |
| `rear-lamp-main-cli.json` | 368 | 143 | 145 | 137 | 141 | −2 |
| `rear-lamp-kb-deterministic.json` | 864 | 108 | 113 | 111 | 115 | +7 |
| `rear-lamp-kb-jev.json` | 389 | 154 | 153 | 150 | 154 | 0 |
| `rear-lamp-kb-jev-filter-v4.json` | 342 | 140 | 158 | 142 | 146 | +6 |
| `rear-lamp-kb-sol-rewrite.json` | 420 | 143 | 150 | 141 | 145 | +2 |
| `rear-lamp-qwen-split-rewrite.json` | 446 | 133 | 137 | 135 | 139 | +6 |
| `rear-lamp-mix-examples-cut.json` | 341 | 138 | 145 | 137 | 141 | +3 |
| `rear-lamp-kb-v5-rewrite.json` | 363 | 148 | 158 | 151 | 155 | +7 |
| `rear-lamp-deterministic-sibling.json` | 647 | 106 | 111 | 104 | 108 | +2 |
| `upload/agent-v3.json` | 302 | 116 | 108 | 102 | 106 | −10 |
| `upload/recall-push-filter.json` | 390 | 150 | 156 | 150 | 154 | +4 |

- Mean absolute error 4.7 matches, Spearman 0.84. The lexical judge is off by up to 18 (v4).
- The acceptance bar (±3 on every file) is not met. The platform scored the same Fable file 149
  and 142, so one upload carries noise of that size: treat differences under about 8 matches as
  a tie, from either judge.

**Out of sample (after calibration).** `rear-lamp-kb-own-subject.json` changes only the rewrite
prompt against `recall-push-filter.json`. The model judge counted 163 against 150 (estimate
+16 over the platform); the platform counted 151 against 150. Both judges overrate this kind of
wording change, so do not use either to choose between rewrite prompts; use an upload. The
platform's matched count barely moves with the writing style (143 to 154 across every Opus,
Fable, Sonnet and Sol rewrite of the same paragraphs).

**Configurations tried:**

| Configuration | Result |
|---|---|
| Old `model_judge.py` (booleans, top 4 candidates) | crashed on batch length, never finished |
| One call per gold row grading all its candidates from 15 files at once, 3–4 match | MAE 3.6, Spearman 0.83 |
| The same plus a one-by-one check of pairs graded 2 | MAE 2.5 after a −4 offset, Spearman 0.96 on 15 files; but predicted 163 for `recall-push-filter.json`, platform 150 |
| **Every pair graded on its own, shuffled batches, 3–4 match** | **MAE 4.7, Spearman 0.84 on 16 files** |

Grading all candidates of a gold row in one call makes the grade depend on the other rows in the
call: a new file, graded with only its own few candidates, got twice as many 2s and more 3s
than the calibration files, so the 0.96 version overcounted every new file. Grading each pair
alone removes that dependence at the cost of more noise.

**Cost.** About 210 calls to grade the 8,400 non-trivial calibration pairs. A new 390-row file
needs about 40 calls; a cached rerun takes seconds. Grades are cached per pair in
`data/cache/model_judge/`, so scoring a subset of a judged file's rows costs nothing.
