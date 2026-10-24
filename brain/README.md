# Brain

Turns a product spec (and optionally its exploded view) into the JSON list of engineering
requirements the product must fulfil under UN Regulations. Each requirement cites the
regulation, base version, PDF page and paragraph. This is the main-goal backend for the
Certivity challenge. Everything lives in `brain/`.

All commands below run from `brain/`.

## Setup (once)

Needs [uv](https://docs.astral.sh/uv/). It installs Python 3.12 and the dependencies.

```bash
cd brain
uv sync --extra llm                  # PyMuPDF, scikit-learn, pydantic, anthropic, openai
uv run python -m brain.ingest        # parse the 94 regulation PDFs into data/corpus/ (about 10 s)
```

`data/corpus/` is gitignored and rebuilt by the ingest step. The pipeline also runs the ingest
automatically if the corpus is missing. The fitted decision model, `data/decision_model.json`,
is not gitignored, so commit it with the code. Refit it only after changing `brain/features.py`:

```bash
uv run python -m brain.decide        # fits on the dev gold and prints leave-one-regulation-out CV
```

## Run on a case

A case is a folder with `spec.md` and optionally `exploded_view.png`, such as
`../cases/dev-rear-lamp`.

```bash
uv run python -m brain.pipeline ../cases/dev-rear-lamp --no-llm      # deterministic, free
uv run python -m brain.pipeline ../cases/dev-rear-lamp -o out/dev.json --team-id team-07
```

| Option | Meaning |
|---|---|
| `-o, --out` | Output file. Default `out/<case>.json`. |
| `--team-id` | The platform team id. Default `team-00`. |
| `--no-llm` | Deterministic only, even when an LLM is configured. |
| `--include "UN R42" ...` | Force regulations in (review gate). |
| `--exclude "UN GTR 9" ...` | Force regulations out (review gate). Unknown or conflicting ids are rejected. |
| `--threshold 0.2` | Override the paragraph cut-off. With an LLM on, an absolute cut-off on the blended score replaces the per-regulation one. |

The log on stderr shows each step: the product profile, the selected regulations with their
probabilities, the paragraph count and the requirement count. The output file holds the
submission plus extra fields the platform ignores: `confidence` and `quote` on each requirement,
`regulations` (every selected regulation and the strongest rejected ones, with a rationale) and
`profile`.

The pipeline runs `tools/validate.py` on its output and raises if the file is invalid. Still
validate the final file before uploading:

```bash
uv run python ../tools/validate.py out/dev.json
```

From Python, which is how the backend should call it:

```python
from brain.pipeline import run

submission = run(spec_text, image_path, case_id="heldout-front-bumper", team_id="team-07")
```

## LLM modes

Without configuration the pipeline is deterministic and makes no network calls. Paid providers
are opt-in: a key in `.env` does nothing until `BRAIN_LLM` names the provider.

Put the settings in `brain/.env` (gitignored):

```bash
BRAIN_LLM=openai            # or anthropic, or local; unset means deterministic
OPENAI_KEY=...              # or OPENAI_API_KEY
ANTHROPIC_API_KEY=...
```

| `BRAIN_LLM` | Strong model (profile, regulation review, relevance) | Bulk model (rewrite) |
|---|---|---|
| `openai` | `gpt-5.5` (`BRAIN_OPENAI_STRONG`) | `gpt-5.4-mini` (`BRAIN_OPENAI_BULK`) |
| `anthropic` | `claude-opus-5-5` (`BRAIN_MODEL_STRONG`) | `claude-sonnet-5-5` (`BRAIN_MODEL_BULK`) |
| `local` | `BRAIN_LOCAL_MODEL` at `BRAIN_LOCAL_URL` (default `qwen3:14b` on Ollama) | same |

Other settings:
- `BRAIN_RELEVANCE_TIER=bulk` runs paragraph relevance on the cheap model. On dev this scored
  requirement F2 0.58 instead of 0.62, at a fraction of the cost.
- `BRAIN_LLM_TIMEOUT` sets the per-request timeout in seconds (default 180, with 3 retries).
- Local models get no image unless `BRAIN_LOCAL_VISION=1`, and answer without thinking unless
  `BRAIN_LOCAL_REASONING=low|high`. Setup and results: [docs/local-models.md](docs/local-models.md).
- Local mode sends small batches (8 paragraphs for relevance, 4 for the rewrite) one at a time;
  `BRAIN_LOCAL_BATCH` overrides the batch size.
- Where a local runner has no constrained JSON output (Ollama's MLX runner for Qwen 3.5 and
  Gemma 4), `llm.py` puts the schema in the prompt, validates the reply with `jsonschema`, and
  retries once.

**Cost.** The strong model reads every candidate paragraph of every selected regulation, which
is about 2,800 paragraphs on dev. One afternoon of experiments (several dev runs, relevance
sweeps and three full suites) cost about 70 EUR. Estimate the cost before running anything
repeatedly, and prefer the bulk tier for experiments.

Every response is cached in `data/cache/llm/`, keyed on the provider, model, prompt and schema.
Rerunning an identical step is free. Changing a prompt or the set of selected regulations makes
new calls.

If a rewrite batch fails after its retries, it falls back to the deterministic rewrite. Paragraphs
that relevance leaves unscored (a failed batch or a skipped id) get one more pass; if any are
still unscored, the run stops with an error naming their regulations. Rerun it: the cache keeps
the batches that succeeded.

## Sunday runbook (hybrid mode)

The held-out case lands at 08:00 and uploads close at 13:00. On the held-out case **the last
valid upload counts, not the best**, and uploads are limited to 5 per hour. Our team id is
`team-06`. All commands run from `brain/`.

**Saturday evening.** Add Certivity's package repository as a remote, using the address the
organisers gave out. This clone only has `origin`, the team repository:
`git remote add upstream <package repository URL>`.

**08:00 Pull and rebuild.**

```bash
git pull upstream main && git pull origin main
python ../tools/fetch_regulations.py          # downloads any PDFs the held-out case adds
uv run python -m brain.ingest && uv run python -m eval.gold_check
ls ../cases/                                  # the case folder name is the case_id
```

**08:15 Safety net: deterministic run and first upload.** It is free and takes seconds. On dev
it scored requirement F2 0.348 on the platform, against 0.68 for the best model run, so it is
only the floor.

```bash
case=../cases/heldout-front-bumper            # use the real folder name
uv run python -m brain.pipeline $case --no-llm --team-id team-06 -o out/heldout-det.json
uv run python ../tools/validate.py out/heldout-det.json
```

Upload it. Note whether the platform shows a score for the held-out case. That decides the end
game (13:00 step).

**08:30 Regulation review, with Francisca.** Read the `regulations` field and the log, then
fix the list with `--include` / `--exclude` on every later run. Rules from the dev gold:
- Cite the consolidated regulation, not the legacy ones it replaces: R148 over R6, R7, R23 and
  R38; R149 over R19; R150 over R3 and R104.
- Lighting (R48 with R148 or R149) only if the spec has lamps. R10 only if it has electronics
  (sensors, LED, wiring).
- Exclude regulations that approve the whole vehicle for something the part does not decide
  (R94 and R137 frontal impact, R32 rear-end collision), unless the spec says otherwise.
- R42, R127 and R26 are the likely core for a front bumper. **GTR 9 against R127:** keep both
  unless Francisca is more than about 70% sure GTR 9 is out. A wrong extra regulation costs
  about 0.06 of requirement F2, while a missing one costs about 0.15.
- After the rerun, check the requirement count per regulation: no core regulation may have
  zero rows.

**09:00 Model run, if one is approved.** Choose the model and its budget the evening before.
The likely bumper regulations hold about 1,040 paragraphs, about 37% of the dev case, so one
run costs about $6 with Fable 5.1 or about $2.40 with Opus 5.5, and about three times that if
lamps and sensors bring in R48 and R10. The provider's key must be in `brain/.env` (on
24 Oct it held only `OPENAI_KEY`).

