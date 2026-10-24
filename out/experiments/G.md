# Lane G: Sunday feasibility of the winners

State: done. Updated: 24 Oct 23:12 CEST.
Approved spend: $8. Spent: $7.35 ($0.41 six plain Haiku runs, $1.088 plain Sonnet at weight 0.7, $0.225 Opus-reference rewrite, $0.257 plain Sonnet at weight 0.85, $1.039 four fog Haiku runs, $4.330 fog Sonnet at weight 0.85). Votes are free. Opus relevance was 39 cache hits and $0.

## Checklist

- [x] G1 On `brain/data/synthetic/bumper-plain` and `bumper-sensors-fog`, time and price k cheap
      runs and the vote. Done 23:12. Code: `brain/swing/g_runs.py`.
      Plain: six Haiku runs ($0.41, 36 to 62 s), their vote, one Sonnet run (59 s, $1.088),
      one Opus-relevance + Sonnet-rewrite reference (21 s, $0.225, 39 Opus cache hits), and
      the same Sonnet run at blend weight 0.85 (21 s, $0.257, 39 Sonnet cache hits).
      Fog: four Haiku runs (125 to 141 s, $0.249 to $0.271) and their vote, then one Sonnet
      run at weight 0.85 (134 s, $4.330, no cache-hits line). Files under
      `out/experiments/G-bumper-plain-*` and `out/experiments/G-bumper-sensors-fog-*`.
      Found: see the report table. One Sonnet run beats every Haiku vote on both bumpers.
- [x] G2 Paragraph recall and precision of the voted file against the silver bumper labels, next
      to a single run's. Done 23:12. Same 67 silver-cited paragraphs (R42, R26, R127, GTR 9)
      on both cases. Plain: best Haiku vote F2 0.616 (min 4 of 6; P 0.63 R 0.61) against best
      single Haiku F2 0.596 (P 0.54 R 0.61) and Sonnet weight 0.85 F2 0.838 (P 0.79 R 0.85).
      Fog: union of four Haiku runs F2 0.554 (P 0.34 R 0.66) against best single Haiku F2 0.534
      (P 0.58 R 0.52) and Sonnet weight 0.85 F2 0.779 (P 0.74 R 0.79).
- [x] G3 Exact Sunday commands for the best feasible variant, with wall-clock time and cost, as a
      proposal for task 06 (runbook not edited). Done 23:12. Commands in the report.
      `uv run python ../tools/validate.py` from `brain/` passed on the Sonnet weight-0.85 files
      and on the vote and Haiku files named below.

Next: none. Lane G is done.

## Run log rows

