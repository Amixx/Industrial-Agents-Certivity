# Regulation graph

A spike on whether a graph built from the base PDFs helps find the golden paragraphs of `cases/dev-rear-lamp`. Regex and structure extraction only, no model calls.

## Verdict

The reference graph does not help recall at a useful precision cost. Following `parent` and `ref` edges one hop from half of the golden paragraphs adds 9 of the missing 60, at 115 non-golden paragraphs pulled in. Taking the next and previous paragraph in document order adds 13 at 87 pulled, and the whole page adds 39 at 368. The one structural expansion that keeps up with document order is siblings, the paragraphs under the same parent, and those are neighbouring paragraphs by another name.

What the graph is good for is elsewhere: `supersedes` edges explain the regulation choice (R148 replaces R6, R7 and R23, R150 replaces R3), and `ref` edges name the definition or annex a requirement leans on, which is context for rewriting it, not another requirement.

## What was built

```
uv run --with pymupdf python scripts/reggraph/build.py    # all 56 base PDFs, about 30 s
python3 scripts/reggraph/measure.py                       # tables below, data/reggraph/metrics.json
python3 scripts/reggraph/view_data.py                     # data for /dev/reggraph
```

- `scripts/reggraph/parse.py` extends the paragraph parser in `scripts/diff_regulation.py` with annex parts (`Annex 6 Part 4 3`), table captions under the paragraph that announces them (`5.1.4.4.1. Table 3`), annex and part heading nodes, and the `Introduction`. All 121 distinct golden labels exist, each on the cited page.
- `scripts/reggraph/edges.py` finds `parent` (label hierarchy), `ref` ("paragraph 5.4.", "paragraphs 6.1. to 6.3.", "Annex 4", "Annex 5, paragraph 2", "paragraph 3 of Part 1 of Annex 4", bare numbers inside an annex tried against that annex first), `xref` ("UN Regulations Nos. 53, 74 and 86", "paragraph 5.5.2. of UN Regulation No. 48") and `supersedes`. Every edge except `parent` keeps its evidence span.
- `data/reggraph/<regulation>.json` holds nodes (label, page, and the first 300 characters for R148, R48, R150, R10 and R7) and edges; `index.json` holds per-regulation stats, the cross-regulation counts and the supersedes edges. 5.4 MB over 57 files.
- R51 parses to no paragraphs and R49 to 14: their layout differs from the rest and was left alone.

## Graph stats

Across all 56 regulations: 23,886 nodes, 10,095 references found, 92.8% resolve to an existing paragraph exactly and 95.5% to it or its nearest existing ancestor. `refs found` counts mentions (a range counts its two ends), the `ref` column counts edges (a range expands to every paragraph in it).

| Regulation | Nodes | parent | ref | xref | supersedes | Refs found | Resolved exactly | Resolved incl. ancestor | Most referenced |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R10 | 837 | 790 | 292 | 12 | 0 | 334 | 92.5% | 92.8% | Annex 9 (14), Annex 6 (13), Annex 4 (11), 6 (8), Annex 13 (8) |
| R48 | 1202 | 1173 | 528 | 122 | 0 | 490 | 95.1% | 100% | 5.8.1 (25), 5.11 (13), Annex 5 (12), Annex 1 (11), Annex 9 (10) |
| R148 | 411 | 396 | 136 | 48 | 9 | 143 | 95.1% | 98.6% | 4.6 (12), 5 (9), Annex 3 (9), Annex 1 (8), 4.8 (7) |
| R150 | 540 | 522 | 263 | 22 | 5 | 265 | 92.5% | 98.1% | Annex 4 Part 1 (21), 5 (18), 4 (13), Annex 5 (11), Annex 6 Part 6 (9) |
| R7 | 247 | 227 | 92 | 34 | 1 | 90 | 95.6% | 100% | 6.1 (5), Annex 4 (5), Annex 2 (4), 7 (4), 6 (3) |

The most referenced targets are annexes (test procedures, communication forms) and section headers. Only one of the 25 is golden: R48 5.11.

## Connectivity of the golden set