```bash
BRAIN_LLM=anthropic BRAIN_MODEL_STRONG=claude-fable-5-1 BRAIN_MODEL_BULK=claude-fable-5-1 \
  uv run python -m brain.pipeline $case --team-id team-06 -o out/heldout-llm.json \
  --include ... --exclude ...
uv run python ../tools/validate.py out/heldout-llm.json
```

If a relevance batch still fails after its retry, the run stops instead of writing a weaker
file; rerun it, since finished batches are cached. Read 20 random rows against their quotes,
then upload.

**Without a model run**, the deterministic file stays the answer. Spend the morning on the
regulation review instead: on dev, the regulation list is the one thing a human can still fix
in minutes.

**13:00 End game.** Stop uploading variants at about 12:30. Then make sure the final upload is
the file you want counted:
- If the platform shows held-out scores, upload the best-scoring file once more as the last
  upload.
- If it does not, the last upload is the model-backed file with the reviewed regulation list,
  since it scored about twice the deterministic one on dev.
- Never end on an experiment.

## Evaluate

```bash
uv run python -m eval.score out/dev.json                 # F2 at three levels against dev gold
uv run python -m eval.score out/x.json --expected path/to/expected.json
uv run python -m eval.model_judge out/dev.json [more.json ...]  # calibrated model judge, platform estimate
uv run python -m eval.suite --no-llm --tag note          # dev + synthetic cases, appends eval/results.csv (local)
uv run python -m eval.suite --no-llm --cases 'synth-a*'  # only the cases in ../synthetic/cases
uv run python -m eval.cached_relevance --since "..."     # score cached relevance answers mid-run
uv run python -m eval.gold_check                         # every dev gold citation resolves on its page
uv run python -m eval.synth                              # regenerate the Tier A synthetic cases
uv run python -m eval.relevance_check                    # LLM relevance vs decision model (paid calls)
```