| Run | File | Method | Code | Rows | Local matched / F2 | Platform (upload): matched / F2 | Spend |
|---|---|---|---|---|---|---|---|
| 24 Oct 22:44 | out/experiments/G-bumper-plain-haiku-base-s0.json | Haiku 5.5 relevance + rewrite, main's prompts, regs fixed to R42/R26/R127/GTR 9 | g_runs.py | 173 | silver paragraphs P 0.55 R 0.54 F2 0.541, LLM AUC 0.885; 62 s | none (bumper) | $0.069 |
| 24 Oct 22:47 | out/experiments/G-bumper-plain-haiku-base-s1.json | as above, paragraph order seed 1 | g_runs.py | 243 | P 0.46 R 0.60 F2 0.563, AUC 0.866; 45 s | none | $0.071 |
| 24 Oct 22:47 | out/experiments/G-bumper-plain-haiku-alt-s0.json | reworded relevance prompt (REL_ALT) | g_runs.py | 177 | P 0.54 R 0.61 F2 0.596, AUC 0.900; 38 s | none | $0.061 |
| 24 Oct 22:47 | out/experiments/G-bumper-plain-haiku-alt-s2.json | REL_ALT, seed 2, batch 15 | g_runs.py | 197 | P 0.50 R 0.57 F2 0.552, AUC 0.864; 43 s | none | $0.067 |
| 24 Oct 22:48 | out/experiments/G-bumper-plain-haiku-base-s3-verbatim.json | seed 3, verbatim rewrite prompt (RW_VERBATIM) | g_runs.py | 169 | P 0.48 R 0.63 F2 0.590, AUC 0.883; 36 s | none | $0.065 |
| 24 Oct 22:48 | out/experiments/G-bumper-plain-haiku-base-s4-b40.json | seed 4, batch 40 | g_runs.py | 328 | P 0.37 R 0.63 F2 0.548, AUC 0.871; 46 s | none | $0.077 |
| 24 Oct 22:57 | out/experiments/G-bumper-plain-vote1-anchor-6.json | paragraph vote, keep paragraphs in at least 1 of 6 Haiku runs; rows from haiku-base-s0 | g_runs.py vote | 456 | P 0.31 R 0.78 (52/67) F2 0.598 | none | $0 |
| 24 Oct 22:57 | out/experiments/G-bumper-plain-vote2-anchor-6.json | same, min 2 of 6 | g_runs.py vote | 311 | P 0.40 R 0.67 (45/67) F2 0.592 | none | $0 |
| 24 Oct 22:57 | out/experiments/G-bumper-plain-vote3-anchor-6.json | same, min 3 of 6 | g_runs.py vote | 232 | P 0.48 R 0.64 (43/67) F2 0.602 | none | $0 |
| 24 Oct 22:57 | out/experiments/G-bumper-plain-vote4-anchor-6.json | same, min 4 of 6 | g_runs.py vote | 155 | P 0.63 R 0.61 (41/67) F2 0.616 | none | $0 |
| 24 Oct 22:57 | out/experiments/G-bumper-plain-vote-cluster-mr2.json | row clusters, Jaccard 0.6, keep a cluster written by >= 2 runs | g_runs.py vote | 301 | P 0.41 R 0.67 F2 0.595 | none | $0 |
| 24 Oct 22:57 | out/experiments/G-bumper-plain-vote-cluster-mr3.json | same, >= 3 runs | g_runs.py vote | 206 | P 0.48 R 0.64 F2 0.602 | none | $0 |
| 24 Oct 22:57 | out/experiments/G-bumper-plain-vote-cluster-mr4.json | same, >= 4 runs | g_runs.py vote | 134 | P 0.63 R 0.60 F2 0.604 | none | $0 |
| 24 Oct 22:59 | out/experiments/G-bumper-plain-sonnet-base-s0.json | Sonnet 5.5 relevance + rewrite, weight 0.7, seed 0, regs fixed | g_runs.py | 138 | P 0.78 R 0.79 (53/67) F2 0.789, AUC 0.976; 59 s | none | $1.088 |
| 24 Oct 23:00 | out/experiments/G-bumper-plain-opus-ref.json | Opus 5.5 relevance (cached) + Sonnet 5.5 rewrite, weight 0.7, seed 0 | g_runs.py | 123 | P 0.75 R 0.67 (45/67) F2 0.686, AUC 0.970; 21 s | none | $0.225 |
| 24 Oct 23:03 | out/experiments/G-bumper-plain-sonnet-w85.json | Sonnet 5.5, blend weight 0.85, relevance cached | g_runs.py | 143 | P 0.79 R 0.85 (57/67) F2 0.838, AUC 0.976; 21 s | none | $0.257 |
| 24 Oct 23:04 | out/experiments/G-bumper-sensors-fog-haiku-base-s0.json | Haiku 5.5, main's prompts, eight regs fixed | g_runs.py | 652 | on the 4 labelled regs: P 0.58 R 0.52 (35/67) F2 0.534, AUC 0.883; 125 s | none | $0.271 |
| 24 Oct 23:08 | out/experiments/G-bumper-sensors-fog-haiku-base-s1.json | same, seed 1 | g_runs.py | 717 | P 0.39 R 0.49 (33/67) F2 0.467, AUC 0.858; 136 s | none | $0.266 |
| 24 Oct 23:08 | out/experiments/G-bumper-sensors-fog-haiku-alt-s0.json | REL_ALT, seed 0 | g_runs.py | 550 | P 0.59 R 0.45 (30/67) F2 0.470, AUC 0.884; 141 s | none | $0.249 |
| 24 Oct 23:08 | out/experiments/G-bumper-sensors-fog-haiku-base-s3-verbatim.json | seed 3, RW_VERBATIM | g_runs.py | 492 | P 0.41 R 0.49 (33/67) F2 0.474, AUC 0.857; 134 s | none | $0.253 |
| 24 Oct 23:08 | out/experiments/G-bumper-sensors-fog-vote1-anchor-4.json | paragraph vote, min 1 of 4 Haiku runs | g_runs.py vote | 1120 | on the 4 labelled regs: P 0.34 R 0.66 (44/67) F2 0.554 | none | $0 |
| 24 Oct 23:08 | out/experiments/G-bumper-sensors-fog-vote2-anchor-4.json | same, min 2 of 4 | g_runs.py vote | 711 | P 0.49 R 0.52 (35/67) F2 0.516 | none | $0 |
| 24 Oct 23:08 | out/experiments/G-bumper-sensors-fog-vote3-anchor-4.json | same, min 3 of 4 | g_runs.py vote | 461 | not in the summary table; file kept | none | $0 |
| 24 Oct 23:08 | out/experiments/G-bumper-sensors-fog-vote4-anchor-4.json | same, min 4 of 4 | g_runs.py vote | 249 | P 0.74 R 0.30 (20/67) F2 0.339 | none | $0 |
| 24 Oct 23:11 | out/experiments/G-bumper-sensors-fog-sonnet-w85.json | Sonnet 5.5 relevance + rewrite, weight 0.85, eight regs fixed | g_runs.py | 519 | on the 4 labelled regs: P 0.74 R 0.79 (53/67) F2 0.779, AUC 0.981; 134 s | none | $4.330 |

