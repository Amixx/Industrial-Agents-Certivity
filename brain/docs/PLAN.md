# Certivity challenge: winning plan

## Context

This is the Industrial Agents hackathon in Munich, 24–25 Oct 2026. It is Saturday afternoon. The held-out case (`heldout-front-bumper` plus a sub-goal pair) drops **Sun 08:00** and **uploads close 13:00**. Finalists pitch from 15:00. The repo has the official package (tools, schemas, the index of 56 regulations, all the PDFs, a dev case, a sub-goal dev case) but **no solution code yet**. The team works overnight, Sunday is hybrid (the agent produces the output and Francisca reviews it before upload), we do the sub-goal (Troy owns it), and the LLMs are Claude (credits plus personal keys) and OpenAI/Gemini.

How the jury weighs it: held-out score 40% (**F2**, so recall counts more, with recall as the tie-break; scored at the regulation, page and requirement levels), demo/UI 20%, sub-goal 15%, impact 15%, pitch 10%.

## What the data tells us (the facts that drive the design)

1. **The gold is a sparse, curated subset, not every "shall".** The rear lamp has 190 gold requirements from 4 regulations that together contain about 2,030 "shall"s: R148 63/250, R48 56/625, R150 39/441, R10 32/718. The gold IDs have gaps (G-0007 is missing, for example), which suggests the set was machine-extracted and then pruned by an expert.
2. **Section selection is the main precision lever.** R48 gold uses only §5 (general) plus the sub-sections for the functions the product actually has (6.4 reversing, 6.7 stop, 6.10 rear position, 6.14 rear retro-reflector). R10 uses only the ESA sections (§6, Annex 9, Annex 10). R148 uses §3 (markings), §4 (general), the matching §5.x sections, §6 and a few annexes.
3. **Regulation choice follows a pattern: new consolidated regulations beat legacy ones.** The gold has R148, R149 and R150, and none of the legacy R7, R23 or R3. The general rule is: device-approval regulation + installation regulation (R48) + EMC (R10) when the product has electronics.
4. **The requirement text is the regulation's own "shall" sentence**, made standalone with the subject spelled out ("The stop lamp shall emit red light.") and **split at one obligation per sentence**: a paragraph with two "shall"s gives two requirements, and enumerations are split too.
5. **Citations:** the page is the PDF page (the footer prints "page N of M", and the parsed text is clean). A citation counts if **either the page or the paragraph** matches, so always fill in `paragraph`, in the formats `5.4.2.3` and `Annex 6 Part 4 3`.
6. **F2 math decides the cut-off.** Including an item pays off whenever P(it is in gold) > F2*/5. If we expect F2 ≈ 0.6, include anything with more than a ~12% chance of matching. Sanity check on the dev numbers: 400 candidates at recall 0.75 gives F2 ≈ 0.62, while 250 candidates at recall 0.6 gives F2 ≈ 0.56. **Aim for about 1.5–2.5× the estimated gold size, ranked by relevance.**
7. **The sub-goal gold is machine-generated from a paragraph diff.** The reasons read like "Paragraph 5.1.4 … was amended: 'X' became 'Y'; 'Z' was added" and "Paragraph 6.6.1.1 is new …". Rebuilding that diff is very tractable. The dev answer has 17 added, 6 modified and 1 removed.

## Architecture (one pipeline, one output file for both the platform and the UI)

```
spec.md + optional image
  → [1] Product profile: parts, functions, vehicle category, electronics/sensors, conditional facts (e.g. plastic lens)
        mapped to regulation vocabulary through the DEVICE TAXONOMY (built from regulation definitions, e.g. R48/R148 §2)
  → [2] Regulation selection: scope check + graph hops + legacy-vs-new rule → P(applies) + "why included / why excluded"
        → human review gate (Sunday hybrid mode)
  → [3] Paragraph relevance: walk the graph from the sections for the product's functions (parents, refs, definitions) → candidates
  → [4] Obligation extraction: one shall per row → slot record → minimal-edit EARS text
  → [5] Decision model: P(in gold) per obligation → include if p > F2*/5 → expand graph refs from accepted rows, re-score once
  → [6] Verify: BASE version only, quote found on the cited page, dedupe, INCOSE/fidelity checks, validate.py
  → Output: JSON (plus extra fields: part, confidence, quote, rationale, graph path, test_case) + UI (highlights, exclusions)
```

