# Lane A: vote ensemble

State: done. Updated: 24 Oct 22:57 CEST.
Approved spend: $0. Spent: $0.

## Checklist

- [x] A1 Pool every model-written dev file, cluster rows per (regulation, paragraph) at lexical
      similarity 0.5, 0.6, 0.7 and number-aware; write `out/experiments/A-pool.json`.
      Done 22:50. Files: `brain/swing/a_votes.py`, `out/experiments/A-pool.json`. Commit: see git log
      ("swing A: step 1").
      Found: 15 files, 5,695 rows. Average-linkage token Jaccard, two rows of one run never share
      a cluster. Clusters: 949 at 0.5, 1,098 at 0.6, 1,341 at 0.7; number-aware adds 70 to 150.
      Medoid text, 13 voters, local matched / rows: v5 156/395 (0.675) at 0.5, 155/389 at 0.6,
      150/369 at 0.7; v6 155/364 (0.690) at 0.5. Number-aware loses 2 to 7 matches at every
      cut (it scatters votes), so the pool is written at Jaccard 0.5, plain.
- [x] A2 Sweep the vote threshold, and weighted votes (by platform matched, by run family).
      Done 23:05. Files: `brain/swing/a_sweep.py` (`weights`). Commit: "swing A: steps 2 and 3".
      Found: the plain vote count is as good as any weighting. Medoid text, 14 voters, local
      matched at 330 / 360 / 420 rows: uniform 150 / 155 / 157; one vote per family 149 / 154 /
      157; square-root family 151 / 154 / 158; platform-matched weights 151 / 155 / 158; 13 voters
      151 / 154 / 156. Every spread is within 2 matches, inside the judge's noise. A relevance
      confidence tie-break inside a vote level adds 0 to 4. Paragraph-level votes (runs citing
      the paragraph) and per-paragraph row quotas do not beat it either (best 0.698 to 0.704
      against 0.704). Exact cuts (medoid): v>=5 413/157 (0.669), v>=6 381/155 (0.679), v>=7
      351/154 (0.693), v>=8 325/150 (0.691), v>=9 288/140 (0.668). F2 peaks at 7 to 8 of 14 runs.
- [x] A3 Choose the representative text (Fable, Opus, highest word share, longest, medoid).
      Done 23:12. Files: `brain/swing/a_sweep.py` (`reps`, `write`), `out/rear-lamp-swing-A-votes7.json`
      and `-votes4.json` with logs. Commit: "swing A: steps 2 and 3".
      Found (votes + confidence tie-break, local matched at 330 / 390 rows): medoid 151 / 156,
      Fable first 149 / 154, Opus first 147 / 151, kb-jev first 151 / 155, longest 151 / 156,
      highest word share 152 / 158 (but it picks the minimal-edit rows of `kb-jev-filter-v4`,
      the style that lost 18 on the platform), highest word share among the runs that keep
      subject and condition ("share-claude": not filter-v4, qwen, dev-upload, Sol) 153 / 158.
      share-claude is the representative: best locally, and drawn only from writers that keep the
      subject and condition. Median word share against the source paragraph (stop words dropped):
      votes7 file 1.00, Fable 0.93, kb-jev 0.88, gold 0.96.
- [x] A4 Subsample k of the runs (k = 3, 4, 6, 8) and plot F2 against k; measure diversity.
      Done 23:22. Files: `brain/swing/a_subsample.py`, `out/experiments/A-subsample.txt` (full
      output: pairwise run distances, curve, named sets). Commit: "swing A: step 4".
      Found (local F2, votes >= half of k, share-claude text, 40 random draws per k, clusters of
      the full pool restricted to the drawn runs): k=2 0.630, 3 0.669, 4 0.673, 6 0.678, 8 0.686,
      10 0.692, 12 0.696, 14 0.702. The mean single run is about 0.63, so 3 runs give about
      half of the 14-run gain. Within a k, F2 rises with diversity (correlation +0.3 to +0.6).
      Six runs of one family (Opus relevance + Sonnet rewrite, prompt variants; mean distance
      0.30) reach 0.663 to 0.669; seven runs, one per family (distance 0.49), reach 0.696. Three
      Claude models on all steps: 0.671. Four cheap Sunday-like runs (Sonnet, main-cli,
      main-a39acab, mix): 0.658. Diversity has to come from different paragraph selection
      (different relevance model or blend), not from rewrite prompt variants over the same
      cached relevance: the four mix runs share Opus relevance and sit 0.15 to 0.32 apart.