## Uploads

None. Lane G scores the bumper silver labels. There is no platform upload.

| File | Question | Predicted matched / F2 | Uploaded at | Platform matched / F2 |
|---|---|---|---|---|

## Notes

- `claude -p` is not logged in for agents, so every run uses the API.
- Paragraph scores use `swing/g_runs.py labels`: precision is true positives over labelled
  selected paragraphs, recall is true positives over the 67 silver-cited paragraphs in R42,
  R26, R127 and GTR 9. Fog files also contain R10, R48, R148 and R149, which have no silver
  labels and are left out of these P, R and F2 numbers. The row counts in the run log are the
  whole file.
- `haiku-base-s0-scores.json` on the plain bumper was rewritten by a cache-only rerun (wall 1 s,
  $0, 47 hits). The $0.069 and 62 s in the run log are the original paid run.
- Opus relevance, profile and regulation choice for the plain bumper were already in the cache
  (39 hits, $0). The $0.225 is the Sonnet rewrite only. The silver labels are Opus-made; the
  Opus selection still scored below Sonnet (F2 0.686 against 0.789 at the same weight 0.7).
- `relevance.blend` binds its default weight at import, so assigning `relevance.WEIGHT` does
  nothing. `g_runs.py --weight` wraps `blend`. The first plain weight-0.85 attempt, before that
  wrap, selected the same 72 paragraphs as weight 0.7 and spent $0 (45 cache hits). The file on
  disk is the second run: 80 paragraphs selected, 143 rows, $0.257.
- A cold plain Sonnet run at weight 0.7 was 59 s and $1.088 (45 calls, no cache hits). The
  weight-0.85 file reused that relevance (39 cache hits) and paid $0.257 to rewrite 80
  paragraphs. A cold weight-0.85 run on a bumper of this size is about 60 s and about $1.15.
- Fog Sonnet at weight 0.85 was cold: 184 calls, 1,078,881 in / 214,802 out / 122,780 cache
  read, no cache-hits line, $4.330, 134 s, 310 paragraphs selected, 519 rows. Log:
  `G-bumper-sensors-fog-sonnet-w85.log`.
- Haiku 5.5 has no server-side fallback; `g_runs.py` strips `fallbacks` for it.
- Validate, from `brain/`, passed on the Sonnet, Opus, Haiku and vote files named in the report.

## Report

A vote over cheap Haiku runs lifts paragraph recall and spends precision, and F2 barely moves: on the plain bumper the best vote is 0.616 against 0.596 for the best single Haiku run, and on the fog bumper the union is 0.554 against 0.534. One Sonnet 5.5 run at blend weight 0.85 is the Sunday file. It reaches paragraph F2 0.838 on the plain bumper (P 0.79, R 0.85) and 0.779 on the fog bumper (P 0.74, R 0.79).

