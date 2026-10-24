# Approach

How a product spec becomes the requirement list for the main goal. The worked example is `cases/dev-rear-lamp`: a new rear lamp for an M1 passenger car, with a position lamp, a stop lamp, a reversing lamp, a retro-reflector, and LED electronics.

The output is one JSON file. Each item is one engineering obligation, with the citation the scorer checks: regulation, **base** version, PDF page, and paragraph. See [CHALLENGE.md](CHALLENGE.md) for the schema. Paragraph extraction is in [pdf-extraction.md](pdf-extraction.md).

## What the score actually checks

Three levels, precision and recall at each. The organisers said missing an obligation matters more than including an extra one.

1. **Regulations.** The set of regulation numbers cited. A stop-lamp sentence taken from R7 does not count as the stop-lamp requirement in R148.
2. **Pages.** The set of `(regulation, version, page)` citations, against the base PDF. A correct paragraph rescues a page that is off by one. `tools/score_local.py` scores these two levels and ignores `text`.
3. **Requirements.** On upload, a model matches the list one-to-one against the golden list by meaning: same scope, condition, and constraint. This is why each item has to be one obligation, written so it stands alone.

## Pipeline

Three steps. An agent does the judgment in steps 1 and 3. A parser, not the agent, owns the citation.

### 1. Read the product

Input is the spec (`spec.md`) and, when present, the exploded view. Take what the product is, which vehicle it goes on, and which functions and parts it actually has.

For the rear lamp: new device, category M1, rear position, stop, reversing, retro-reflector, outer lens, LED on a PCB. No direction indicator, no fog lamp, no front lamp.

### 2. Choose the regulation files

Match that description against the 56 entries in `regulations/index.json` and a short card built once from each base PDF. The card is two passages, not the whole file:

- **Scope**, usually page 1. Which devices this regulation applies to.
- **Transitional provisions.** Whether this regulation still grants a new approval, and which regulation replaced it.

The agent returns the shortlist and opens only those base PDFs. It does not read the corpus. There are 5,532 pages across the files; a cover-to-cover read will not finish when the held-out case arrives, and it still picks the wrong file when two titles cover the same lamp.

The rear-lamp shortlist is R148 (light-signalling devices), R150 (retro-reflectors), R48 (installation), and R10 (electromagnetic compatibility, because the light source is an LED). The golden file has 190 requirements from those four and from no others.

### 3. Search the points inside those PDFs

Parse the shortlisted base PDFs into paragraphs with regulation, version, page, and paragraph label, as in [pdf-extraction.md](pdf-extraction.md). The agent then keeps or drops each paragraph against the product. A lamp with no blinker drops the direction-indicator paragraphs, even though they live in R148, which was correctly opened.

Each kept paragraph becomes one requirement per obligation:

- Keep the regulation's own sentence when it is already a complete "shall".
- Rewrite when the clause is a fragment or a continuation of a parent sentence, so the requirement stands alone. The style to copy is `cases/dev-rear-lamp/expected.json`: "shall", active voice where the source allows it.
- The citation stays the one the parser recorded. The agent does not invent page numbers.

Definitions, scope notes, and "the following" headers are not obligations.

## Why the regulation has to be chosen first

Searching every point in all 56 PDFs and keeping the sentences that resemble the product fails the regulation-level score. The same stop-lamp idea exists in R7 and in R148. They are different regulation numbers, versions, pages, and paragraphs. Returning the R7 point adds a regulation the answer does not contain and leaves the R148 citation missing. Returning both doubles the obligation, and the platform matches one-to-one, so the extra copy costs precision.

The file is the source of the point, not metadata attached to it. The index title is the metadata. The sentence, the paragraph label, and the PDF page exist only in the file, and the score checks that location.

## Consolidated regulations

Two different things are called consolidated.

**"Consolidated text of this version"** is the header on every PDF, including R7. Certivity folded the amendments of that one regulation into a single file. There is no second copy to choose. Cite that file, and cite its base version. A page from the `latest` PDF counts as a different page.

**A consolidated regulation** is a newer regulation number that absorbed several older ones. R148's introduction says it combined UN Regulations 4, 6, 7, 23, 38, 50, 77, 87, and 91. R150 combined 3, 27, 69, 70, and 104. At the merge, the technical requirements were copied across. The base versions in this pack are later series, so paragraph numbers, pages, and some requirements have since moved apart.

R7 is absent from the rear-lamp answer because it no longer grants a new approval. Paragraph 14.1 of the R7 base PDF (page 12): 24 months after R148 entered into force, contracting parties shall cease to grant approvals under R7. Paragraphs 14.2 to 14.4 keep R7 for extensions of old approvals and for replacement lamps fitted to vehicles already in use. The worked example is a new lamp, so its position-lamp and stop-lamp obligations are the ones in R148. The same handover is why reversing lamps come from R148 rather than R23, and retro-reflectors from R150 rather than R3.

Title match points the other way. R7 is titled "Position, stop and end-outline lamps" and R23 is "Reversing lamps". The card, not the title, is what selects R148.

## What each agent receives

| Step | Receives | Returns |
| --- | --- | --- |
| Choose the files | Product description, 56 index titles, one scope-and-transitional card per regulation | The shortlist of base PDFs |
| Keep the points | Parsed paragraphs from those PDFs only, each already labeled with regulation, version, page, and paragraph | One requirement per applicable obligation, citation unchanged |

Build the cards and the paragraph records once. Re-run only the two agent steps when the held-out spec arrives.
