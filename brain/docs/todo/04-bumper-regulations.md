# 04 Decide the regulation list for every likely bumper spec

## Prompt

You are joining a hackathon team mid-event (Certivity challenge, Munich). Read
`brain/docs/todo/README.md` first: it has the event, the scores, the rules and the tools. Work
from `brain/`.

**Why this task exists.** The held-out case is a front bumper, and the regulation list is the
decision with the largest effect on its score. A wrong extra regulation adds rows that cannot
match (requirement precision falls); a missing one loses every gold row in it (recall falls,
and recall counts four times). Rough numbers for about 350 rows and about 150 gold rows: a
wrong extra regulation costs about 0.06 requirement F2, a missing one about 0.15. At 08:00 this
has to be a lookup, not a debate.

**What the dev gold teaches** (`../docs/approach.md`, `README.md`):
- The gold cites the consolidated regulation, never the legacy ones it replaced: R148 over R6,
  R7, R23, R38; R149 over R19; R150 over R3 and R104. The index includes those legacy ones as
  decoys.
- Device regulation plus the installation regulation (R48) when the product is installed on a
  vehicle, plus EMC (R10) when the product has electronics. Light-source regulations (R37,
  R128) were not cited even for LED lamps.
- Within a regulation the gold cites whole sections for the product's functions only.

**The bumper candidates** in `../regulations/index.json`: R42 (front and rear protective
devices), R127 (pedestrian safety), GTR 9 (pedestrian safety, the global text R127
transposes), R26 (external projections). If the spec has lamps: R48 with R148 (position,
indicators) or R149 (fog lamps, headlamps). If it has electronics or sensors: R10. If it has a
radar for emergency braking: R152 or R131 (decide). Whole-vehicle regulations a bumper does not
decide alone: R94 and R137 (frontal impact), R32 (rear-end collision).

**Evidence so far.**
- The deterministic selector picks GTR 9, R127, R42 and R26 for the plain bumper spec
  (`data/synthetic/bumper-plain/spec.md`), and adds R10, R48, R149 and R148 for the spec with
  fog lamps, position lamps and parking sensors (`data/synthetic/bumper-sensors-fog/spec.md`).
- The silver labels (`data/bumper-labels/*.md`) mark GTR 9 as not cited, as unsure: under the
  1958 Agreement the approval basis is R127, which sets the same limits. Some experts would
  still list it.
- The Jev spike's regulation step scored F2 0.965 on 13 lamp cases, with R128 and R37 as its
  remaining trap; Opus scored 1.000 with one call per case (`docs/jev.md`).

**What to do.**
1. Read the scope and transitional provisions of each candidate in the corpus
   (`uv run python -c "from brain.ingest import load; ..."`), not only the titles.
2. Write five or six realistic held-out spec variants in `data/synthetic/` (plain; with fog
   lamps; with position lamps and direction indicators; with parking sensors; with a radar
   behind the bumper; with a towing eye and registration plate bracket). Use the dev spec's
   layout (`../cases/dev-rear-lamp/spec.md`).
3. For each variant, write the regulation list an expert would cite and why, one line per
   included and per excluded regulation, in a new `docs/bumper-regulations.md`. Ask one strong
   model (Opus, Grok or both, with the scope texts) as a second opinion and record where they
   disagree. Get the team's regulatory reviewer to sign off on GTR 9 against R127.
4. Run the pipeline deterministically on every variant and compare its picks with your list:
   `uv run python -m brain.pipeline data/synthetic/<variant> --no-llm`. Where it differs, fix
   `brain/select_regs.py` only if the fix is a general rule (a scope or supersession rule),
   never a bumper keyword list. Rerun `uv run python -m eval.suite --no-llm` after any change:
   the lamp cases must not lose a regulation.
5. Produce the exact `--include` / `--exclude` arguments per variant, ready to paste on Sunday.
6. Review the silver labels for R42, R127 and R26 row by row where they are marked unsure, and
   correct them (the format is in `data/bumper-labels/README.md`).

**Acceptance.**
- `docs/bumper-regulations.md` with a table: spec feature, regulations in, regulations out,
  the rule behind each, and the `--include` / `--exclude` line.
- The deterministic selector agrees with the table on every variant, or the table says why it
  does not and the review gate covers it.
- The synthetic suite keeps regulation F2 at its current values.

**Deliverables.** The doc, the spec variants, any rule change in `brain/select_regs.py`,
corrected silver labels, and notes under "Results".