121 distinct golden paragraphs in 2,990 paragraphs of R148, R48, R150 and R10, a base rate of 4.0%. How many golden paragraphs reach another golden paragraph:

| Edges | Within 1 hop | Within 2 hops |
| --- | --- | --- |
| parent or child | 16 (13%) | 82 (68%) |
| sibling | 69 (57%) | 69 (57%) |
| ref, either direction | 20 (17%) | 36 (30%) |
| parent, child or ref | 33 (27%) | 102 (84%) |
| baseline: next or previous paragraph | 53 (44%) | 72 (60%) |

Why references don't connect the set:

- 74 of the 121 golden paragraphs cite no other paragraph.
- The 98 `ref` edges that leave a golden paragraph land on another golden paragraph 15 times, on an annex 27 times and on other body paragraphs 56 times. Golden paragraphs cite definitions, marking rules and test procedures, and those are not obligations in the golden list.
- Of 29 cross-regulation references that name a paragraph, one joins two golden paragraphs: R148 4.6.1.2 cites R48 6.10.8.
- The 2-hop figure for parent, child or ref comes from going up to a shared section and back down, which is the sibling relation again.

## Expansion test

Simulate a retriever that found a random share of the golden paragraphs (seeds 0 to 19), expand one hop, and count golden paragraphs gained against non-golden paragraphs pulled in. Averages over the 20 seeds.

Found 50% (61 of 121):

| Expansion | Recall after | Golden gained | Non-golden pulled | Precision of pulled |
| --- | --- | --- | --- | --- |
| parent | 0.516 | 1.9 | 43.9 | 0.043 |
| children | 0.517 | 2.1 | 18.9 | 0.100 |
| parent + children | 0.533 | 4.0 | 62.8 | 0.061 |
| siblings | 0.690 | 22.9 | 131.1 | 0.149 |
| ref out | 0.524 | 2.9 | 32.4 | 0.081 |
| ref in | 0.523 | 2.8 | 23.3 | 0.107 |
| ref both | 0.547 | 5.7 | 55.6 | 0.092 |
| parent + ref out | 0.538 | 4.7 | 73.7 | 0.059 |
| parent + children + ref both | 0.577 | 9.3 | 114.5 | 0.076 |
| parent + children + ref both, 2 hops | 0.805 | 36.9 | 433.6 | 0.078 |
| siblings + ref both | 0.706 | 24.9 | 175.9 | 0.124 |
| baseline: next and previous paragraph | 0.611 | 13.4 | 86.8 | 0.134 |
| baseline: 2 paragraphs either side | 0.679 | 21.6 | 161.2 | 0.118 |
| baseline: same page | 0.824 | 39.2 | 367.8 | 0.096 |
| baseline: 8 paragraphs either side | 0.888 | 47.0 | 448.0 | 0.095 |

Found 25% (30 of 121):

| Expansion | Recall after | Golden gained | Non-golden pulled | Precision of pulled |
| --- | --- | --- | --- | --- |
| parent | 0.263 | 1.6 | 24.3 | 0.062 |
| children | 0.263 | 1.6 | 8.4 | 0.159 |
| parent + children | 0.276 | 3.2 | 32.8 | 0.089 |
| siblings | 0.411 | 19.4 | 77.6 | 0.200 |
| ref out | 0.274 | 2.9 | 17.3 | 0.144 |
| ref in | 0.267 | 2.0 | 11.3 | 0.154 |
| ref both | 0.291 | 5.0 | 28.6 | 0.148 |
| parent + ref out | 0.287 | 4.5 | 40.9 | 0.098 |
| parent + children + ref both | 0.316 | 8.0 | 60.1 | 0.117 |
| parent + children + ref both, 2 hops | 0.533 | 34.3 | 262.4 | 0.116 |
| siblings + ref both | 0.436 | 22.4 | 102.4 | 0.180 |
| baseline: next and previous paragraph | 0.335 | 10.2 | 44.4 | 0.188 |
| baseline: 2 paragraphs either side | 0.394 | 17.4 | 86.9 | 0.167 |
| baseline: same page | 0.569 | 38.6 | 230.7 | 0.143 |
| baseline: 8 paragraphs either side | 0.679 | 51.9 | 287.9 | 0.153 |