The regulation and page levels reuse Certivity's `tools/score_local.py`, so they should match
the platform. In `eval.score` **the requirement level is a lexical proxy** (`eval/judge.py`: token
overlap, one-to-one matching within a regulation), whose error depends on the writing style.
`eval.model_judge` is calibrated against the 16 dev uploads the platform scored: Sonnet 5.5
through `claude -p` grades each candidate pair on its own, and the platform estimate is its match
count plus 4. It is within 4.7 matches of the platform on average (Spearman 0.84); the platform
itself varies by up to 7 matches between two uploads of the same file. Calibration table:
[docs/todo/01-model-judge.md](docs/todo/01-model-judge.md). `eval.suite` without `--no-llm`
follows `BRAIN_LLM` and makes paid calls for every case.

## Develop

```bash
uv run pytest -q && uv run ruff check . && uv run mypy
```

| Path | Contents |
|---|---|
| `brain/` | The pipeline modules (table below). |
| `eval/` | Scoring, the lexical judge, the suite, synthetic cases, checks. |
| `tests/` | Unit tests per step; some need the ingested corpus. |
| `data/decision_model.json` | Fitted decision model (meant to be committed). |
| `data/synthetic/` | Tier A ablation cases with gold, and unlabelled bumper specs. |
| `out/` | Saved outputs of the runs in the results below. |
| `data/corpus/`, `data/cache/` | Generated, gitignored. |
| `docs/` | Requirement-framework notes. |

## Pipeline