- [x] A5 Score the two files already written (`out/rear-lamp-swing-A-votes7.json`,
      `out/rear-lamp-swing-A-votes4.json`) with `tools/validate.py`, `tools/score_local.py` and
      `eval.score`, and write the report from those local numbers. No upload: the owner said the
      platform cap is 4 of 5 used this hour.
      Done 22:55, report 22:57. Files: the two json files (already committed in "swing A: steps 2 and 3").
      Commit: this commit ("swing A: step 5").
      Found, both files valid. Regulation and page P/R/F1 from `score_local.py`. Requirement
      matched count and F2 from `eval.score`. Spend $0.

      | File | Rows | Reg P / R / F1 | Page P / R / F1 (cited/expected/matched) | Req P / R / F2 (cited/expected/matched) |
      |---|---|---|---|---|
      | votes7 | 351 | 1.000 / 1.000 / 1.000 (4/4/4) | 0.831 / 0.925 / 0.875 (59/53/49) | 0.444 / 0.821 / 0.702 (351/190/156) |
      | votes4 | 463 | 1.000 / 1.000 / 1.000 (4/4/4) | 0.746 / 0.943 / 0.833 (67/53/50) | 0.348 / 0.847 / 0.658 (463/190/161) |

      `eval.score` page F2 is 0.904 on votes7 (59/53/49) and 0.896 on votes4 (67/53/50).
      Regulation F2 is 1.000 on both. The 4-vote file adds 112 rows and 5 matches (4.5%), under
      the break-even rate of about 0.14, so requirement F2 falls from 0.702 to 0.658. Page recall
      moves from 0.925 to 0.943 (49 to 50 of 53) and page precision from 0.831 to 0.746.

Next: none. Lane finished on local scores. No file nominated for upload.

## Run log rows

| Run | File | Method | Code | Rows | Local matched / F2 | Platform (upload): matched / F2 | Spend |
|---|---|---|---|---|---|---|---|
| 22:55 | `rear-lamp-swing-A-votes7.json` | Vote over 14 dev runs: clusters per paragraph at token Jaccard 0.5, keep votes >= 7, representative share-claude. Scored 22:55. | `big-swings` (`swing/a_sweep.py write --votes 7`), scored with `validate.py`, `score_local.py`, `eval.score` | 351 | 156 / 0.702 | not uploaded | $0 |
| 22:55 | `rear-lamp-swing-A-votes4.json` | The same, votes >= 4. Scored 22:55. | `big-swings` (`swing/a_sweep.py write --votes 4`), same three scorers | 463 | 161 / 0.658 | not uploaded | $0 |

Local levels, 22:55 CEST. `score_local.py` prints regulation and page precision, recall and F1.
`eval.score` prints precision, recall and F2 at regulation, page and requirement, and is the
source of the requirement matched count.