Reading the tables:

- Every expansion beats the 4% base rate, so nothing here is noise. But no expansion along `parent` or `ref` edges beats a document-order window of similar size: one hop of parent, children and refs gains 9.3 for 115 pulled where the next and previous paragraph gain 13.4 for 87, and two hops gain 36.9 for 434 where the same page gains 39.2 for 368. Siblings are on par with a window of 2 either side.
- `ref` edges are fairly precise (0.09 to 0.15) and small: about 5 golden paragraphs gained from either starting point. Adding them to siblings adds 2 to 3 golden paragraphs for 25 to 45 more pulled.
- The simulation drops golden paragraphs at random. A real retriever misses in clumps (a whole section about a function it didn't recognise), and locality helps less there. References might do relatively better on that kind of miss; this test can't show it.

## Cross-regulation references

`xref` edges between the four golden regulations and the superseded ones (counts of references):

| From \ to | R10 | R48 | R148 | R150 | R7 | R6 | R23 | R3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R10 |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| R48 | 0 |  | 24 | 10 | 5 | 3 | 3 | 6 |
| R148 | 0 | 18 |  | 0 | 2 | 2 | 2 | 0 |
| R150 | 0 | 6 | 0 |  | 0 | 0 | 0 | 2 |
| R7 | 0 | 6 | 1 | 0 |  | 4 | 3 | 1 |
| R6 | 0 | 3 | 1 | 0 | 7 |  | 2 | 0 |
| R23 | 0 | 3 | 0 | 0 | 4 | 2 |  | 1 |
| R3 | 0 | 4 | 0 | 0 | 2 | 1 | 1 |  |

- R48 and R148 reference each other heavily, and R48 points to R150 and to the older device regulations it still accepts.
- Nothing references R10. R148 mentions electromagnetic compatibility once, in a footnote to 4.7.2.3 ("relevant to the vehicle type"), without a regulation number, and the parser drops footnotes as small type. R10 has to come from the product (LED electronics), not from links.

`supersedes` edges found:

| Newer | Older | Where it is stated |
| --- | --- | --- |
| R148 | R6, R7 | R6 14.1 and R7 14.1: 24 months after R148 enters into force, cease to grant approvals |
| R148 | R4, R6, R7, R23, R38, R50, R77, R87, R91 | R148 Introduction: "combines the provisions of individual UN Regulations Nos. ..." |
| R150 | R3, R27, R69, R70, R104 | R150 Introduction |
| R149 | R19, R98, R112, R113, R119, R123 | R149 Introduction |

R7 does point to R148: once in 14.1, which is the supersession. R3 and R23 say nothing about their successors in their own base PDFs, so the old-to-new direction is only visible from the newer regulation's introduction. Of the names in those introductions, R4, R50, R77, R87, R91, R27, R69, R70, R98, R112, R113 and R119 are not in the corpus.

## Recommendation for the pipeline

- Don't add graph expansion to the retrieval step. If a recall safety net is wanted, offer the agent the rest of a kept paragraph's parent section (its siblings) or page for keep or drop. It's simpler and it wins on these numbers.
- Keep `ref` edges as context: when a kept paragraph says "as defined in paragraph 3.3.4.2." or "according to Annex 8", attach that text so the rewritten requirement can stand alone. Don't cite the referenced paragraph as a requirement of its own.
- Put the `supersedes` edges on the regulation cards of step 2. The R148, R149 and R150 introductions and R6 and R7 14.1 give the handover deterministically, including for R23 and R3, whose own text is silent.
- Reuse `scripts/reggraph/parse.py` for the paragraph records: it produces the golden label style, including parts and tables, on the right page for all 121 golden labels.
- Regulation choice for R10 needs the product's features (electronics, EMC), since no cross-reference leads there.

## View

`/dev/reggraph` draws one regulation as an arc diagram: paragraphs along an axis in document order, `ref` edges as arcs, golden paragraphs in mint. It makes the finding visible: golden paragraphs sit in clumps, and most arcs from them run to annexes and headers outside the golden set.
