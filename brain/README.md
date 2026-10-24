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
| `--threshold 0.2` | Override the paragraph cut-off (the blended LLM cut-off when an LLM is on). |

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

1. Pull the held-out case and check that `uv run python -m brain.ingest` has run.
2. Run deterministic first and keep it as the safety net:
   `uv run python -m brain.pipeline ../cases/heldout-front-bumper --no-llm --team-id team-XX -o out/heldout-det.json`
3. If an LLM is approved, run with it to `out/heldout-llm.json`.
4. Review the regulation list in the log and in the `regulations` field with Francisca. Rerun
   with `--include` / `--exclude` as needed. Check the per-regulation requirement counts, so no
   core regulation emits zero requirements.
5. Validate, upload a baseline early, then upload better variants. The last valid upload
   counts, uploads are limited to 5 per hour, and they close at 13:00.

## Evaluate

```bash
uv run python -m eval.score out/dev.json                 # F2 at three levels against dev gold
uv run python -m eval.score out/x.json --expected path/to/expected.json
uv run python -m eval.suite --no-llm --tag note          # dev + synthetic cases, appends eval/results.csv (local)
uv run python -m eval.suite --no-llm --cases 'synth-a*'  # only the cases in ../synthetic/cases
uv run python -m eval.cached_relevance --since "..."     # score cached relevance answers mid-run
uv run python -m eval.gold_check                         # every dev gold citation resolves on its page
uv run python -m eval.synth                              # regenerate the Tier A synthetic cases
uv run python -m eval.relevance_check                    # LLM relevance vs decision model (paid calls)
```

The regulation and page levels reuse Certivity's `tools/score_local.py`, so they should match
the platform. **The requirement level is a lexical proxy** (`eval/judge.py`: token overlap,
one-to-one matching within a regulation, zero for opposite polarity, a penalty for mismatched
numbers). The platform uses an LLM judge, so treat the proxy as a relative signal between our
own runs until a dev upload calibrates it. `eval.suite` without `--no-llm` follows `BRAIN_LLM`
and makes paid calls for every case.

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
| 3 | `brain/features.py`, `brain/decide.py` | Paragraph features (product-term match in the heading path, sections about other devices, section kind, content, graph) feed a logistic regression fitted on the dev gold, with a threshold tuned for F2. TabPFN is optional (`--extra tabpfn`, `BRAIN_DECIDER=tabpfn`). |
| 3b | `brain/relevance.py` | LLM path: the strong model reads every candidate paragraph in document order, with its heading path and parent clause, and estimates P(cited). Geometric blend with the decision model (weight 0.7 on the LLM), cut-off 0.20, plus a floor of each selected regulation's top 6% so a product unlike the lamp still gets its core regulation. |
| 4 | `brain/rewrite.py` | Rewrites each paragraph as minimal-edit EARS requirements. Deterministic path: split at "shall", fold "However" into "except that", turn telegraphic lines ("In height: …") into shall-statements using the subject from the heading path. LLM path: few-shot EARS rewrite with the parent clause, so child items keep the parent's condition. |
| 5 | `brain/verify.py` | Base version only; every number must appear in the source paragraph or its ancestors; dedupe; Certivity's `validate.py`. |
| – | `brain/llm.py` | One interface for OpenAI, Anthropic and local OpenAI-compatible servers (Ollama): structured JSON output, or prompted and validated JSON where a local runner lacks it; timeouts and retries; an atomic disk cache. |

## Results on dev

Requirement F2 uses the lexical proxy. Everything here is tuned on this one case, so expect
less on the bumper.

| Run | n | Regulation F2 | Page F2 | Requirement F2 |
|---|---|---|---|---|
| Deterministic (`--no-llm`) | 778 | 1.000 | 0.723 | 0.364 |
| LLM, bulk-tier relevance | 488 | 0.952 | 0.851 | 0.577 |
| LLM, strong-tier relevance | 409 | 0.952 | 0.877 | 0.624 |

The strong-tier run selected R148, R150, R10, R48 and R26. R26 is the only regulation that isn't
in gold. Its 17 rows cost about 0.01 of requirement F2 on dev, but R26 §6.5 covers bumpers, so
it stays for the held-out case.

These runs used the earlier relevance prompt with cut-off 0.10 and the earlier judge. The
current domain-neutral prompt with cut-off 0.20 is measured at paragraph level only: F2 0.75 at
recall 0.94, against 0.73 for the earlier prompt. The rewrite prompt with parent clauses hasn't
been run end to end yet.

On the five Tier A synthetic cases, the LLM path scores requirement F2 0.40 to 0.63, against
0.34 to 0.40 for the deterministic path. Tier A cases are ablations of the same dev gold (see
`eval/synth.py`), so they test function-aware selection, not transfer to a new product. The
plain bumper smoke test (`data/synthetic/bumper-plain`) selects R42, R127, R26 and GTR 9, with
10 R42 requirements from §6.1.1 to §6.1.5. `eval.suite` logs each run to `eval/results.csv`, which stays local.

Saved outputs in `out/` (all with `team_id` `team-00`; set yours before uploading):

| File | Run |
|---|---|
| `dev-rear-lamp.json` | Dev, deterministic. 778 requirements, the first row of the table above. |
| `dev-llm.json` | Dev, LLM with strong-tier relevance (cut-off 0.10). 407 requirements, page F2 0.877, requirement F2 0.626. Valid; the candidate for a first platform upload. |
| `bumper-plain.json`, `bumper-sensors-fog.json` | Bumper smoke tests, deterministic (before the negation fix in the spec parser). |
| `bumper-plain-llm.json`, `bumper-sensors-fog-llm.json` | Bumper smoke tests, LLM with strong-tier relevance (cut-off 0.10). |

## Findings that shaped the design

- Gold paragraphs are about 4% of all paragraphs in the four dev regulations, and 25–40% of the paragraphs in the sections for the product's functions. Picking the section is the main lever.
- 42 of the 190 gold requirements come from sentences without "shall" (R48's telegraphic style). The gold was written per paragraph with an LLM-like rewrite, so the selection unit is the paragraph.
- The gold follows EARS: 122 start "The …", 22 "When", 9 "Where", 7 "While". See [docs/requirement-frameworks.md](docs/requirement-frameworks.md).
- An LLM reading each paragraph ranks relevance far better than the feature model: AUC 0.975 against 0.836 out of fold.

## Next

1. One platform dev upload to calibrate the lexical proxy against the real requirement score.
2. Decide the Sunday LLM budget and mode: Claude credits, the OpenAI bulk tier, or deterministic.
3. Front bumper: review GTR 9 vs R127 and R26 with Francisca. Label 60 to 100 bumper paragraphs to check transfer.
4. Open points from the code review: semantic fidelity checks, table-qualified paragraph labels, quote-level page provenance.
