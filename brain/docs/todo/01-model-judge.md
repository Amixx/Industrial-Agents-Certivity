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

**Ground truth you have.** Five dev files scored by the platform, with the number of gold
requirements each matched (recall times 190):

| File | Rows | Platform matches | Local lexical judge |
|---|---|---|---|
| `../out/rear-lamp-deterministic.json` | 778 | 107 | 112 |
| `../out/rear-lamp-sonnet.json` | 344 | 140 | 131 |
| `../out/rear-lamp-opus.json` | 338 | 143 | 139 |
| `out/dev-upload.json` | 407 | 145 | 138 |
| `../out/rear-lamp-fable.json` | 332 | 149 | 141 |

A sixth arrives tonight: a qwen3.5:9b rewrite of Fable's paragraphs; its platform score will
be added to `../out/README.md`. Hold one file out as a check; do not tune on all of them.

**What to do.**
1. Read `eval/model_judge.py`, `eval/judge.py` and the platform's rule in
   `../docs/CHALLENGE.md` ("same scope, condition and constraint").
2. Run the model judge on the five files as it is. Report matches per file next to the
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

(fill in)
