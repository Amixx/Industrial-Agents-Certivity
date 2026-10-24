# Lane F: requirement-level selector over a wide pool

State: done. The chosen file is not nominated: 4 of 5 upload slots were already used this hour.
Updated: 24 Oct 23:00 CEST (`date`).
Approved spend: $5. Spent: $1.25 (Opus keep pass $0.83, Sonnet keep pass $0.42). Fit and scoring $0.

## Checklist

- [x] F1 Pool: lane A's `out/experiments/A-pool.json` if it exists, else the union of the
      model-written dev files, built here. Done 23:05. Files: `brain/swing/f_pool.py`,
      `out/experiments/F-pool.json`. Commit: "swing F: step 1".
      Found: lane A's pool (949 clusters, 15 files, medoid text, 14 voters) with features and
      labels; 177 gold rows assignable, 279 clusters within 0.45 of some gold row. Vote baseline
      on this pool, local judge: v5 413 rows / 157 matched / F2 0.669; v6 381 / 155 / 0.679;
      v8 325 / 150 / **0.691**; v10 265 / 133 / 0.649. Opus paragraph relevance for all 2,805
      lamp paragraphs read from the cache ($0). Spend $0.
- [x] F2 Features per row: votes, paragraph relevance, regulation, word share against the source,
      length, number count, modality, cites another paragraph, position in paragraph, and an LLM
      answer to "would an expert list this row" (start from `kb-stack`'s `brain/keep.py`).
      Done 23:20. Files: `brain/swing/f_keep.py`, `out/experiments/F-pool.json` (fields
      `p_keep_strong`, `p_keep_bulk`), `out/experiments/F-keep-strong.log`, `F-keep-bulk.log`.
      Commit: "swing F: steps 2 and 3". Found: `kb-stack`'s keep prompt over all 949 clusters,
      batches of 30, effort low: Opus 32 calls, 125k in / 16k out, $0.83, 31 s; Sonnet the same
      calls, $0.42, 27 s. Sonnet's and Opus's p_keep correlate at 0.87. (Both logs report
      exactly the same token counts. The answers differ, so these were two real runs; the
      matching counts are not explained.)
- [x] F3 Logistic model, leave one regulation out; cut where expected F2 is highest (keep rows
      above F2 / 5, iterate). Done 23:00. Files: `brain/swing/f_fit.py`. Spend this step $0
      (no new calls; `p_keep_*` already on the pool). The log-scale sets are in `SETS`.
      `log_votes = log(votes)`, `logit_keep = logit(clip(p_keep_strong, 0.02, 0.98))`,
      `logit_keep_bulk` the same clip of `p_keep_bulk`. Out of fold, local judge:

      | Features | AUC (R10 / R148 / R150 / R48) | Rows | Expected matched / F2 | Local matched / F2 |
      |---|---|---|---|---|
      | votes alone (log) | 0.865 (0.862 / 0.880 / 0.896 / 0.845) | 402 | 160.8 / 0.692 | 157 / 0.676 |
      | log votes + logit keep (Opus) | 0.892 (0.923 / 0.884 / 0.939 / 0.855) | 356 | 159.9 / 0.716 | 154 / 0.690 |
      | the above + word share | 0.909 (0.944 / 0.892 / 0.947 / 0.883) | 342 | 160.2 / 0.727 | 158 / 0.717 |
      | the above + depth | 0.912 (0.933 / 0.902 / 0.943 / 0.887) | 331 | 158.6 / 0.727 | 158 / 0.724 |
      | the above + paragraph relevance | 0.900 (0.933 / 0.869 / 0.943 / 0.877) | 328 | 156.7 / 0.720 | 155 / 0.712 |
      | one run, no votes: keep + share + relevance | 0.811 (0.876 / 0.727 / 0.894 / 0.803) | 443 | 155.3 / 0.645 | 148 / 0.615 |
      | log votes + Sonnet keep | 0.885 (0.927 / 0.860 / 0.937 / 0.858) | 360 | 159.1 / 0.710 | 154 / 0.687 |
      | Sonnet keep + word share | 0.897 (0.939 / 0.868 / 0.939 / 0.884) | 339 | 158.0 / 0.719 | 158 / 0.719 |
      | vote threshold 8 of 14 (F1, not a fit) | | 325 | | 150 / 0.691 |

      R26 has 17 clusters and 0 assigned gold rows, so its AUC is undefined. It is not a feature.
      A linear model on the raw features (the old `full` set, 17 columns) is worse: AUC 0.871,
      303 rows, 140 local matches, F2 0.659. Votes and p_keep combine as a product.
- [x] F4 AUC per regulation, expected and local F2, feature weights; drop lamp-only features.
      Done 23:00. Chosen model, standardised coefficients fit on all 949 clusters:
      `log_votes` +1.65, `logit_keep` +1.02. With word share added: +1.63, +1.33, +0.99.
      Depth beside those three is +0.39. Paragraph relevance beside them is +0.06, and adding
      it lowers AUC from 0.912 to 0.900. Depth beside log votes and the keep score only (no
      word share) is +0.28 and does not move the local score (354 rows, 154 matched, F2 0.691).
      Sonnet's pair: `log_votes` +1.73, `logit_keep_bulk` +0.87. None of these features is
      lamp-only. Regulation is the leave-one-out fold, not a covariate. See the report.
- [x] F5 Write the chosen submission and score it. Done 22:59, reported 23:00.
      File: `out/rear-lamp-swing-F-votes-logit.json` (and `.log`). Not nominated for upload.
      `validate.py`: pass, 356 requirements. `score_local.py`: regulation precision/recall/F1
      1.000 / 1.000 / 1.000 (4 / 4 / 4); page 0.803 / 0.925 / 0.860 (61 / 53 / 49).
      `eval.score` requirement level: 154 matched of 190, F2 0.690 (P 0.433, R 0.811).
      `score_local.py` does not compute requirement F2. Its page figure is F1; `eval.score`
      prints page F2 0.897 on the same 61 / 53 / 49 counts.

Next: nothing further in this lane. Do not rebuild `F-pool.json` (`f_pool.py` drops `p_keep_*`).
Do not start another keep pass. The file to upload when a slot is free is
`out/rear-lamp-swing-F-votes-logit.json`.

## Run log rows

| Run | File | Method | Code | Rows | Local matched / F2 | Platform (upload): matched / F2 | Spend |
|---|---|---|---|---|---|---|---|
| 24 Oct 22:59 | `rear-lamp-swing-F-votes-logit.json` | Leave-one-regulation-out logistic on log(votes) and logit(Opus p_keep). Cut at max expected F2. Word share left out. | `f_fit.py` on `big-swings` | 356 | 154 / 0.690 | not uploaded (4 of 5 slots used this hour) | $0 (keep passes already $1.25) |

## Uploads

Not nominated. At 23:00 the hour already had 4 of 5 uploads. Candidate for a later slot:
`out/rear-lamp-swing-F-votes-logit.json`, local 154 matched, F2 0.690. The brief's usual
Claude-style gap of about +4 matches would be 158 matched and F2 0.708
(5 x 158 / (760 + 356)). The medoid texts are mixed runs, so that +4 is a guess, not a
second measurement.

| File | Question | Predicted matched / F2 | Uploaded at | Platform matched / F2 |
|---|---|---|---|---|
| `out/rear-lamp-swing-F-votes-logit.json` | Does a row-level keep judgement plus votes beat paragraph relevance and a vote threshold, on the platform? | local 154 / 0.690; platform guess 158 / 0.708 | not queued | |

## Notes

- Labels: `y` assigns each gold row to at most one cluster (local judge, count first, then the
  cluster with more votes, then similarity), so the sum of `y` over any subset is close to the
  local matched count of that subset. `y_any` marks clusters within 0.45 of any gold row.
- `claude -p` is not logged in for lane agents (master, 22:55): LLM features go through the API.
- Resuming: `f_pool.py` rewrites `F-pool.json` and drops the `p_keep_*` fields. After a
  rebuild, rerun `PYTHONPATH=. uv run python swing/f_keep.py --tier strong` and `--tier bulk`
  (both come from the cache, $0, as long as the pool order and texts are unchanged; the cost
  line should say 0 new calls). The `--cap` flag stops a run once its new spend passes the cap.
- Labels on the pool give the local judge's count for any subset to within a few matches
  (v5: 157 labelled = 157 by `judge.match`), so `sum(y)` is a fast local score.
- Word share was measured and left out of the file. Against the Opus keep model it adds 28
  rows (8 labelled, mean word share 0.98) and drops 42 (5 labelled, mean word share 0.62).
  Net about +4 local matches, inside the noise band of about 5, and on the verbatim side the
  lexical judge over-counts (finding 4 in the task file).
- Chosen set name for a rerun, from `brain/`:
  `PYTHONPATH=. uv run python swing/f_fit.py --set "log votes + logit keep" --write votes-logit`

## Report

Log(votes) plus an Opus keep judgement beats paragraph relevance and a votes-only logistic model: out-of-fold AUC 0.892 (R10 0.923, R148 0.884, R150 0.939, R48 0.855) and 154 local matches at 356 rows (F2 0.690, expected 159.9 matches and F2 0.716), against AUC 0.865 and F2 0.676 for log(votes) alone, with paragraph relevance at weight +0.06 once those two features are present. It ties the best fixed vote threshold (150 matches, F2 0.691 at 8 of 14 runs), Sonnet's keep score matches the 154 local hits (AUC 0.885, F2 0.687), and word share's further local gain (158 matches, F2 0.717) is 28 near-verbatim rows the lexical judge is known to over-count, so the chosen file leaves word share out.

### Table

Same numbers as the F3 checklist. R26 (17 clusters, no gold row) has no AUC. Coefficients below are standardised and fit on all 949 clusters.

| Model | Weights | What it says |
|---|---|---|
| log votes + Opus keep (chosen) | log_votes +1.65, logit_keep +1.02 | The weight sits on these two. |
| the same + word share | +1.63, +1.33, +0.99 | Local F2 0.717. Extra rows are word share 0.98. |
| the same + depth | depth +0.39 on top of the three | Same 158 matches, 331 rows, local F2 0.724. |
| the same + relevance | llm_p +0.06 | AUC falls to 0.900. Relevance adds nothing given votes. |
| Sonnet instead of Opus | log_votes +1.73, logit_keep_bulk +0.87 | AUC 0.885, same 154 local matches, F2 0.687. |
| votes + relevance, raw | votes +1.52, llm_p +0.49 | AUC 0.861, 146 local matches, F2 0.667. |
| one run, no votes | keep +1.59, word share +0.97, relevance +0.03 | AUC 0.811, 148 matches at 443 rows, F2 0.615. |

The keep score does not replace a pool of runs. Without votes the file is larger and the local F2 is worse than one Fable run.

### Chosen file

`out/rear-lamp-swing-F-votes-logit.json`, 356 rows. Written 22:59. Not queued.

| Check | Result |
|---|---|
| `tools/validate.py` | pass (356 requirements) |
| `tools/score_local.py` regulation | precision 1.000, recall 1.000, F1 1.000 (4 / 4 / 4) |
| `tools/score_local.py` page | precision 0.803, recall 0.925, F1 0.860 (61 / 53 / 49) |
| `eval.score` requirement | 154 matched of 190, F2 0.690 (P 0.433, R 0.811) |

Expected matched under the fitted probabilities is 159.9 (F2 0.716). The local judge is 6 matches lower. That gap is the model being optimistic, not a second judge.

### Transfer, and Sunday

No feature in the chosen model is specific to a lamp. The open hole is the transfer check, which this lane did not run. Silver bumper labels are paragraph-level and lane G's plain-bumper runs have no keep scores. A keep pass on a bumper pool would be new spend (the lamp Sonnet pass was $0.42 for 949 clusters). `synth-a03`'s gold is a subset of the dev gold, so it is not a transfer test. Do not treat the lamp weights as checked for Sunday.

If the rewrite runs already exist, applying this cut is free and takes seconds. Producing the keep feature on a pool the size of the lamp's is one Sonnet pass, about $0.42 and half a minute here, and Sonnet matched Opus on the local count. Lane G's Haiku rewrites of the plain bumper were about $0.07 and under a minute each, so several runs plus one keep pass fit the 08:00 to 13:00 window. The part that is not known is whether these weights still rank bumper rows.