| Step | Module | What it does |
|---|---|---|
| 0 | `brain/ingest.py` | Turns each PDF into a paragraph tree. It uses scope headings (Annex / Part / Appendix, and a GTR's "Text of the Regulation") and keeps the longest chain of label numbers that follow each other, so table cells and wrapped references can't derail the numbering. Labels match the gold style (`Annex 6 Part 4 3`). All 121 gold citations of the dev case resolve on their page. |
| – | `brain/graph.py` | Graph built with regexes: parent/child, "paragraph 4.6." / "Annex 3" references, links to other regulations, definitions. |
| 1 | `brain/profile.py` | Reads the spec into a `ProductProfile` (parts, functions, vehicle category, electronics; negated features such as "without radar" don't count). The LLM path also reads the exploded view. |
| 2 | `brain/select_regs.py` | Matches product terms against each regulation's title, scope, headings and definitions; checks vehicle category; pulls in the EMC regulation for electronics; demotes legacy regulations that a consolidated one "combines" (R148 over R7). The LLM path reviews all regulations, retries any it skipped, and flags any left without a verdict. |
| 3 | `brain/features.py`, `brain/decide.py` | Paragraph features (product-term match in the heading path, sections about other devices, section kind, content, graph) feed a logistic regression fitted on the dev gold, with a threshold tuned for F2. Sections about other devices are found from defined terms and from siblings: when one section under a top-level heading names the product ("6.3 Front fog lamp"), its siblings that name none ("6.2 Dipped-beam headlamp") count as other devices. A regulation whose title names the product (R42) counts as about the product throughout. TabPFN is optional (`--extra tabpfn`, `BRAIN_DECIDER=tabpfn`). |
| 3b | `brain/relevance.py` | LLM path: the strong model reads every candidate paragraph in document order, with its heading path and parent clause, and estimates P(cited). Geometric blend with the decision model (weight 0.7 on the LLM). Each regulation keeps the paragraphs scoring at least 0.3 times its best one (never below 0.10), plus its top 6%, so the cut-off follows each regulation's own scale instead of the lamp's. |
| 4 | `brain/rewrite.py` | Rewrites each paragraph as minimal-edit EARS requirements. Deterministic path: split at "shall", fold "However" into "except that", turn telegraphic lines ("In height: …") into shall-statements using the subject from the heading path. LLM path: few-shot EARS rewrite with the parent clause, so child items keep the parent's condition. |
| 5 | `brain/verify.py` | Base version only; every number must appear in the source paragraph or its ancestors; dedupe; Certivity's `validate.py`. |
| 5b | `brain/boilerplate.py` | Drops requirements whose quote only points elsewhere ("Failure provisions: See paragraph 4.6."), only brings other paragraphs into force, or spells out the approval mark. |
| 6 | `brain/sections.py` | LLM path, after the requirement filter (`brain/keep.py`): the strong model scores the cited paragraphs of each section side by side; a requirement goes when p_keep × p_section < 0.2. |
| – | `brain/llm.py` | One interface for OpenAI, Anthropic and local OpenAI-compatible servers (Ollama): structured JSON output, or prompted and validated JSON where a local runner lacks it; timeouts and retries; an atomic disk cache. |

## Results on dev

Platform scores of the uploaded dev files, with model, cost and the commit behind each, are in
[`../out/README.md`](../out/README.md). In short, requirement F2 on the platform:

| Run | Requirements | Requirement F2 (platform) | Cost |
|---|---|---|---|
| Deterministic (`--no-llm`) | 778 | 0.348 | $0 |
| gpt-5.5 relevance, gpt-5.4-mini rewrite (`out/dev-upload.json`) | 407 | 0.621 | not tracked |
| Sonnet 5.5, every step | 344 | 0.634 | $3.08 |
| Opus 5.5, every step | 338 | 0.651 | $6.36 |
| Fable 5.1, every step | 332 | 0.682 | $16.52 |

The deterministic row predates the sibling and title features. With them it gives 647
requirements on dev, page F2 0.758 and requirement F2 0.394 on the local judge (0.364 before);
the decision model is fitted on dev, so these dev numbers are optimistic. On the silver bumper
labels (`data/bumper-labels/`) the same change raises the decision model's paragraph AUC from
0.724 to 0.808.

The local judge (`eval/judge.py`) finds 4 to 9 fewer matches than the platform on model-written
text and 5 more on verbatim text, and ranks runs in the platform's order. Use it for changes
worth more than about 5 matches, and a dev upload for closer calls. `eval.suite` appends each
run to `eval/results.csv`.

Saved outputs in `out/` (from earlier versions of the pipeline):

| File | Run |
|---|---|
| `dev-llm.json` | Dev, LLM with strong-tier relevance (cut-off 0.10), 407 requirements. |
| `dev-upload.json` | The same rows as `dev-llm.json` with `team_id` `team-06`: the 0.621 platform upload above. |
| `dev-rear-lamp.json` | Dev, deterministic, 778 requirements. |
| `bumper-plain.json`, `bumper-sensors-fog.json` | Bumper smoke tests, deterministic (before the negation fix in the spec parser). |
| `bumper-plain-llm.json`, `bumper-sensors-fog-llm.json` | Bumper smoke tests, LLM with strong-tier relevance (cut-off 0.10). |

## Findings that shaped the design

- Gold paragraphs are about 4% of all paragraphs in the four dev regulations, and 25–40% of the paragraphs in the sections for the product's functions. Picking the section is the main lever.
- 42 of the 190 gold requirements come from sentences without "shall" (R48's telegraphic style). The gold was written per paragraph with an LLM-like rewrite, so the selection unit is the paragraph.
- The gold follows EARS: 122 start "The …", 22 "When", 9 "Where", 7 "While". See [docs/requirement-frameworks.md](docs/requirement-frameworks.md).
- An LLM reading each paragraph ranks relevance far better than the feature model: AUC 0.975 against 0.836 out of fold.
- Inside the right sections the gold is selective, so routing by section has a low ceiling:
  an oracle choice of sections lifts paragraph F2 from 0.76 to 0.83, and rule-based gates on
  top of the LLM score lowered F2 on all four uploaded runs.
- A stronger model chooses paragraphs better (rows outside the gold: Sonnet 175, Opus 160,
  Fable 155) but misses as many gold rows on the paragraphs it chose (26 to 37). Those misses
  come from splitting less finely than the gold: one gold row per table row, list item or
  optional case. The rewrite prompt now asks for that.
- qwen3.5:9b relevance ranks no better than the decision model (AUC 0.78 to 0.84, see
  [docs/local-models.md](docs/local-models.md)), so local models are for the rewrite, not
  for relevance.

## Next

1. Score the split-rewrite prompt on dev (local judge, then one dev upload) against Fable's
   own rewrite on the same paragraphs.
2. Decide the Sunday mode and budget, and put the provider key in `brain/.env`.
3. Front bumper: review GTR 9 against R127 with Francisca, and replace silver labels with her
   corrections where she disagrees.
4. Deterministic gaps on bumper specs: R149 headlamp sections pass when the product has fog
   lamps (their headings are too long to count as titles), and impactor certification (R127
   Annex 6, GTR 9 §8) and R10 §7 pass although the labels say they are not cited.
5. Open points from the code review: semantic fidelity checks, table-qualified paragraph
   labels, quote-level page provenance.