| File | Level | Source | P | R | F1 | F2 | Cited / expected / matched |
|---|---|---|---|---|---|---|---|
| votes7 | regulation | score_local | 1.000 | 1.000 | 1.000 | | 4 / 4 / 4 |
| votes7 | regulation | eval.score | 1.000 | 1.000 | | 1.000 | 4 / 4 / 4 |
| votes7 | page | score_local | 0.831 | 0.925 | 0.875 | | 59 / 53 / 49 |
| votes7 | page | eval.score | 0.831 | 0.925 | | 0.904 | 59 / 53 / 49 |
| votes7 | requirement | eval.score | 0.444 | 0.821 | | 0.702 | 351 / 190 / 156 |
| votes4 | regulation | score_local | 1.000 | 1.000 | 1.000 | | 4 / 4 / 4 |
| votes4 | regulation | eval.score | 1.000 | 1.000 | | 1.000 | 4 / 4 / 4 |
| votes4 | page | score_local | 0.746 | 0.943 | 0.833 | | 67 / 53 / 50 |
| votes4 | page | eval.score | 0.746 | 0.943 | | 0.896 | 67 / 53 / 50 |
| votes4 | requirement | eval.score | 0.348 | 0.847 | | 0.658 | 463 / 190 / 161 |

Both files passed `tools/validate.py` (351 and 463 requirements, team-06, dev-rear-lamp).

## Uploads

No file nominated. The owner said at 22:54 that the platform cap is 4 of 5 used this hour.

| File | Question | Predicted matched / F2 | Uploaded at | Platform matched / F2 |
|---|---|---|---|---|

## Notes

- Pool format (`A-pool.json`): `clusters[]` with regulation, paragraph, paragraph_key, page (mode),
  `votes` (14 voters: every file but `mix-examples-cut-consolidated`), `votes_13` (also without
  `main-a39acab`, the 13 of finding 2), `families`, `medoid`, and `members[]` (file, run,
  id_index into that file's `requirements`, text, page, paragraph, confidence, word_share against
  the corpus paragraph). `medoid_matched_in_full_pool` is the local judge's verdict when all 949
  medoids are submitted together; a proxy, not a label.
- Platform / local ratios per run (in `a_sweep.RATIO`): fable 149/141, opus 143/139, sonnet
  140/131, kb-jev 154/153, filter-v4 140/158, Sol 143/150, main-cli 143/145, mix-examples-cut
  138/145, dev-upload 145/138, qwen 133/137. The "+5 for Claude-style text" of finding 2 holds
  for the all-step Claude runs only; the Opus + Sonnet runs score 2 to 7 below local.
- STATUS.md was not edited by this lane (the master owns it). State here is done.
- A5 did not call a model. Commands, from `brain/`, with `BRAIN_LLM=` set empty:
  `uv run python ../tools/validate.py`, `uv run python ../tools/score_local.py`,
  `uv run python -m eval.score`, each on both vote files.
- Rebuild of the pool and the curves, still $0, from `brain/`:
  `BRAIN_LLM= PYTHONPATH=. uv run python swing/a_votes.py pool`,
  `... swing/a_sweep.py weights` and `reps`,
  `... swing/a_sweep.py write --votes 7 --out ../out/rear-lamp-swing-A-votes7.json`,
  `... swing/a_subsample.py --draws 40`.

## Report

Agreement across 14 existing runs is a stronger selector than a single run: clusters that 7 or more runs wrote, worded as the highest word-share row from a writer that keeps the subject and condition, match 156 of 190 expert rows in 351 rows (requirement F2 0.702, regulation F1 1.000, page F1 0.875), and the climb from one run at about 0.63 to all 14 at 0.702 is half earned by 3 runs and almost all earned by 7 runs from different families (0.696). The representative should be that share-claude row: at the same 351-row cut it matches 156 where the medoid matches 154, vote weights move the count by at most 2, and the highest word share with no style filter picks the minimal-edit rows of `kb-jev-filter-v4`, which the platform scored at 140 after a local 158.

### Local scores, 22:55 CEST

Both files are valid. Requirement matched count and F2 are from `eval.score`. Regulation and page precision, recall and F1 are from `score_local.py`. Page F2 is from `eval.score` and is a different number from page F1.