This adopts the teammate's diagram (product profile → regulation selection → paragraph relevance over a graph → obligation extraction → JSON + UI with highlights and exclusions) as the team's shared architecture, with four additions: the **decision model and F2 cut-off** [5], the **verify** step [6], the **EARS renderer** [4], and the **review gate** [2].

**Offline, deterministic, pre-computed tonight:**
- **Corpus:** all 94 PDFs (56 base + 38 latest). `pdftotext -layout` per page → paragraph tree (numbering regex, Annex/Part tracking, footers stripped, tables kept with their paragraph, page spans) → `data/corpus/<reg>_<role>.jsonl`. Every row carries `role` and `version_label`. **Main goal reads base only**, since a page of the latest version scores as wrong. Latest is used for the sub-goal.
- **Regulation graph, built with regex, no LLM:** nodes are regulations, paragraphs, annexes, tables and defined terms. Edges are parent/child, "see paragraph/Annex X", "Regulation No. N" and defines/uses. Evidence it pays off: R148 §5.5 refers to "paragraph 4.6" (4.6.1.2 is gold) and to Annex 3 and Annex 8 (both gold). R48's links are counted as R148 ×21, R149 ×14, R150 ×9 against R7 ×3 and R23 ×3, so link frequency already points to the new regulations.
- **Device taxonomy:** terms mined from each regulation's definitions section ("stop lamp", "category S1", "rear retro-reflector", "bumper", "front protective device") plus their synonyms. It maps spec parts to regulation terms and sections without hand-tuning for lamps.
- **Embeddings** of every paragraph and scope section, from a small local model held in a numpy matrix. They are **features, not a top-k retriever**. No classic chunk RAG, because top-k caps recall and chunks break citations.

**Decision model [5]:** TabPFN over a feature table. Features: embedding similarities; section type (administrative, approval, definitions and transitional provisions are negative); graph distance from function sections; how often the paragraph is referenced; taxonomy-term hits; modality ("may" is negative); P(regulation); depth in the tree. Trained on the dev gold (190 positives against roughly 2,000 negatives) plus the Tier A/B synthetic cases. Calibrated probabilities make the F2 cut-off principled. It runs on a CPU, which fits the organizers' "light, local" tie-break.

**Models:** every LLM call goes through one provider-agnostic interface.
- **At runtime, local** (the tie-break story): a small LLM fills the slot records and does the rewriting; a small vision-language model reads the exploded view.
- **At build time, Claude / GPT / Gemini as teachers:** silver labels, the local judge, few-shot examples.
- On Sunday we upload whichever mode scores higher on dev. The demo shows the local mode.

### The teammate's "missing pieces", with how each is covered and who owns it
| Missing piece | How it is covered | Owner |
|---|---|---|
| Eval harness, F2 per level | `eval/score.py` (regulation and page levels via `score_local.score()`) plus local LLM judge with Hungarian matching | Vlad |
| Device taxonomy | Mined from definitions sections into graph nodes; the profile agent maps parts onto them | Vlad (mining) + Troy (mapping) |
| Legacy vs new | Rule plus graph signal (R48 link counts; "type-approved to R7 **or** R148" → prefer the newer series); Francisca checks | Troy + Francisca |
| Local models | Provider-agnostic interface; local vs cloud compared on dev F2 and runtime | Troy |
| Granularity | EARS experiment variants (enumerations, sentences with two shalls) | Vlad |
| Cross-refs | Graph edges plus the expansion loop in [5] | Vlad |
| Sub-goal diff | `subgoal/` with diffs pre-computed for all pairs | Troy |
| Bumper test | Tier B bumper variants plus a full dry run tonight; lamp-specific rules forbidden | Francisca + Vlad |

## Requirement-writing framework (organizers' suggestion)

### Decision: minimal-edit EARS, checked against INCOSE GtWR v4 rules

