# Lane F: requirement-level selector over a wide pool

State: stopped at the master's request (handover to Cursor). Updated: 24 Oct 23:25 CEST.
Approved spend: $5. Spent: $1.25 (Opus keep pass $0.83, Sonnet keep pass $0.42).

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
- [~] F3 Logistic model, leave one regulation out; cut where expected F2 is highest (keep rows
      above F2 / 5, iterate). Mostly done 23:25 with Opus p_keep (`brain/swing/f_fit.py`; the
      log-scale sets below are in a scratch script, not yet in `f_fit.py`). Local judge, out of
      fold, at the expected-F2 cut:

      | Features | AUC (R10 / R148 / R150 / R48) | Rows | Expected matched | Local matched / F2 |
      |---|---|---|---|---|
      | votes alone (log) | 0.865 (0.862 / 0.880 / 0.896 / 0.845) | 402 | 161 | 157 / 0.676 |
      | log votes + logit p_keep | 0.892 (0.923 / 0.884 / 0.939 / 0.855) | 356 | 160 | 154 / 0.690 |
      | log votes + logit p_keep + word share | **0.909** (0.944 / 0.892 / 0.947 / 0.883) | 342 | 160 | **158 / 0.717** |
      | the above + paragraph depth | 0.911 | 330 | 159 | 157 / 0.720 |
      | the above with Opus paragraph relevance added | 0.896 | 340 | 160 | 156 / 0.709 |
      | one run, no votes: logit p_keep + word share + relevance | 0.813 | 441 | 156 | 148 / 0.616 |
      | vote baseline, best threshold (v8) | | 325 | | 150 / 0.691 |

      Raw-feature logistic models (`f_fit.py` as committed, 17 features) did worse (full: 303
      rows, 140 matched, 0.659): votes and p_keep combine as a product, which a linear model on
      raw values cannot express. The parameter-free ranking votes x p_keep gives 150 / 300 rows
      (0.708) and 164 / 400 rows (0.707). Fitted weights (log votes + logit keep + word share):
      1.63, 1.33, 0.99. Opus paragraph relevance gets weight 0.04: given the votes it adds
      nothing.
- [ ] F4 AUC per regulation, expected and local F2, feature weights; drop lamp-only features.
- [ ] F5 Nominate one file.

Next (all $0; every LLM answer is cached):
1. Move the log-scale feature sets into `f_fit.py`'s `SETS` (add `log_votes = log(votes)`,
   `logit_keep = logit(clip(p_keep_strong, 0.02, 0.98))` in `matrix`), rerun
   `PYTHONPATH=. uv run python swing/f_fit.py` from `brain/`, and add the same rows with
   `p_keep_bulk` (does Sonnet's judgement do as well as Opus's?).
2. Write the nominee: `PYTHONPATH=. uv run python swing/f_fit.py --set "<log votes + logit keep
   + word share>" --write votes-keep` and check it with `uv run python ../tools/validate.py
   ../out/rear-lamp-swing-F-votes-keep.json` and `uv run python -m eval.score` on it; save a `.log`.
3. Before nominating, decide on word share: it has weight 0.99, but the lexical judge itself
   rewards verbatim rows (finding 4), so part of that weight may not carry over to the
   platform. The safer nominee is log votes + logit keep only; nominate one of the two and write
   the prediction down first (local matched + about 4 for the platform).
4. F4 report: AUC table above; transfer check is still open (needs pooled runs on a bumper
   from lane G; synth-a03's gold is a subset of the dev gold, so it is not a real transfer test).

## Run log rows

| Run | File | Method | Code | Rows | Local matched / F2 | Platform (upload): matched / F2 | Spend |
|---|---|---|---|---|---|---|---|

## Uploads

| File | Question | Predicted matched / F2 | Uploaded at | Platform matched / F2 |
|---|---|---|---|---|

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
- Rebuild the pool: from `brain/`, `PYTHONPATH=. uv run python swing/f_pool.py` (3 s, $0; a
  relevance cache miss raises instead of paying).

## Report
