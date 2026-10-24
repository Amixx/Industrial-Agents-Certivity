# Open tasks before the held-out case

Each file in this folder is a prompt for one fresh agent session. Take one, paste it into a new
session, and work it to its acceptance criteria. The tasks are independent: each owns its own
files, so they can run in parallel without merge conflicts.

| File | Task | Owns | Status |
|---|---|---|---|
| [01-model-judge.md](01-model-judge.md) | Calibrate a model judge against the platform's dev scores | `eval/model_judge.py`, `eval/judge.py` | open |
| [02-rewrite-granularity.md](02-rewrite-granularity.md) | Split obligations the way the gold does, with a strong model | `brain/rewrite.py`, `eval/rewrite_pass.py` | done on branch `kb-stack`, see Results |
| [03-selection-stack.md](03-selection-stack.md) | Fewer paragraphs outside the gold: Jev, LLM and decision model combined | `brain/relevance.py`, `brain/features.py`, `brain/decide.py`, `data/decision_model.json`, a new `brain/jev.py` | done on branch `kb-stack`, see Results |
| [04-bumper-regulations.md](04-bumper-regulations.md) | Decide the regulation list for every likely bumper spec | `brain/select_regs.py`, `data/bumper-labels/`, a new `docs/bumper-regulations.md` | open; `kb-stack` adds an obligation-base ranking and a light-source rule to `select_regs.py` |
| [05-subgoal.md](05-subgoal.md) | The sub-goal submission (15% of the jury score) | `scripts/diff_regulation.py` or a new `brain/subgoal.py` | open |
| [06-sunday-rehearsal.md](06-sunday-rehearsal.md) | Dry-run the whole Sunday path and freeze the configuration | the runbook in `brain/README.md`, `brain/pipeline.py` for wiring fixes only | open |

Paths are relative to `brain/` unless they start with `../`.

## Shared context (every prompt assumes it)

- **The event.** Certivity challenge, Industrial AI hackathon, Munich. The held-out case
  (`heldout-front-bumper`) lands Sunday 25 Oct at 08:00; uploads close at 13:00. On the
  held-out case the **last valid upload counts**, not the best. Uploads: 5 per hour. Jury:
  held-out score 40%, demo and UI 20%, sub-goal 15%, impact 15%, pitch 10%. Lighter, locally
  deployable solutions win ties.
- **The task.** Spec plus exploded view in; a JSON list of requirements out, each citing
  regulation, base version, PDF page and paragraph. Scored by F2 (recall weighted four times)
  at regulation, page and requirement level. The requirement level is a one-to-one match by
  a model judge on the platform: same scope, condition and constraint. See
  `../docs/CHALLENGE.md`.
- **Dev data.** One real case, `../cases/dev-rear-lamp` (190 gold requirements from R148, R48,
  R150, R10; 119 gold paragraphs out of about 2,900 candidates). Synthetic ablations of the
  same gold in `../synthetic/cases/` and `data/synthetic/tierA-*`. Silver bumper labels
  (Opus-made, calibrated on the lamp gold) for R42, R26, R127 and GTR 9 in
  `data/bumper-labels/`: the only evaluation data for a product that is not a lamp.
- **The engine.** `brain/pipeline.py`: spec profile, regulation selection, paragraph
  relevance (decision model blended with an LLM score), rewrite into requirements, verify,
  validate. Read `README.md` first, then `docs/jev.md` and `docs/local-models.md`.

## Platform scores on dev (24 Oct)