**Do not.** Hard-code bumper regulations in the selector. Edit the runbook (task 06 owns it);
send it the final `--include` / `--exclude` lines instead.

## Results

24 Oct, branch `todo04` off `main` at `10c3099`. All runs deterministic (`--no-llm`); no paid
calls. One Opus 5.5 call through `claude -p` on the subscription for the second opinion.

**Lookup table and lines:** [`docs/bumper-regulations.md`](../bumper-regulations.md). Base set
for every bumper: R42, R127, R26, GTR 9. Lamps add R48 plus R149 (fog, cornering) or R148
(position, indicator, DRL); electronics add R10; a radar that serves emergency braking adds
R152 (marginal). Towing eye and plate bracket add nothing beyond R26.

**Spec variants** in `data/synthetic/`: `bumper-fog-lamps`, `bumper-position-indicators`,
`bumper-parking-sensors`, `bumper-radar`, `bumper-tow-plate`, `bumper-full`, next to the
existing `bumper-plain` and `bumper-sensors-fog`.

**Rule change in `brain/select_regs.py`:** the vehicle category ("M1", "passenger car") and
terms made only of electrical words ("wiring harness") no longer count as product terms. On
the cached LLM profiles of the two original specs, the deterministic picks now equal the LLM
review's (R152, R157, R171 and R114 gone); on the deterministic profile of `bumper-full`, R114
is gone. New test: `test_vehicle_category_and_wiring_are_not_product_terms`.

`uv run python -m eval.suite --no-llm`, before and after, identical on every case and level:

| Case | Reg F2 | Page F2 | Req F2 |
|---|---|---|---|
| dev-rear-lamp | 1.000 | 0.758 | 0.394 |
| tierA-full-filament | 1.000 | 0.792 | 0.408 |
| tierA-position-retro-led | 1.000 | 0.730 | 0.379 |
| tierA-reversing-filament | 1.000 | 0.826 | 0.435 |
| tierA-stop-lamp-led | 1.000 | 0.782 | 0.413 |
| tierA-stop-position-filament | 1.000 | 0.874 | 0.486 |
| synth-a01-stop-tail-lamp | 1.000 | 0.783 | 0.427 |
| synth-a02-reversing-lamp | 0.938 | 0.645 | 0.340 |
| synth-a03-rear-retro-reflector | 0.556 | 0.400 | 0.186 |
| synth-a04-position-lamp-retro | 0.952 | 0.677 | 0.341 |
| synth-a05-position-reversing-lamp | 0.938 | 0.636 | 0.327 |
| synth-a06-rear-combination-rfq | 0.556 | 0.304 | 0.184 |
| synth-a07-rear-position-lamp | 0.938 | 0.684 | 0.363 |

`uv run python -m eval.transfer` unchanged by the rule (bumper AUC 0.808, best F2 0.531).

**Selector against the table:** agrees on six of eight variants. On `bumper-radar` it misses
R26 (the part is "bumper cover with radar-transparent zone", so "bumper cover" never matches)
and R152; on `bumper-full` it misses R152. The lines force both in. R42 (0.49) and R26 (0.46)
sit just above the 0.40 cut on every variant, which is why every line forces the base set.

**Rehearsal:** `brain.pipeline --no-llm` on all eight variants, plain and with their lines;
outputs in `~/Personal/bench-out/bumper/` (outside the repo). Every line selected exactly the
table's regulations.

**Second opinion (Opus 5.5):** agrees with the table on every variant. GTR 9 at 0.35 and R152
for an AEBS radar at 0.40, both marginal includes. No disagreement on any list.

**Silver labels:** reviewed the unsure rows of R42, R26 and R127. Definitions, application
documents, conformity-of-production clauses and permissions are now marked not cited and sure
(R42 3.1.6, 8.1, Annex 3 3.1; R26 2.11, 2.12, 3.1.2.2, 5.6, 8.3.5; R127 7.2, Annex 3 3.2).
R26 5.5 (soft-material alternative) is now not cited: the fascia and grille are harder than 60
Shore A. 66 paragraphs cited (was 67); transfer AUC on the labels 0.812, best F2 0.537.

**Open:**
- GTR 9 against R127 has no reviewer sign-off. Recommendation: keep GTR 9 in (reasoning in
  the doc). If the reviewer drops it, move `"UN GTR 9"` from `--include` to `--exclude`.
- For task 06: `pipeline.review` keeps a forced include's lexical probability (0.00), which
  feeds the decision model's `reg_prob`. Forced R26 and R152 still got rows, but the
  probability of a forced include could be raised to the selection threshold.