Scores are paragraph precision, recall and F2 against the same 67 silver-cited paragraphs. Fog P, R and F2 cover only those four regulations; the file also holds the lighting and EMC rows.

| Case | Variant | Paragraphs | Rows in the metric | P | R | F2 | Wall | Spend |
|---|---|---|---|---|---|---|---|---|
| plain | best Haiku (alt-s0) | 76 | 177 | 0.54 | 0.61 | 0.596 | 38 s | $0.061 |
| plain | Haiku vote, min 1 of 6 | 180 | 456 | 0.31 | 0.78 | 0.598 | | $0 |
| plain | Haiku vote, min 4 of 6 | 65 | 155 | 0.63 | 0.61 | 0.616 | | $0 |
| plain | Sonnet, weight 0.7 | 68 | 138 | 0.78 | 0.79 | 0.789 | 59 s | $1.088 |
| plain | Opus relevance + Sonnet rewrite | 60 | 123 | 0.75 | 0.67 | 0.686 | 21 s | $0.225 |
| plain | Sonnet, weight 0.85 | 72 | 143 | 0.79 | 0.85 | 0.838 | 21 s warm | $0.257 warm |
| fog | best Haiku (base-s0) | 61 | 157 | 0.58 | 0.52 | 0.534 | 125 s | $0.271 |
| fog | Haiku base-s1 | 88 | 233 | 0.39 | 0.49 | 0.467 | 136 s | $0.266 |
| fog | Haiku alt-s0 | 53 | 123 | 0.59 | 0.45 | 0.470 | 141 s | $0.249 |
| fog | Haiku verbatim | 80 | 156 | 0.41 | 0.49 | 0.474 | 134 s | $0.253 |
| fog | Haiku vote, min 1 of 4 | 134 | 325 | 0.34 | 0.66 | 0.554 | | $0 |
| fog | Haiku vote, min 4 of 4 | 27 | 67 | 0.74 | 0.30 | 0.339 | | $0 |
| fog | Sonnet, weight 0.85 | 72 | 138 | 0.74 | 0.79 | 0.779 | 134 s | $4.330 |

On the plain bumper a union of k Haiku runs has mean recall 0.60, 0.68, 0.72, 0.74, 0.78 for k = 1, 2, 3, 4, 6, and mean F2 stays near 0.60. The whole file on the fog Sonnet run is 519 rows (310 paragraphs selected). The 138 rows in the table are the ones in the four labelled regulations.

**Uploads.** None.

**Transfer.** The same ordering holds on both bumpers. The Haiku vote gains about 0.15 recall on the plain bumper (0.63 to 0.78) and about 0.14 on the fog bumper (0.52 to 0.66), and F2 moves by less than 0.03. Sonnet at weight 0.85 leads on both (0.838 and 0.779). The fog file's extra regulations are unlabelled, so this transfer check does not speak for R10, R48, R148 or R149.

**Sunday.** Feasible inside the five-hour window. From `brain/`, after the 08:30 review, put the kept regulation ids in `--only`:

```bash
PYTHONPATH=. uv run python swing/g_runs.py run \
  data/synthetic/bumper-sensors-fog \
  --name sonnet-w85 \
  --rel-model claude-sonnet-5-5 \
  --rw-model claude-sonnet-5-5 \
  --weight 0.85 \
  --only "UN R10" "UN R48" "UN R149" "UN R148" "UN R127" "UN GTR 9" "UN R42" "UN R26"

uv run python ../tools/validate.py ../out/experiments/G-bumper-sensors-fog-sonnet-w85.json
```

Replace the case path and the `--only` list with the held-out case and the review. Measured on the fog bumper: 134 s, $4.33, paragraph F2 0.779 (P 0.74, R 0.79) on the four labelled regulations, 519 rows in the file, validate passed. On the plain bumper the same models and weight, with `--only "UN R42" "UN R26" "UN R127" "UN GTR 9"`, scored F2 0.838 (P 0.79, R 0.85). That run was 21 s and $0.257 because relevance was cached; a cold run of this size is about 60 s and about $1.15 (the cold weight-0.7 Sonnet run was 59 s and $1.088). `--weight 0.85` has to go through `g_runs.py`: the pipeline command leaves the blend at 0.7, and on the plain bumper weight 0.7 scored F2 0.789. The runbook was not edited.
