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
judge and the platform estimate (model matches minus 4) side by side.

**How it judges.** Sonnet 5.5 through `claude -p`. Candidates per gold row: same regulation, the
8 most similar rows by token overlap, plus rows citing the same paragraph, its parent or a child.
Pass 1 grades all candidates of one gold row in one call, 0 to 4. Pass 2 asks again about every
pair graded 2, one pair at a time in shuffled batches, as yes or no with a lenient prompt
(another name for the same subject, extra numbers from the same paragraph and a dropped
cross-reference still match). A pair matches when graded 3 or 4, or graded 2 and checked yes;
then a one-to-one assignment.

**Calibration** on the 15 dev uploads with a platform score (matches; error is estimate minus
platform):

| File | Rows | Platform | Lexical | Model | Estimate | Error |
|---|---|---|---|---|---|---|
| `out/dev-upload.json` | 407 | 145 | 138 | 150 | 146 | +1 |
| `rear-lamp-sonnet.json` | 344 | 140 | 131 | 137 | 133 | −7 |
| `rear-lamp-opus.json` | 338 | 143 | 139 | 147 | 143 | 0 |
| `rear-lamp-fable.json` | 332 | 149 and 142 | 141 | 149 | 145 | −0.5 |
| `rear-lamp-deterministic.json` | 778 | 107 | 112 | 110 | 106 | −1 |
| `rear-lamp-main-cli.json` | 368 | 143 | 145 | 147 | 143 | 0 |
| `rear-lamp-kb-deterministic.json` | 864 | 108 | 113 | 113 | 109 | +1 |
| `rear-lamp-kb-jev.json` | 389 | 154 | 153 | 151 | 147 | −7 |
| `rear-lamp-kb-jev-filter-v4.json` | 342 | 140 | 158 | 146 | 142 | +2 |
| `rear-lamp-kb-sol-rewrite.json` | 420 | 143 | 150 | 149 | 145 | +2 |
| `rear-lamp-qwen-split-rewrite.json` | 446 | 133 | 137 | 137 | 133 | 0 |
| `rear-lamp-mix-examples-cut.json` | 341 | 138 | 145 | 147 | 143 | +5 |
| `rear-lamp-kb-v5-rewrite.json` | 363 | 148 | 158 | 157 | 153 | +5 |
| `rear-lamp-deterministic-sibling.json` | 647 | 106 | 111 | 109 | 105 | −1 |
| `upload/agent-v3.json` | 302 | 116 | 108 | 115 | 111 | −5 |

- Mean absolute error 2.5 matches; Spearman 0.96 against the platform. The lexical judge: 6.4,
  and +18 on the minimal-edit v4 rewrite.
- The acceptance bar (±3 on every file) is not met: five files are off by 5 to 7. The platform
  itself scored the same Fable file 149 and 142, so a single upload carries about that much
  noise; treat differences under about 5 matches as a tie.
- Held out: with the rule and offset chosen on the 8 uploads before 21:05, the 7 later ones come
  out in the platform's order except `mix` and `v4` (2 matches apart on the platform), mean error
  3.8.

**Configurations tried** (mean absolute error, Spearman):

| Configuration | MAE | Spearman |
|---|---|---|
| Old `model_judge.py` (booleans, top 4 candidates) | crashed on batch length, never finished | |
| Graded, match at 2 or more | ~16 (too many) | |
| Graded, match at 3 or more | 3.6 (−11 on `kb-jev`) | 0.83 |
| Graded, match at 4 | far too few | |
| Graded ≥ 3 and same or related paragraph | 4.5 to 5.0 | 0.80 |
| 4, or 2–3 checked yes, plain prompt | 18.2 | 0.65 |
| 3–4, or 2 checked yes, plain prompt | 3.4 | 0.90 |
| 3–4, or 2 checked yes, lenient prompt, minus 4 | **2.5** | **0.96** |

Grading a candidate next to closer variants of the same gold row makes pass 1 too strict on
rewrites that rename the subject or keep extra table values (`kb-jev`, `sol`): pass 2 fixes that by
asking about each borderline pair alone.

**Cost.** Calibration: 340 grading and 58 check calls on the subscription. A new 390-row file
takes about 2 minutes; a cached rerun takes seconds. Verdicts are cached per pair in
`data/cache/model_judge/`, so scoring a subset of a judged file's rows costs nothing.
