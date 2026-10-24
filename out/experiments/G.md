# Lane G: Sunday feasibility of the winners

State: paused (handed to Cursor by the master at 22:48). Updated: 24 Oct 22:49 CEST.
Approved spend: $8. Spent: $0.41 (six Haiku runs, plain bumper).

## Checklist

- [ ] G1 On `brain/data/synthetic/bumper-plain` and `bumper-sensors-fog`, time and price k cheap
      runs (Sonnet or `claude -p`, varied prompts) and the vote.
      Part done 22:48: six Haiku 5.5 runs on bumper-plain (relevance and rewrite both Haiku), 36
      to 46 s and $0.06 to $0.08 each, $0.41 in all. Files: `out/experiments/G-bumper-plain-haiku-*`
      (`.json` submission, `.log`, `-scores.json` with llm, decision-model and blended score of
      all 923 candidate paragraphs, timings, spend). Code: `brain/swing/g_runs.py`.
      Still to do: the vote over the six, the Sonnet run, the Opus reference, fog bumper.
- [ ] G2 Paragraph recall and precision of the voted file against the silver bumper labels, next
      to a single run's.
- [ ] G3 Exact Sunday commands for the best feasible variant, with wall-clock time and cost, as a
      proposal for task 06 (runbook not edited).

Next (all from `brain/`; `P='--only "UN R42" "UN R26" "UN R127" "UN GTR 9"'`):

1. Vote, free: `PYTHONPATH=. uv run python swing/g_runs.py vote bumper-plain haiku-base-s0
   haiku-base-s1 haiku-alt-s0 haiku-alt-s2 haiku-base-s3-verbatim haiku-base-s4-b40 --min 2`
   (try `--min 1..4`, and `--rows cluster --min-rows 2`), then `swing/g_runs.py labels
   bumper-plain vote2-anchor-6 ...`. Also worth doing offline from the `-scores.json` files:
   average the six `llm` scores, re-blend with `model` (`brain.relevance.blend`) and sweep the cut.
2. Sonnet run, about $1.40: `PYTHONPATH=. uv run python swing/g_runs.py run
   data/synthetic/bumper-plain --name sonnet-base-s0 --rel-model claude-sonnet-5-5 --rw-model
   claude-sonnet-5-5 --only "UN R42" "UN R26" "UN R127" "UN GTR 9" 2>
   ../out/experiments/G-bumper-plain-sonnet-base-s0.log`
3. Opus reference (main's Sunday default), about $2.75 or less: lane B cached Opus profile,
   regulation choice and relevance for bumper-plain with main's prompts at about 22:50, so
   `--name opus-ref --rel-model claude-opus-5-5 --rw-model claude-sonnet-5-5 --seed 0` (seed 0 =
   main's order) may be mostly cache hits; check the `[g] ... cache hits` line in the log.
4. Fog bumper, four Haiku runs about $1.20: same `run` commands on
   `data/synthetic/bumper-sensors-fog` with `--only "UN R10" "UN R48" "UN R149" "UN R148" "UN R127"
   "UN GTR 9" "UN R42" "UN R26"`.
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

## Report