**Why EARS.** The dev gold already follows it. Of the 190 requirements, 122 start "The \<system\> shall", 22 "When", 9 "Where", 7 "While" and 1 "If … then". Some forced sentences ("While the approval marking … is replaced …") suggest the gold was converted mechanically. The platform judge matches on "same scope, condition and constraint", which are the three EARS slots: system name, While/When/Where/If clause, shall response. Writing in EARS lines our sentences up with the judge.

**Rendering rules for the `text` field:**
1. **One obligation per requirement.** Split at each "shall" or "shall not". Whether to split (a)/(b)/(c) enumerations is decided by the experiment below.
2. **Explicit subject from the heading path**: "5.5 Stop lamps › 5.5.7 Colour" becomes "The stop lamp shall emit red light."
3. **Condition first, with an EARS keyword:** When (event or test), While (state), Where (optional feature), If … then (failure). Keep the regulation's own "For …" and "In the case of …" phrasing when it reads better.
4. **Keep word for word:** numbers, units, tolerances, paragraph and annex references, and passive voice (the gold has 55 passive sentences, so don't force active voice).
5. **Modality filter:** emit "shall" and "shall not" only. "May" (permission) is gold only once out of 190.

**INCOSE GtWR v4 rules applied as code checks after rendering:** definite article "the" (R5); no pronouns (repeat the noun, as the gold does); no vague terms or escape clauses added by us; one thought per sentence; consistent units. Plus a **fidelity check**: the condition, numbers and units must all appear in the quoted source sentence. An INCOSE 2024 poster found LLM rewrites drop preconditions.

**Internal record:** the local LLM fills slots and Python renders the text, so the decision model, the UI, `test_case` and the export all reuse the same slots:
```
{modality, subject, condition_type: none|when|while|where|if, condition, response,
 values: [{quantity, min, max, unit}], exceptions, refs, source: {regulation, version, page, paragraph}, quote}
```
Prompting: few-shot from the dev gold (a 2026 MoDRE study found simple few-shot prompting best for template-based requirement generation).

### Experiment that confirms or overturns the decision (dev case, local judge plus 1–2 platform uploads)
- **A. Verbatim:** split per "shall", no rewriting (baseline and fallback).
- **B. Minimal-edit EARS** (chosen).
- **C. Full EARS + INCOSE rewrite** (active voice, fully normalized). Expected to drift from the gold.
- Granularity variants within B: split enumerations or not; split sentences with two "shall"s or not (13 gold sentences keep two).
- The variant with the best requirement-level F2 wins. If A beats B, switch the renderer and keep the record.

### Alternatives on file (in case we need to switch)
| Candidate | What it is | Use if / where |
|---|---|---|
| **Verbatim "shall" extraction** | Regulation sentence as is, only split | Fallback if any rewriting costs matches |
| **Full EARS + INCOSE** | Strict EARS with every INCOSE rule (active voice, no passive) | If the jury values requirement quality over matching the gold; UI "clean view" |
| **ISO/IEC/IEEE 29148:2018** | Standard behind INCOSE (necessary, unambiguous, singular, verifiable, …) | Conformance claim in the pitch; otherwise covered by the INCOSE checks |
| **Rupp / IREB boilerplate (MASTER)** | [condition] + system + shall/should/will + process verb + object | Drop-in replacement for EARS if German or IREB-trained customers prefer it (Francisca's market) |
| **Deontic / legal norm models** (Breaux semantic parametrization, LegalRuleML) | Obligation, prohibition or permission; actor, action, condition, exception | Already the basis of our internal record; extend it if we need exceptions or cross-references modelled formally |
| **Planguage** (Gilb) | Scale / Meter / Must / Plan for quantified limits | UI display of measurable limits (e.g. 4–17 cd); never the `text` field |
| **Gherkin** (Given/When/Then) | Test-scenario syntax | The optional `test_case` field, generated from the EARS slots |
| **ReqIF** (OMG) | Exchange format for DOORS, Polarion and similar tools | Export button plus an impact point in the pitch |

### Vlad's brain lives entirely in `vlad/`

Troy builds a competing brain in parallel and the better one wins. Nothing outside `vlad/` is touched. Nothing is committed: Vlad reviews and commits.

```
vlad/pyproject.toml            uv project (pydantic, numpy, anthropic, openai, tabpfn, scipy, jsonschema)
vlad/brain/models.py           Paragraph, Obligation, ProductProfile, Requirement (pydantic)
vlad/brain/ingest.py           PDF pages → paragraph tree with page spans → vlad/data/corpus/*.jsonl
vlad/brain/graph.py            parent / ref / regulation-link / definition edges
vlad/brain/obligations.py      rule-based shall splitter + slot record + EARS renderer
vlad/brain/llm.py              provider-agnostic client (Anthropic / OpenAI / local OpenAI-compatible) with disk cache
vlad/brain/profile.py          spec + image → ProductProfile
vlad/brain/select_regs.py      scope check + graph + legacy rule → P(applies) + rationale
vlad/brain/features.py, decide.py   feature table + TabPFN (fallback: logistic regression) + F2 cut-off
vlad/brain/verify.py           base-only, quote on page, dedupe, validate.py
vlad/brain/pipeline.py         CLI: python -m brain.pipeline ../cases/<case> -o out.json
vlad/eval/score.py, judge.py   3-level F2 (regulation and page via tools/score_local.py) + LLM judge
vlad/tests/                    pytest per step
```

Build order, each step atomic, tested and runnable: (1) project + models → (2) ingest + gold-citation check → (3) graph + reachability → (4) obligation splitter + coverage against gold → (5) eval harness → (6) profile + regulation selection → (7) features + decision model + cut-off → (8) EARS rewrite → (9) verify + end-to-end CLI → (10) synthetic Tier A.

## Evaluation harness (built before tuning anything)

- **Regulation and page level:** reuse `tools/score_local.py:score()` and add F2.
- **Requirement level:** a local LLM judge. For each gold requirement, take candidates from the same regulation within nearby paragraphs, ask the judge "same scope, condition and constraint?", run a one-to-one maximum matching (Hungarian), and compute P, R and F2. Cache the verdicts.
- **Calibrate the local judge against the platform:** upload dev outputs (5 per hour) and adjust until our numbers track the platform's.
- Every pipeline change is scored on dev plus the synthetic suite; results are logged to `eval/results.csv`.

## Synthetic datasets (three tiers, by how far we can trust them)

- **Tier A, ablations of the real gold (high trust, cheap).** Tag each of the 190 gold requirements with its function (rear position / stop / reversing / retro-reflector / general / EMC). Write variant specs that drop or swap functions, e.g. "stop lamp only (CHMSL)", "position + retro-reflector", "filament instead of LED → no R10". The gold for each variant is the filtered subset. This tests function-aware section selection against real expert labels.
- **Tier B, silver cases for new products (medium trust).** Front-bumper variants: plain bumper; with fog lamps; with DRL and direction indicators; with parking sensors or radar; with a tow-eye cover. Plus a headlamp and a front fog lamp. A separate, heavier labelling pipeline produces the labels: GPT or Gemini reads every paragraph, the labels mimic the gold style and sparsity, and Francisca spot-checks them. Use this tier mainly for regulation- and section-level metrics, not for wording.
- **Tier C, sub-goal pairs.** For every base/latest pair in the index (about 40), run our extractor on base to get `requirements_old`, then run the diff to get the changes. This tests robustness (renumbering, big series jumps such as R79 4.11→5.0) and **pre-computes the held-out sub-goal** if its pair is in the index.

## Front bumper: initial hypothesis (Francisca validates today)

- Core regulations: **R42** (front and rear protective devices, M1 low-speed impact, 9 pages), **R127** (pedestrian legform-to-bumper tests), **R26** (external projections).
- Watch out: **GTR 9** is the only GTR in the index, so it is either gold or a legacy-style decoy for R127, the same way R7 was a decoy for R148. Check the spec wording and compare variants with uploads.
- Only if the spec says so: integrated lamps → R48 + R148 (position, indicator, DRL, side marker) + R149 (fog lamp; not the legacy R19/R6/R7) + R150 (retro-reflectors); electronics or sensors → R10; AEB radar → R152 (M1/N1; not R131).
- Probably not: R94 (frontal collision, vehicle level) and R32 (rear).

## Who does what

| Person | Owns | Saturday deliverables |
|---|---|---|
| **Vladyslav** | Corpus, extraction, ranking, eval | `models.py`; ingest of all 56 regulations with page and paragraph spans checked against the dev gold; section selector; extractor; ranker with F2-tuned cut-off; eval harness with local judge; Tier A/B synthetic suite |
| **Troy** | Agent layer, API, sub-goal | Product-profile agent (spec + vision); regulation selector; orchestration and FastAPI SSE endpoint; optional MCP server ("Certivity corpus as tools", good pitch value); sub-goal diff + mapping, uploaded for `subgoal-dev`; diffs pre-computed for all pairs |
| **Imants** | Demo UI (20%) | Starts at once on mock data from `expected.json`. Upload spec and image → live pipeline stages → requirements grouped by part/regulation → **click any requirement and the PDF opens at the cited page with the sentence highlighted** (pdf.js) → exploded view with part hotspots linked to their requirements → review mode (accept/reject a regulation or section, which drives Sunday's hybrid flow) → sub-goal diff view → export JSON/CSV |
| **Francisca** | Domain, pitch, platform | Registers the team (team_id); front-bumper regulation hypothesis; tags the gold requirements by function (Tier A); writes bumper variant specs and spot-checks the silver labels (Tier B); pitch with the business case for Certivity (runs on their structured corpus, change monitoring); measured weaknesses for the "proof" part |

### Timeline

- **Sat → 16:00, foundations:** contracts, ingest, UI on mocks, sub-goal prototype, bumper hypothesis.
- **16:00–20:00, first end-to-end run on dev:** first dev upload to calibrate the judge; sub-goal-dev upload.
- **20:00–02:00, iterate on F2** across dev plus the synthetic cases; pre-compute all corpora and pair diffs; full bumper dry run with Francisca's review in the UI.
- **02:00–07:00, freeze:** sleep in shifts; record a fallback demo video.
- **Sun 08:00, runbook:** pull, then fetch → run the pipeline → **upload a valid baseline by about 09:00** (a safety net, since the last valid upload counts) → Francisca reviews the regulations and sections → upload variants that differ on uncertain regulations (e.g. GTR 9, R10), picked by our own judgment and the platform scores → sub-goal held-out upload → **final upload by 12:30, never a worse file at the end.**
- **Sun 13:00–15:00:** repo and demo submitted on the organizers' platform (R4), pitch rehearsal.

## What I (Claude) do right after approval

1. Write `docs/PLAN.md` (this plan, aimed at the team) and publish it as a private shareable page for the team.
2. Build Vlad's critical path: `pyproject.toml`, `models.py`, the ingest for all regulations, a check that our page and paragraph spans match the 190 gold citations, and the eval harness (F2 plus the local judge).
3. Run the gold analysis: what share of the "shall"s in each selected section is in gold. This sets the size and cut-off targets.
4. Save the framework research to `docs/research/requirement-frameworks.md`; implement the slot record, the EARS renderer and the INCOSE/fidelity checks; run experiment A/B/C on the dev case.

## Verification

- `python3 tools/validate.py out.json` on every output (it is a pipeline step).
- `python3 tools/score_local.py out.json` plus `eval/score.py` (three levels, F2) on the dev case and the synthetic suite; targets are set after the baseline.
- Ingest check: every gold `(regulation, page, paragraph)` resolves to a parsed paragraph whose text contains the requirement's key words.
- Platform: dev uploads calibrate the local judge; on Sunday the baseline upload must be accepted and scored.
- Sub-goal: `validate.py --requirements-old` plus the comparison against `subgoal/dev/expected.json` (recall of the flagged IDs, change-type accuracy).

## Risks

- One labelled case → overfitting. Keep the rules general (by function, not by lamp) and check on Tier A/B.
- Bumper spec ambiguity → hybrid review plus variant uploads.
- PDF tables and paragraphs that span pages → keep page spans and cite the page where the sentence sits.
- Upload limits → never spend the last slot on an experiment.
