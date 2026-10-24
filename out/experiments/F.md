# Lane F: requirement-level selector over a wide pool

State: running. Updated: 24 Oct 23:05 CEST.
Approved spend: $5. Spent: $0.

## Checklist

- [x] F1 Pool: lane A's `out/experiments/A-pool.json` if it exists, else the union of the
      model-written dev files, built here. Done 23:05. Files: `brain/swing/f_pool.py`,
      `out/experiments/F-pool.json`. Commit: "swing F: step 1".
      Found: lane A's pool (949 clusters, 15 files, medoid text, 14 voters) with features and
      labels; 177 gold rows assignable, 279 clusters within 0.45 of some gold row. Vote baseline
      on this pool, local judge: v5 413 rows / 157 matched / F2 0.669; v6 381 / 155 / 0.679;
      v8 325 / 150 / **0.691**; v10 265 / 133 / 0.649. Opus paragraph relevance for all 2,805
      lamp paragraphs read from the cache ($0). Spend $0.
- [ ] F2 Features per row: votes, paragraph relevance, regulation, word share against the source,
      length, number count, modality, cites another paragraph, position in paragraph, and an LLM
      answer to "would an expert list this row" (start from `kb-stack`'s `brain/keep.py`).
- [ ] F3 Logistic model, leave one regulation out; cut where expected F2 is highest (keep rows
      above F2 / 5, iterate).
- [ ] F4 AUC per regulation, expected and local F2, feature weights; drop lamp-only features.
- [ ] F5 Nominate one file.

Next: F2, the LLM keep feature (`brain/swing/f_keep.py`, Opus, estimated $0.75).

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
- Rebuild the pool: from `brain/`, `PYTHONPATH=. uv run python swing/f_pool.py` (3 s, $0; a
  relevance cache miss raises instead of paying).

## Report