| File | Rows | Requirement P / R / F2 | Matched of 190 | Cost |
|---|---|---|---|---|
| `../out/rear-lamp-deterministic.json` | 778 | 0.138 / 0.563 / 0.348 | 107 | $0 |
| `out/dev-upload.json` (gpt-5.5 relevance, gpt-5.4-mini rewrite) | 407 | 0.356 / 0.763 / 0.621 | 145 | not tracked |
| `../out/rear-lamp-sonnet.json` | 344 | 0.407 / 0.737 / 0.634 | 140 | $3.08 |
| `../out/rear-lamp-opus.json` | 338 | 0.423 / 0.753 / 0.651 | 143 | $6.36 |
| `../out/rear-lamp-fable.json` | 332 | 0.449 / 0.784 / 0.682 | 149 | $16.52 |
| `../out/rear-lamp-qwen-split-rewrite.json` (qwen3.5:9b rewrite of Fable's paragraphs, first split prompt) | 446 | 0.298 / 0.700 / 0.551 | 133 | $0 |

The leader is at 0.762 (recall 0.895, about 360 rows). Details, provenance and costs are in
`../out/README.md`.

**Where Fable loses** (`uv run python -m eval.errors ../out/rear-lamp-fable.json`):
- 155 of its 332 rows come from paragraphs outside the gold and match nothing. Dropping them
  all would lift the local judge from 0.646 to 0.752. That is task 03.
- 34 gold rows are missed on paragraphs it did cite, because it splits less finely than the
  gold (one gold row per table row, list item or optional case). That is task 02.
- 15 gold rows sit on paragraphs it never cited.

A stronger model mostly improves selection: rows outside the gold go from 175 for Sonnet to
155 for Fable, while the misses on cited paragraphs stay at 26 to 37 for every model. So a
bigger model does not fix granularity; the prompt has to.

## Rules for every task

1. **No paid call without approval.** Before any paid run, write down the token count, the
   price and the number of repeats, and get a yes from the repo owner. List prices per million
   tokens: Sonnet 5.5 $2 in / $10 out, Opus 5.5 $4 / $20, Fable 5.1 $10 / $50, Jev $0.042 input
   only. Check Grok's price before using it. LLM responses are cached in `data/cache/llm/`, so
   reruns are free. `BRAIN_LLM` is unset by default; never put it in `.env`.
2. **No overfitting.** A change is accepted only if it helps dev **and** does not hurt the
   silver bumper labels (`uv run python -m eval.transfer` for the decision model) or the
   synthetic suite (`uv run python -m eval.suite --no-llm`). Report learned models leave one
   regulation out, never in-sample. Never put dev gold text in a prompt or a few-shot example;
   three examples that did were removed on 24 Oct.
3. **Measure, then claim.** Every result goes in your task file under "Results", with the
   command, the configuration, the commit and the numbers. Every dev upload goes into
   `../out/README.md` with its platform score.
4. **Checks before every commit:** `uv run pytest -q`, `uv run ruff check .`,
   `uv run ruff format --check .`, `uv run mypy`. Commit straight to `main`; pull first, never
   force push. Follow `../DESIGN.md`, including its list of AI-isms, in docs and commit messages.
5. **Stay in your files.** If you need a change in a file another task owns, write it down in
   your task file and tell the team instead of editing it.
6. **Freeze at 02:00.** After that only task 06 changes the engine, and only to fix the
   Sunday path.

## Tools

| Command | What it does |
|---|---|
| `uv run python -m eval.score <file>` | F2 at three levels; the requirement level uses the local lexical judge |
| `uv run python -m eval.errors <files>` | Where a file loses points: rows outside gold paragraphs, misses on cited and uncited paragraphs |
| `uv run python -m eval.rewrite_pass <source> <out> [--provider ...]` | Rewrites the paragraphs a submission cites with the current prompt, so a rewrite change is measured with selection held constant |
| `uv run python -m eval.transfer` | Decision model on dev (leave one regulation out) and on the silver bumper labels |
| `uv run python -m eval.suite --no-llm` | Deterministic run on dev and every synthetic case |
| `uv run python -m eval.model_judge <file>` | Model judge through `claude -p` (task 01 calibrates it) |
| `uv run python ../tools/validate.py <file>` | The platform's own format check |

The local lexical judge finds 4 to 9 fewer matches than the platform on the Claude and gpt
rewrites, but 5 more on verbatim text and 4 more on qwen's short split rows. Its error depends on
the writing style, so it cannot compare two rewrite styles: use a dev upload for that until
task 01 delivers a calibrated judge.