| File | Rows | Reg P / R / F1 | Page P / R / F1 | Page matched | Page F2 | Req P / R / F2 | Req matched |
|---|---|---|---|---|---|---|---|
| `rear-lamp-swing-A-votes7.json` | 351 | 1.000 / 1.000 / 1.000 | 0.831 / 0.925 / 0.875 | 49 of 53 (59 cited) | 0.904 | 0.444 / 0.821 / 0.702 | 156 of 190 |
| `rear-lamp-swing-A-votes4.json` | 463 | 1.000 / 1.000 / 1.000 | 0.746 / 0.943 / 0.833 | 50 of 53 (67 cited) | 0.896 | 0.348 / 0.847 / 0.658 | 161 of 190 |

Votes of 4 or more add 112 rows and 5 requirement matches. That is a 4.5% hit rate, below the break-even rate of about 0.14, so F2 falls from 0.702 to 0.658. One extra expert page is recovered (49 to 50) and page precision falls from 0.831 to 0.746. Both files cite all 4 expected regulations.

No file is nominated for upload. The platform cap is 4 of 5 used this hour, so these numbers stay local.

### Vote curve

Threshold sweep, medoid text, 14 voters (A2). F2 peaks at 7 to 8 votes.

| Keep votes >= | Rows | Matched | Local F2 |
|---|---|---|---|
| 5 | 413 | 157 | 0.669 |
| 6 | 381 | 155 | 0.679 |
| 7 | 351 | 154 | 0.693 |
| 8 | 325 | 150 | 0.691 |
| 9 | 288 | 140 | 0.668 |

The scored votes7 file uses share-claude text at the same cut: 351 rows, 156 matched, F2 0.702. Two more matches than the medoid at the same size.

Representative text, votes plus a confidence tie-break, local matched at 330 / 390 rows (A3): medoid 151 / 156, Fable 149 / 154, Opus 147 / 151, kb-jev 151 / 155, longest 151 / 156, highest word share 152 / 158, share-claude 153 / 158. Median word share against the source paragraph, stop words dropped: votes7 1.00, Fable 0.93, kb-jev 0.88, gold 0.96.

Subsample, share-claude text, votes at least half of k, mean local F2 over 40 draws (A4, full table in `out/experiments/A-subsample.txt`):

| k | Local F2 | Rows |
|---|---|---|
| 2 | 0.630 | 506 |
| 3 | 0.669 | 346 |
| 4 | 0.673 | 405 |
| 6 | 0.678 | 374 |
| 8 | 0.686 | 362 |
| 10 | 0.692 | 353 |
| 12 | 0.696 | 353 |
| 14 | 0.702 | 351 |

Named sets at the half-vote rule: six runs of one family (distance 0.30) reach 0.663, best cut 0.669; seven runs, one per family (distance 0.49) reach 0.696; three Claude models on every step reach 0.671; four cheap Sunday-like runs reach 0.658. Within a k, F2 rises with diversity (correlation +0.3 to +0.6). The four mix runs share one Opus relevance pass and sit 0.15 to 0.32 apart, so extra rewrite prompts over a cached relevance pass add little.

### Transfer

This lane did not score the silver bumper labels or `synthetic/cases/synth-a03-rear-retro-reflector`. The vote is a combiner: it has nothing to combine until several runs of the new product exist. Those runs, and the paragraph scores against the silver labels, are lane G's measurement and were still open when this report was written. The 0.702 is a rear-lamp result.

### Sunday

The combiner itself runs in seconds and costs $0 once the run files exist (`swing/a_sweep.py write`). It fits the 08:00 to 13:00 window. It is worth running when the runs already disagree on which paragraphs they select: seven runs from different families reached local F2 0.696 here, against 0.702 for all 14. Six runs that share a relevance model reached 0.663 to 0.669, and four cheap runs reached 0.658, level with a single good run. This lane spent $0. The cost on Sunday is the cost of the input runs, not of the vote. Lane G has timed a Haiku pass on the plain bumper at 36 to 62 seconds and $0.06 to $0.08, so several cheap passes fit the five hours; they help the vote only if their paragraph sets differ.
