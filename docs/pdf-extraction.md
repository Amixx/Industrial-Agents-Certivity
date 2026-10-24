# PDF extraction

How to turn the regulation PDFs into paragraph records (regulation, version, page, paragraph label, text): what the Certivity PDFs look like, and what carries over from the PDF work in `sl26_g2_unifiedsearchengine` (its decisions 070 and 078, `eval/pdf-pages`, `eval/pdf-text` and the 2026-10-17 chunking survey).

## The Certivity PDFs, measured

Run with PyMuPDF and pikepdf over everything in `regulations/pdf/` and `subgoal/dev/`, 2026-10-24.

- **Every file has a clean text layer.** All 94 files were rendered from text by Chrome's Skia PDF backend, not scanned: 5,532 pages at about 2,000–3,000 characters a page. The 33 pages with under 50 characters are figure pages or near-empty annex endings.
- **No broken characters:**
  - The 56 base PDFs contain no U+FFFD and no ligature codepoints, and only 2 control characters.
  - Fonts are plain Times New Roman and Helvetica.
  - So the failures `sl26_g2_unifiedsearchengine` hit (below) don't happen here.
- **Page numbers are PDF pages.** Every page has a header line `UN R148, version 1.6.0 | page 10 of 48`, so `source.page` is the PDF's own page number. For all 190 expected requirements in `cases/dev-rear-lamp`, the cited paragraph label appears on the cited page.
- **Paragraphs start with their label at the left margin:** `6.19.7.3. The automatic operation …`. List items start with `(a)`, `(b)` and so on. The reading order from PyMuPDF's blocks is clean.
- **All 56 base PDFs are tagged.** They carry a structure tree with roles `P`, `H1`/`H2`, `Table`/`TR`/`TD` and `Figure`. For example, R48 has 44 tables and R148 has 25. Figures have no alt text.
- **No bookmarks and no links.** The outline is empty, so section structure has to come from the paragraph labels.

## What `sl26_g2_unifiedsearchengine` tried

Its stack was Extractous 0.3 (Apache Tika and PDFBox) in Rust, plus hayro for rendering. The lessons below are independent of the library.

**Worked**
- **Page boundaries from the extractor's own page markers.** Tika's XHTML wraps each page in `<div class="page">`, and the text inside equals the plain-text output byte for byte on 40 probed PDFs. The page starts recorded from those markers gave correct pages. PyMuPDF iterates pages natively, which gives the same result for free.
- **Store the text whole, with page-start offsets beside it, rather than one value per page.** Splitting into per-page pieces broke phrases that cross a page boundary: only 11 of 461 boundary phrases still matched. For us, the equivalent is to stitch a paragraph's text across the page break and cite the page where its label sits, which is what the expected answers do.
- **An independent reader as a check.** `align_pypdf.py` compared each page's words with pypdf's text of that page and its neighbours (Jaccard similarity on words). It caught any page drift. We can reuse the idea: check the corpus against the `page N of M` headers and the dev answers' paragraph-to-page pairs.
- **Small units, provenance first** (chunking survey):
  - Every unit keeps a pointer to its source: page and block, here page and paragraph label.
  - Context gets added on top, never in place of the source text.
  - A deterministic header ("Regulation / section heading / paragraph") beats LLM-generated context as a first step: it's cheap and can't invent facts.
- **Index small, return big** (small-to-big, parent and child). Match on small units, then return the surrounding unit for context. Here that means matching on an obligation or sentence and showing the whole paragraph.

**Didn't work**
- **Using Tika's per-page character counts to find page boundaries.** The counts drifted from the extracted text by up to 12,814 characters, because Tika counts before PDFBox adds word and line separators. No multi-page PDF lined up. Take boundaries from page iteration, never by summing counts.
- **Bookmarks as structure.** Tika appends bookmark titles after the last page with no page numbers. That's moot here, since the PDFs have no bookmarks.
- **Assuming tagged structure nests inside pages.** Tika's marked-content mode handles structure and pages separately and defers content that crosses pages. If we read the structure tree, for example for tables, we have to map each element back to its page ourselves, through the marked-content IDs in each page's content stream.
- **Replacement characters (U+FFFD).** They came from fonts whose ToUnicode maps glyphs to control characters, which lost ligatures ("Alster�eet"), and from embedded OCR layers. Stripping them hid the symptom without recovering text. As measured above, this doesn't happen in these files, but a one-line U+FFFD count stays in the corpus build as a guard.

## What this means for our parser

1. **PyMuPDF, page by page.** Drop the `UN R… | page N of M` header line, and use it to assert the page number.
2. **Split into paragraphs** with a regex on labels at the left margin: `^\d+(\.\d+)*\.\s`, annex headings `^Annex \d+`, and annex-local numbering under the current annex. That last part produces labels in the expected answers' style, like `Annex 10 2` or `Annex 9 3.1`.
3. **Each paragraph cites the page where its label sits.** Text runs on until the next label, across page breaks.
4. **Store the parent sections:** the chain of headings and parent labels, e.g. `6.19 Daytime running lamp > 6.19.7 …`. Later steps use it for filtering by relevance and as the deterministic context header.
5. **Store the cross-references found in the text** ("paragraph 3.3.4.2.", "Annex 13"). The organisers said regulations link to each other and we should follow those links. A reference to an annex or another paragraph is how test procedures get pulled in.
6. **Tables:** see the first decision below.
7. **Checks:**
   - Every expected `(regulation, version, page, paragraph)` in the dev answer exists in the corpus.
   - Every page's header number matches its index.
   - No U+FFFD anywhere.

## Decisions

- **Tables.** Requirements often sit in tables, such as candela values per angle. Options:
  - (a) Plain text only. The cells come out as loose lines, so the numbers survive but the rows don't.
  - (b) PyMuPDF's `find_tables()` on the pages that have them.
  - (c) Rebuild the tables from the structure tree with pikepdf, which gives exact rows and columns but needs work to map elements to pages.
  - Recommendation: (a) now, then (b) if the requirement-level score shows we're losing points on table values.
- **Language.** Python is the natural choice here: PyMuPDF and pikepdf, and Certivity's own tools are Python. Bun is the alternative for the rest of the pipeline, but every serious PDF library is in Python. Recommendation: Python, run through `uv`.
