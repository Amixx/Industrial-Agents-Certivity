# What can be deterministic

The aim is to put as much of the pipeline as possible into deterministic code, and to use a language model only where code can't decide. Deterministic steps are reproducible and cheap, they run locally, and every decision is traceable. "Why was regulation X excluded" then reports the rule that fired, not generated text. The organisers also said that between equal scores they prefer a solution that is light and runs on the user's machine.

## Step by step

| Step | Deterministic | Model only for |
|---|---|---|
| PDF → paragraphs, pages, hierarchy, cross-references | All of it: label regex, page headers, `paragraph X` / `Annex N` references (see [pdf-extraction.md](pdf-extraction.md)) | Nothing |
| Product profile | The spec has a fixed template (Product Type, Vehicle Category, Function, Main Parts, Materials). Parse the markdown | The exploded-view image, only when the spec lacks parts |
| Regulation selection | Vehicle-category filter (M/N vs L, from each regulation's scope), a supersession table (R148 replaces R6/R7/R23/R38/…, R149 replaces R19/R98/R112/R123, R150 replaces R3/R104), device names matched against regulation titles and scope | Regulations whose scope the rules leave undecided |
| Section routing | Section headings name the device or feature ("6.7 Stop lamp", "6.10 Rear position lamp", "6.5 Bumpers", "5.1 Legform test to bumper"). Match against the spec's parts with a small synonym list | Parts that no heading matches |
| Paragraph relevance | Keep the regulation's general sections plus the routed device sections. Drop administrative paragraphs by their subject ("The Contracting Party…", "The Technical Service…", "application for approval"). Keep marking and labelling | Borderline paragraphs, if the harness shows a gain |
| Obligation extraction | Split into sentences containing "shall"; split lettered lists; fold "This condition shall not apply…" into the sentence before it; add "of the <device>" from the section heading | Fixing the subject of awkward sentences |
| Exclusion reasons | Generated from the rule that fired: "superseded by R148", "applies to L-category vehicles only", "no section for any part of this product" | Nothing |
| Sub-goal diff | Paragraph diff between versions. The golden reasons follow a fixed pattern ("'X' was added", "'A' became 'B'"), so template them | Nothing |
| Test cases (optional) | A template from the extracted value, unit and condition | Optional polish |
| Evaluation | The regulation and page levels (`tools/score_local.py`) | The requirement-level judge, which compares meanings |

## Evidence from the dev case

- **Routing works on headings.** In R48 the golden answer cites the general sections 5.x, plus exactly 6.4 Reversing lamp, 6.7 Stop lamp, 6.10 Rear position lamp and 6.14 Rear retro-reflector. Those are the product's parts. None of the other 24 device sections is cited.
- **The text is near-verbatim.** Of the 190 golden requirements:
  - 189 use "shall", and none uses "must" or "should".
  - 55 keep the source's passive voice.
  - 40 keep "paragraph X" references unresolved.
  - The rewrites are limited to an explicit subject, context from the section heading, and folded exceptions.

## Strategy

1. **Build the fully deterministic pipeline first** and score it with the harness, per stage, with the correct answer fed in upstream.
2. **Add a model only at the step where the harness shows it gains points.**
3. **The key experiment:** score verbatim "shall" sentences against rewritten ones at the requirement level. If verbatim scores close, models shrink to narrow fallbacks.
4. **Guard against overfitting to lamps.** Write the rules against regulation structure (headings, scope, vehicle category), never lamp vocabulary, and check them on a mock front-bumper spec. Expected: R42, R26 (§6.5 Bumpers), R127 (§5.1 Legform test to bumper) and GTR 9.
