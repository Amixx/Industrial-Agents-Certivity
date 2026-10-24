# Lane G: Sunday feasibility of the winners

State: running. Updated: 24 Oct 23:00 CEST.
Approved spend: $8. Spent: $1.72 ($0.41 six Haiku runs, $1.088 Sonnet, $0.225 Opus-reference rewrite). The vote is free. Opus relevance was 39 cache hits and $0.

## Checklist

- [ ] G1 On `brain/data/synthetic/bumper-plain` and `bumper-sensors-fog`, time and price k cheap
      runs (Sonnet or `claude -p`, varied prompts) and the vote.
      Part done 22:48: six Haiku 5.5 runs on bumper-plain (relevance and rewrite both Haiku), 36
      to 46 s and $0.06 to $0.08 each, $0.41 in all. Files: `out/experiments/G-bumper-plain-haiku-*`
      (`.json` submission, `.log`, `-scores.json` with llm, decision-model and blended score of
      all 923 candidate paragraphs, timings, spend). Code: `brain/swing/g_runs.py`.
      Vote done 22:57, free. Files: `out/experiments/G-bumper-plain-vote{1,2,3,4}-anchor-6.json`,
      `G-bumper-plain-vote-cluster-mr{2,3,4}.json`, `G-blend-sweep.json`. Against 67 silver
      paragraphs, best single run is haiku-alt-s0 (P 0.54 R 0.61 F2 0.596, 38 s, $0.061).
      Paragraph vote, anchor haiku-base-s0: min 1 (union) P 0.31 R 0.78 F2 0.598; min 2
      P 0.40 R 0.67 F2 0.592; min 3 P 0.48 R 0.64 F2 0.602; min 4 P 0.63 R 0.61 F2 0.616
      (best F2, recall does not beat the best single run). Row clusters at min-rows 2/3/4:
      F2 0.595 / 0.602 / 0.604. Unions of k runs, mean recall: k=1 0.60, k=2 0.68, k=3 0.72,
      k=4 0.74, k=6 0.78; F2 stays near 0.60. Averaging the six LLM scores and re-blending
      (weight 0.7, cut 0.15, floor) selects 152 paragraphs at P 0.35 R 0.76 F2 0.614; the
      default cut 0.20 is P 0.48 R 0.63 F2 0.590. Haiku weight 0.85 does not reach the 0.91
      recall quoted for a stronger relevance model.
      Sonnet run done 22:59. File: `out/experiments/G-bumper-plain-sonnet-base-s0.json` (+ `.log`,
      `-scores.json`). 45 new Sonnet calls, no cache-hits line, $1.088, wall 59 s
      (profile 3 s, regulations 16 s, relevance 21 s, rewrite 19 s). 138 rows, 68 paragraphs.
      P 0.78 R 0.79 (53/67) F2 0.789, LLM AUC 0.976. One Sonnet run beats every Haiku vote
      on precision, recall and F2.
      Opus reference done 23:00. File: `out/experiments/G-bumper-plain-opus-ref.json`.
      Opus profile, regulations and relevance: 39 cache hits, 0 s, $0 new. Sonnet rewrite of the
      64 selected paragraphs: 6 calls, $0.225, 20 s, no Sonnet cache-hits line (the batches
      differ from the Sonnet run). 123 rows, 60 paragraphs. P 0.75 R 0.67 (45/67) F2 0.686,
      LLM AUC 0.970. Weaker than the single Sonnet run on recall and F2. The silver labels are
      Opus-made; that did not make this Opus selection win.
      Still to do: fog bumper, then a Sonnet blend at weight 0.85 (offline sweep, below).
- [ ] G2 Paragraph recall and precision of the voted file against the silver bumper labels, next
      to a single run's.
- [ ] G3 Exact Sunday commands for the best feasible variant, with wall-clock time and cost, as a
      proposal for task 06 (runbook not edited).

Next (all from `brain/`):

1. Vote: done at 22:57. See the G1 note.
2. Sonnet run: done at 22:59, $1.088, 59 s, F2 0.789. Log has no cache-hits line.
3. Opus reference: done at 23:00. Log: `claude-opus-5-5: 39 cache hits`, new spend $0.225
   (Sonnet rewrite only). F2 0.686, behind Sonnet's 0.789.
   Offline Sonnet blend sweep (selection, same labels): weight 0.7 cut 0.20 is P 0.75 R 0.81
   F2 0.794 (the run above, 72 paragraphs). Weight 0.85 cut 0.20 is P 0.73 R 0.87 F2 0.833
   (80 paragraphs). Weight 0.85 cut 0.15 is P 0.62 R 0.90 F2 0.822. Run weight 0.85 next; the
   relevance calls should be cache hits.
