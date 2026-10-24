# Lane A: vote ensemble

State: stopped by the master (hand-over to Cursor) after A4. Updated: 24 Oct 23:25 CEST.
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
- [ ] A5 Nominate the best threshold and representative, and one more aggressive variant.

Next: A5. Nominate the two files already written (no new code needed):
1. `out/rear-lamp-swing-A-votes7.json` (351 rows; local 156 / 0.702). Prediction to write in the
   upload table: 157 matched, F2 0.707 (local + 1: the representatives come from Fable, Opus and
   the Opus + Sonnet runs, whose platform / local ratios average about 1.0; the ratio estimate
   in its log says 159 / 0.716). Question: does a vote of 14 runs beat every single run on the
   platform (best single 154, kb-jev)?
2. `out/rear-lamp-swing-A-votes4.json` (463 rows; local 161 / 0.658). Prediction: 163 matched,
   F2 0.669. Question: do the 112 rows with 4 to 6 votes match more often on the platform than
   the local judge's 4.5% (the break-even rate is about 14%)?
Then set State to "waiting for upload" here and in STATUS.md, fill in the Report section (Rules,
item 5) from A1 to A4, and do the transfer check: the vote needs several runs on the bumper;
no bumper runs exist yet, so it is a lane G question. Rebuild everything from `brain/`:
`BRAIN_LLM= PYTHONPATH=. uv run python swing/a_votes.py pool`, `... swing/a_sweep.py weights|reps`,
`... swing/a_sweep.py write --votes 7 --out ../out/rear-lamp-swing-A-votes7.json`,
`... swing/a_subsample.py --draws 40` (20 s). All $0.

## Run log rows

| Run | File | Method | Code | Rows | Local matched / F2 | Platform (upload): matched / F2 | Spend |
|---|---|---|---|---|---|---|---|
| 23:12 | `rear-lamp-swing-A-votes7.json` | Vote over 14 dev runs: clusters per paragraph at token Jaccard 0.5, keep votes >= 7, representative share-claude | `big-swings` (`swing/a_sweep.py write --votes 7`) | 351 | 156 / 0.702 | not uploaded | $0 |
| 23:12 | `rear-lamp-swing-A-votes4.json` | The same, votes >= 4 | `big-swings` (`swing/a_sweep.py write --votes 4`) | 463 | 161 / 0.658 | not uploaded | $0 |

## Uploads

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
- STATUS.md was not edited by this lane (the master owns it); the lane's state is in this file.
- Rebuild: from `brain/`, `BRAIN_LLM= PYTHONPATH=. uv run python swing/a_votes.py pool` (6 s).

## Report
