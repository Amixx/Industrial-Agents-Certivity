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

(fill in)