4. Fog bumper, four Haiku runs about $1.20: base seed 0, base seed 1, alt seed 0, verbatim seed 3
   on `data/synthetic/bumper-sensors-fog` with `--only "UN R10" "UN R48" "UN R149" "UN R148"
   "UN R127" "UN GTR 9" "UN R42" "UN R26"`. Stop if the first run prices the four above the
   remaining cap.
5. G2 and G3 as in the task file.

Resuming a half-finished run: rerun the same `run` command. Finished LLM calls come back from
`brain/data/cache/llm/` for free, and the log's `cache hits` line shows how many.

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
| 24 Oct 22:59 | out/experiments/G-bumper-plain-sonnet-base-s0.json | Sonnet 5.5 relevance + rewrite, main's prompts, seed 0, regs fixed | g_runs.py | 138 | P 0.78 R 0.79 (53/67) F2 0.789, AUC 0.976; 59 s | none | $1.088 |
| 24 Oct 23:00 | out/experiments/G-bumper-plain-opus-ref.json | Opus 5.5 relevance (cached) + Sonnet 5.5 rewrite, main's prompts, seed 0 | g_runs.py | 123 | P 0.75 R 0.67 (45/67) F2 0.686, AUC 0.970; 21 s | none | $0.225 |

## Uploads

None planned: lane G works on the bumper, which has no platform score before Sunday.

## Notes

- `claude -p` is not logged in for agents ("Not logged in · Please run /login"), so every run
  here uses the API. Told the master at 22:43.
- Cost plan written before spending (measured on the first Haiku run, plain bumper, 923
  candidate paragraphs: 288k in / 80k out, $0.07, 62 s):
  plain bumper 6 Haiku runs $0.45, 1 Sonnet run about $1.40, 1 Opus relevance + Sonnet rewrite
  reference about $2.75; fog bumper (3,898 candidates, 4.2x the tokens) 4 Haiku runs about
  $1.20. Total about $5.80 of the $8.
- Runs fix the regulation list with `--only` (the 08:30 review): plain = R42, R26, R127, GTR 9;
  fog = the eight the pipeline selects (R10, R48, R149, R148, R127, GTR 9, R42, R26).
- First numbers (P, R against the 67 silver-cited paragraphs incl. GTR 9's 16): single Haiku runs
  reach paragraph recall 0.54 to 0.63 at precision 0.37 to 0.55; the runs disagree enough (75
  to 118 paragraphs) that a vote has room. Relevance takes 13 to 15 s, rewrite 22 to 33 s, so
  k Haiku runs fit the Sunday window many times over. The low recall is mostly the blend with
  the lamp-fitted decision model (weight 0.7), which the note in `brain/relevance.py` already
  flags for the bumper. The silver labels are Opus-made, so an Opus run will look better on them
  than it may be.
- Haiku 5.5 takes no server-side fallback; `g_runs.py` strips `fallbacks` and its beta for Haiku.
- Vote (22:57, free). Written-paragraph Jaccard between runs is 0.39 to 0.56, so the six
  disagree. A union (min 1) lifts recall from 0.63 to 0.78 and drops precision from 0.54 to
  0.31; F2 barely moves (0.596 to 0.598). The best F2 is min 4 (0.616) by raising precision
  to 0.63 while recall stays at the best single run. Mean recall of a random union grows
  with k (0.60, 0.68, 0.72, 0.74, 0.78 for k = 1, 2, 3, 4, 6) and mean F2 stays near 0.60.
  Majority votes lose recall. `haiku-base-s0-scores.json` was rewritten by a cache-only rerun
  (wall 1 s, $0, 47 hits); the $0.069 and 62 s in the run log are the original paid run.
- Offline blend sweep (`G-blend-sweep.json`): the stored `selected` sets match
  `relevance.blend` at weight 0.7, cut 0.20, plus the floor. Averaging the six LLM scores
  does not beat a vote on F2. Raising the Haiku weight to 0.85 or 1.0 buys recall and spends
  precision; it does not reproduce the 0.91 recall in `brain/relevance.py`, which was measured
  for a stronger relevance model. Lane B's cached Opus blend on this case: pipeline
  64 paragraphs, recall 0.69, precision 0.72; blend >= 0.10 is recall 0.91 at precision 0.43.

## Report
