# Prompt: coverage page ("what we miss")

Paste everything below the line into a new Claude Code session at the repo root. This is independent of `docs/regulation-change-ui-prompt.md`, and the two can run in parallel. Both edit `AssessmentHeader.svelte`, so expect a small merge there.

---

Build a coverage page in the web app. It compares an assessment with the expert's answer and shows plainly where sudo falls short and why. Hackathon juries rate a team that shows where its solution is weak and how that was measured. The brief says the same: a strong submission "shows in the pitch where it is weak and how that was measured" (`docs/final-hardening.md`). This page is also scenes 7 to 9 of our product video (`docs/product-video-prompt.md`), so it has to look right in a screen recording.

Read `CLAUDE.md`, `DESIGN.md`, `docs/final-hardening.md`, `out/README.md` (the run log, and the section on where the misses come from) and `web/` before you start. Follow DESIGN.md exactly, including its list of AI-isms to avoid.

## What exists

- **The expert's answer.** The worked example's expert answer is `cases/dev-rear-lamp/expected.json`: 190 requirements over UN R148, R48, R150 and R10. It's the only case with a full expert answer.
  - The held-out front bumper has no public answer. For it, the page says so and shows only the regulation decisions and the paragraph cut.
  - `out/README.md` mentions silver paragraph labels for the bumper. Show them only if they're in the repo, and label them as our own labels, not Certivity's.
- **A local judge.** `brain/eval/judge.py` matches requirements one to one by token overlap within the same regulation, solved as an assignment problem. It uses no model and no network.
- **A miss breakdown.** `brain/eval/errors.py` already splits the misses:
  - expert rows missed on paragraphs sudo cites, which come down to granularity or wording;
  - expert rows missed on paragraphs sudo never cites, which are selection misses;
  - sudo rows outside the expert's paragraphs.
  
  Reuse both modules. Don't write a second matcher.
- **Platform scores.** The challenge platform judges with a language model, so its counts differ from the local judge. The best dev upload is `out/rear-lamp-consolidate-v2.json`: 167 of 190 matched, F2 0.794. That row is in the run log in `out/README.md`. The scores of the other uploads are also there.
- **Paragraph scores.** Requirements carry `confidence`, the brain's probability that the paragraph is cited. Check what the stored assessment and the brain's run output keep about paragraphs that did not make the cut: their score, and the cut value used. A miss of type "below the cut" needs both numbers. If the assessment doesn't store them, add them where the pipeline already has them. Don't rerun the paid pipeline; that needs the owner's approval and a cost estimate.
- **Regulation decisions.** Excluded regulations and their reasons are already on the assessment (`regulations[].included`, `reason`). The graph's `NodeDetail` shows them.

## Backend

Add `GET /api/assessments/{id}/coverage`. It runs the local judge in the brain's venv, the way `web/backend/app/pipeline.py` runs the brain, or from a precomputed file. It returns:

1. **Totals.**
   - From the local judge: expert rows, sudo rows, matched, precision, recall, F2.
   - From the platform, where this assessment's requirements equal an uploaded file: its matched count and F2, with the upload time and the file name. Look the file up by a hash of the requirement list against the files in `out/`. If no uploaded file matches, return no platform scores, and the page says the platform never scored this exact list.
2. **Every missed expert requirement.** For each: id, text, regulation, page, paragraph, and one reason.
   - `below_cut`: sudo never cites the paragraph. Include its score and the cut, if the run kept them.
   - `split_finer`: sudo cites the paragraph but has fewer rows there than the expert.
   - `worded_differently`: sudo cites the paragraph with as many rows, but the judge didn't pair them.
   
   For the last two, also return sudo's nearest requirement on that paragraph, by the judge's similarity.
3. **Every sudo requirement the expert didn't list,** split by whether its paragraph is in the expert's set.
4. **The excluded regulations** with their reasons, from the assessment.

Precompute the response for the stored rear lamp assessment and commit it, so the page works on Render without the brain's venv if it has to. A backend test covers the reason split on a small fixture.

## Frontend

Add a "Coverage" tab to `AssessmentHeader`, and a page at `/a/[id]/coverage`, in the app shell with the ink canvas and the tokens. Top to bottom:

1. **Score band.** Two large teal numerals, "167 of 190" expert requirements matched and F2 "0.794", with a mono label that names the judge: "Challenge platform, uploaded 25 Oct 04:57". Next to them, in smaller type, the local judge's numbers with the label "Local judge, token overlap". Under both, a thin bar shows matched and missed as two shares in the existing tokens. One sentence: "sudo leans toward recall: a missed requirement costs more than an extra one to strike out."
2. **Missed expert requirements.**
   - Grouped by reason, each group with a count and a one-line plain explanation:
     - "Paragraph ranked below the cut. The engine scored it, but under the threshold."
     - "Expert splits it finer. One expert row per table row or list item, one sudo row for the paragraph."
     - "Same paragraph, different wording. The judge did not pair them."
   - Each row shows the expert text with its regulation, page and paragraph in mono. For below-the-cut rows it adds the score against the cut, for example "0.12, cut 0.15".
   - Clicking a row expands it. The expert text sits beside sudo's nearest requirement, with a "Read the paragraph" button that opens the existing `PdfDrawer` on that paragraph.
3. **Rows the expert did not list.**
   - A count, then the rows grouped by regulation and collapsed by default.
   - Rows on the expert's paragraphs and rows on other paragraphs are counted separately.
4. **Regulations left out on purpose.** One line per excluded regulation, with its reason, for example UN R7, R23 and R3, which UN R148 and R150 replaced.
5. **For assessments without an expert answer** (the bumper): one sentence saying there is no public expert answer to compare against. Then only bands 3 and 4, adapted: the paragraphs near the cut, and the excluded regulations.

The animations are short and functional: numerals roll once on load, groups expand in place. The page must read as a measurement, not a disclaimer.

## Copy

Sentence case, plain words, no exclamation marks, no em dashes or middle dots as separators, no "AI" badges. State numbers flatly, with no apology, no spin, and no "only". Every number on the page comes from the judge or the run log, and each block names its source.

## Done when

- The rear lamp assessment's coverage page shows the platform and local scores, every missed expert requirement with one of the three reasons, the extra rows and the excluded regulations.
- Opening a miss shows sudo's nearest requirement, and the PDF drawer opens on the paragraph.
- The front bumper assessment shows the no-expert-answer state without errors.
- `make check` and `make test` pass, and a backend test covers the reason split.
- You checked the page in the browser preview in dark mode at 1920×1080 and attached a screenshot of each band.
- The page is committed straight to `main` (pull before pushing, never force push). If you score a file on the way, record it in `out/` as `CLAUDE.md` asks.
