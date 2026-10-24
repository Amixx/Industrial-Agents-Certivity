# Industrial Agents × Certivity

Entry for the Certivity challenge at the Industrial AI hackathon.

- Brief: [docs/certivity-challenge-brief.pdf](docs/certivity-challenge-brief.pdf)
- Official challenge repo: <https://github.com/Certivity/industrial-ai-hackathon>, merged in at the repo root like a fork, with its README at [docs/CHALLENGE.md](docs/CHALLENGE.md). Its data is licensed for this hackathon only, so keep this repo private.
- The regulation PDFs are committed under `regulations/pdf/` and `subgoal/dev/`, because the download links expire after the event.

```bash
git remote add upstream https://github.com/Certivity/industrial-ai-hackathon   # once per clone
git pull upstream main                          # Sunday morning: brings in the held-out case
python3 tools/fetch_regulations.py              # then fetch the held-out case's PDFs
```

## The task

**Main goal (required, decides the ranking).** Input: a product spec (`spec.md`) and/or an exploded-view image. Output: one JSON file listing every engineering requirement the product must fulfil under UN Regulations. Each requirement cites `regulation` + `version` + `page`, with `paragraph` optional but recommended. Test cases are optional and not scored.

**Sub-goal (optional).** Input: requirements derived from an old regulation version, plus the old and new PDFs. Output: a list of `modified` / `removed` / `added` changes, each with a `reason` and a `source.page`.

You submit outputs, not code. Certivity never runs our code.

## Scoring

Main goal, primary measure: precision and recall against Certivity's golden set at three levels.

1. **Regulations**: the set of distinct regulations cited, compared with the expected set.
2. **Pages**: the set of distinct `(regulation, version, page)` triples. A page counts if **either the page or the paragraph** matches. Paragraph labels are normalised for case, spaces, commas and a trailing dot, so a page that is off by one is rescued by a correct paragraph. Always fill in `paragraph`.
3. **Requirements**: each requirement is matched one-to-one with an expected one on meaning (same scope, condition and constraint), judged by a model on the platform.

Secondary measure: the UI, judged by the jury. Finalists pitch on Sunday from 15:00.

Sub-goal: recall of the flagged requirements, plus accuracy of each stated change.

Platform rules:
- 5 uploads per hour per challenge; a file that fails validation doesn't count against that.
- On the held-out case, **the last valid upload counts, not the best one**. Don't upload a worse file at the end.
- Validate before uploading: `python3 tools/validate.py out.json`
- Score the worked example locally at the regulation and page levels: `python3 tools/score_local.py out.json`

## What's in the data

- `regulations/index.json`: the **56 citable regulations** (UN R3 … R175, plus GTR 9). Each has a `base` version, and most also have a `latest` version. **The main goal must cite the base version.** A page from the latest PDF counts as a wrong page. The sub-goal is base vs latest.
- `cases/dev-rear-lamp/`: the worked example (a rear lamp for an M1 vehicle) with its full expected answer:
  - **190 requirements from just 4 regulations**: R148 (63), R48 (56), R150 (39) and R10 (32).
  - About 53 distinct pages, every requirement has a paragraph, and none has a test case.
- `subgoal/dev/`: R175 (ACPE) with 94 old requirements. The expected answer has 24 changes: 17 added, 6 modified, 1 removed.
  - Each `reason` is phrased mechanically, e.g. *"Paragraph 5.1.2 … was amended: 'X' was added"*. That points to a paragraph-level diff of the old and new text.

## Takeaways for our approach

- **Picking the regulations is the first and cheapest win.** The rear lamp cites the new consolidated regulations: R148 for light-signalling devices and R150 for retro-reflectors. It does **not** cite the legacy ones (R7 position/stop, R23 reversing, R3 retro-reflectors), even though they're in the index and match by title. Add the installation regulation (R48) and EMC (R10, because the lamp has LED electronics). Citing the legacy regulations would cost precision at every level.
- **The answer is close to an extraction of the regulation's own "shall" sentences**, lightly rewritten into standalone obligations: one obligation per requirement, at paragraph granularity. A pipeline of parsing the PDFs into paragraphs, finding the applicable sections, then splitting out "shall" statements should get high recall. The hard part is precision: dropping paragraphs about lamp types the product doesn't have, such as fog or direction-indicator lamps in R48 or R148.
- **Page numbers are PDF pages** of the base file, not the printed page labels. Check how the expected pages line up with the PDF before trusting any page offset.
- **The held-out case lands on Sunday morning.** Build the pipeline to be general (spec + image in, JSON out) and re-run it fast. Keep the dev case as the regression test with `score_local.py`.
- **For the sub-goal, diff paragraph by paragraph.** Align old and new paragraphs by number, diff the text, and map each changed paragraph to the old requirements that cite it. Paragraphs that are new and contain "shall" become `added` changes.

## Requirement engine (`brain/`)

`brain/` turns a spec and exploded view into the submission JSON: product profile, regulation
selection, paragraph relevance, EARS rewrite, validation. Details, options and the Sunday
runbook are in [brain/README.md](brain/README.md).

```bash
cd brain
uv sync --extra llm                                              # once
uv run python -m brain.ingest                                    # parse the regulation PDFs (about 10 s)
uv run python -m brain.pipeline ../cases/dev-rear-lamp --no-llm  # writes out/dev-rear-lamp.json
uv run python -m eval.score out/dev-rear-lamp.json               # F2 at three levels
```

Without configuration it runs deterministically with no network calls. LLM steps run only when
`BRAIN_LLM` is set in `brain/.env` (gitignored), because a strong-model run costs real money.

## Development

```bash
cd web/backend && uv run uvicorn app.main:app --reload   # API on :8000
cd web/frontend && bun run dev                       # UI on :5173, proxies /api and /pdfs to :8000
```

Code quality: `make check` runs ruff, ruff format, mypy (backend and brain) and Biome,
svelte-check (frontend) without changing files. `make fix` applies the ruff and Biome fixes.
`make test` runs the brain tests. Run `uv sync` in `brain/` once first.

Docker (also what Render deploys via `render.yaml`):

```bash
docker build -t certivity .
docker run --rm -p 8000:8000 certivity   # UI and API on :8000
```
