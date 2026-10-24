# Lane A: vote ensemble

State: running. Updated: 24 Oct 22:40 CEST.
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
- [ ] A2 Sweep the vote threshold, and weighted votes (by platform matched, by run family).
- [ ] A3 Choose the representative text (Fable, Opus, highest word share, longest, medoid).
- [ ] A4 Subsample k of the runs (k = 3, 4, 6, 8) and plot F2 against k; measure diversity.
- [ ] A5 Nominate the best threshold and representative, and one more aggressive variant.

Next: A2, vote threshold and weighted votes (`a_votes.py sweep`).

## Run log rows

| Run | File | Method | Code | Rows | Local matched / F2 | Platform (upload): matched / F2 | Spend |
|---|---|---|---|---|---|---|---|

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
- Rebuild: from `brain/`, `BRAIN_LLM= PYTHONPATH=. uv run python swing/a_votes.py pool` (6 s).

## Report
