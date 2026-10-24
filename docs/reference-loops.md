# Reference loops in the regulations

Where a paragraph refers back to itself, either directly or through a chain of references, within one regulation or across regulations. Measured over all 56 base PDFs with the parser and reference resolver in `scripts/reggraph/`, 2026-10-24.

## How it was counted

- Paragraph records and references come from `scripts/reggraph/build.py`. References are numeric ("paragraph 6.2.6.1.2.", "paragraphs 6.13. to 6.15.", "Annex 7", "paragraph 4.6.1.4. of UN Regulation No. 148").
- `scripts/reggraph/edges.py` skips references from a paragraph to itself. For this count those two checks were removed and the graphs rebuilt into a scratch folder.
- A loop is a set of paragraphs that can all reach each other by following references (a strongly connected component).

## Numbers

| Kind | Count | Across regulations |
| --- | --- | --- |
| Paragraph refers to itself | about 45 | n/a |
| Two paragraphs refer to each other | 97 pairs | 2 |
| Three or more paragraphs in a loop | 23 | 1 |

- **Self-references.** A first count gave 453. 406 of those were annex titles ("Annex 1 Examples of approval marks") read as a reference to the annex itself. The real ones mostly point at their own sub-item or repeat their own number, for example R100 Annex 9G 3.2.2 ("the charging specified in paragraph 3.2.2.(b)") and R162 4.4.1 ("the circle prescribed in paragraph 4.4.1."). Harmless.
- **Pairs.** The usual pattern is a requirement and its test procedure. GTR 9 5.2.1 says "when tested in accordance with paragraph 7.3", and 7.3 says it applies "with respect to the requirements of paragraph 5.2.1".
- **Longer loops.** The largest are 9 paragraphs: R100 5.2.3 with 6.13 to 6.15.4.4 (warnings and the events that trigger them), and R107 Annex 3 7.7.x. R48 has 6 loops, R83 6, R152 4.
- **Across regulations.** Both pairs involve R48 6.5.8, the direction-indicator tell-tale: one with R148 4.6.1.4 and one with R6 6.2.2. They form the single cross-regulation loop.

## Example 1: across regulations, R48 6.5.8 and R148 4.6.1.4

- **R48 6.5.8** (installation, page 44) requires the operating tell-tale for direction-indicator lamps, and says it "shall be activated by the signal produced according to" paragraph 6.2.2. of R6, paragraph 5.6.3. of R148 (00 series), paragraph 4.6.1.4. of R148 (01 series), or another suitable way.
- **R148 4.6.1.4** (device, page 11) defines that signal: "A signal for activation of the tell-tale prescribed in paragraph 6.5.8. of Regulation No. 48 or paragraph 6.3.8. of Regulation No. 53 shall be produced" when a light source fails or the intensity falls below the minimum.

The vehicle rule says the tell-tale is driven by the lamp's signal; the lamp rule says the signal exists to drive the vehicle's tell-tale. R48 6.5.8 and R6 6.2.2 refer to each other the same way.

## Example 2: inside one regulation, R48 6.2.6.1.1 and 6.2.6.1.2

- **6.2.6.1.1** sets the initial downward inclination of the passing-beam cut-off, specified by the manufacturer to within 0.1 per cent and "within the range defined in paragraph 6.2.6.1.2."
- **6.2.6.1.2** defines that range as limits by mounting height, measured "starting from the initial downward inclination value set by the vehicle manufacturer as prescribed in paragraph 6.2.6.1.1."

Each paragraph needs the other: the first takes its range from the second, and the second measures from the first's value.

## What it means for the pipeline

- **Keep loop partners together.** When a paragraph is kept, the paragraphs it loops with are the context its requirement needs to stand alone, and usually belong in the answer too.
- **Track visited paragraphs when following references.** Loops are real, so recursive expansion without a visited set does not terminate.
- **Cross-regulation loops mark handovers between installation and device rules.** For lighting that is R48 with R148 and R6. The rear-lamp case has no direction indicator, so this loop is out of scope there, but a product with one would need both sides.
