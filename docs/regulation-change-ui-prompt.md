# Prompt: regulation change UI

Paste everything below the line into a new Claude Code session at the repo root.

---

Build the web UI for the challenge's sub-goal, regulation change. The user is a homologation engineer with a saved assessment for a car part, such as the rear lamp (`cases/dev-rear-lamp`) or the front bumper (`cases/heldout-front-bumper`). They upload a new version of a regulation PDF. The app runs it through our change engine and shows three things in turn:

- which cited regulations changed;
- what changed inside the regulation, paragraph by paragraph, like a git diff;
- how the assessment's requirements change: modified, removed or added.

They can follow the change through the existing process graph and then apply it to the assessment.

The result has to work as a live demo and must look right in a screen recording. It is the last 20 seconds of our product video (see `docs/product-video-prompt.md`, scenes 7 to 10).

Read `CLAUDE.md`, `DESIGN.md`, `docs/regulation-change.md` and `web/` before you start. Follow DESIGN.md exactly, including its list of AI-isms to avoid.

## What exists

- **The engine is done.** `brain/brain/subgoal/` is complete and tested: 100% flag recall, precision and change accuracy on the dev pair. Use `brain.subgoal.diff_assessment(old_pdf, new_pdf, requirements, to_version=None, inclusive=False)`. It returns modified, removed and added changes with `reason` and `source` (new page and paragraph). Modified rows also carry `old_span` and `new_span`. `version_of(pdf)` finds the version label by SHA-256 in `regulations/index.json`. Underneath, `align.units` and `align.align` give unit-level links between the old and new paragraphs, and `align.kind` classifies them as unchanged, amended, new or deleted. Section 2 of `docs/regulation-change.md` explains how. The engine uses no model and no network and takes about 1 s per pair, so you need no cost approval to run it.
- **A stale updates page.** `web/frontend/src/routes/(app)/a/[id]/updates/+page.svelte` exists but nothing links to it. It reads a precomputed catalogue: `data/regulation-updates/dev-rear-lamp.json`, made by the older `scripts/diff_regulation.py`, or `web/backend/app/fake_data.py`. That logic is in `web/backend/app/updates.py`, behind `GET /api/assessments/{id}/updates` and `POST /api/assessments/{id}/updates/{regulation}` (apply). It has no upload and does not call `brain.subgoal`. The old catalogue lists only added rows for R148, R48 and R10, so treat it as a placeholder and replace it.
- **Pieces to reuse:**
  - `lib/ui/WordDiff.svelte` for word-level before and after;
  - `lib/graph/ProcessGraph.svelte` and `lib/graph/model.ts`, the four-column flow: Spec, Product profile, Regulations, Paragraphs;
  - `lib/graph/PdfDrawer.svelte` and `lib/components/PdfViewer.svelte`, which highlight a cited paragraph on its page;
  - `lib/components/AssessmentHeader.svelte` for the tabs;
  - `lib/exploded/Lamp3D.svelte` for part coverage.
- **How the backend runs the brain.** It runs the brain in its own venv (`BRAIN_PYTHON`, `brain_runner.py`, see `web/backend/app/pipeline.py`). Call the subgoal code the same way, or add a small runner entry point. Don't import brain into the backend's venv.
- **Version pairs in the corpus.** `regulations/index.json` and `regulations/pdf/` hold base and latest PDFs:
  - rear lamp: UN R148 1.6.0 to 1.7.0, UN R48 9.3.0 to 9.4.0, UN R10 7.2.0 to 7.3.0 (R150 has no newer version);
  - front bumper: UN R127 4.3.0 to 4.4.0.

## Backend

1. **Upload endpoint.** Add `POST /api/assessments/{id}/updates` with a multipart PDF and an optional `to_version`:
   - Identify the regulation and version by SHA-256 with `version_of`. If the file is not in the index, read the regulation number from the first page and require `to_version`.
   - Reject, with a plain one-sentence reason, a PDF that is not a version of a regulation the assessment cites, or that is the same version it already cites.
   - The old PDF is the version the assessment cites (the base).
2. **Run the diff.** Run `diff_assessment` in default mode, not inclusive, with the assessment's requirements for that regulation. Store the result as an update run with an id, so the page has a stable URL (`/a/{id}/updates/{run}`) and survives a reload. Keep the existing apply endpoint and its `apply_update` logic, fed from the stored run.
3. **Paragraph diff of the regulation.** Return it as well as the requirement changes, built from the alignment links:
   - One hunk per changed paragraph: old label, new label, new page, status (amended, new, deleted, or moved and amended), old text, new text and the word ops.
   - Leave out unchanged units, formatting-only changes and text that only moved or was renumbered. List renumbered paragraphs as a count and nothing more.
   - Mark each hunk as cited when an assessment requirement cites that paragraph or one of its ancestors, and link the hunk to those requirement ids.
4. **Whole-file guard.** If too little of the old document aligns (say under 50% of units unchanged), the upload is a different document or a full rewrite. Return a refusal that says so, and don't render a diff of the whole file. Check the threshold on the four real pairs above, then pick a value that passes all of them.
5. **Precomputed runs for the demo.** Commit precomputed runs for the five pairs above, for the rear lamp and the front bumper assessments, so the demo works offline and on Render. Replace `data/regulation-updates/dev-rear-lamp.json` with output from `brain.subgoal`, and remove the fake-data path once nothing uses it.
6. **Front bumper assessment.** Check `/history` for a stored front bumper assessment. If there is none, build one from an existing held-out main-goal output in `out/` (the requirements file, the spec and the exploded view). Do not run the paid pipeline; that needs the owner's approval and a cost estimate.

## Frontend

All pages sit under the assessment and use the existing app shell, the Certivity ink canvas and the tokens.

1. **Updates tab.** Add an "Updates" tab to `AssessmentHeader`. Show a mono count when a cited regulation has a newer version in the corpus.
2. **Start page** (`/a/[id]/updates`):
   - A table of the assessment's cited regulations with the version it cites, the latest version in the corpus, and the number of requirements that cite it. Each row with a newer version gets "Compare with {version}".
   - Above the table, a drop zone: "Upload a new version of a cited regulation".
   - Either path starts a run. Show the steps as the pipeline progress does: Identify regulation, Parse both versions, Align paragraphs, Map requirements, Done. The engine takes about a second, so hold each step long enough to read, about 300 ms, and make every number real.
3. **Run page** (`/a/[id]/updates/[run]`), three bands, top to bottom:
   - **Summary.** The regulation, "From 1.6.0 to 1.7.0", and large teal numerals for paragraphs amended, new and deleted. Under them, one sentence: "3 of this assessment's 41 cited R148 paragraphs changed. 7 new obligations may apply." Then the Apply update button, the one primary action.
   - **Regulation diff, like a pull request's files view.**
     - A left rail lists the changed paragraphs by label, with a status mark and the +/− word counts. Cited paragraphs come first, and a toggle shows the rest.
     - The main column has one hunk per paragraph. Its header is mono, with label, page and status ("§ 5.13.1.1, p. 27, new"). The body is a unified word diff by default, with a toggle for split old and new.
     - Use the tokens rather than red and green: mint `bg-mark` for inserted words, struck-through `text-muted` for deleted ones.
     - Each hunk's footer lists the requirement ids it affects. Clicking one scrolls to that requirement below.
     - "Open in PDF" on a hunk opens `PdfDrawer` on the new version with the paragraph highlighted. Add a before and after toggle in the drawer if the viewer handles two documents cleanly.
   - **Requirement impact.** Use the existing row layout with `WordDiff`: modified rows show the old requirement and the new text, removed rows are struck through, added rows show the new obligation. Each row has its reason and new page and paragraph. Group the rows by change type, with counts.
4. **Graph in diff mode** (`/a/[id]/graph?update=[run]`). Reuse `ProcessGraph`; don't build a second graph.
   - The regulation node shows "1.6.0 to 1.7.0".
   - Paragraph clusters get a status: changed, new and removed are lit, unchanged ones dim. New clusters use mint edges, removed clusters a dashed outline.
   - The right panel shows the requirement changes for the picked cluster.
   - Add a toggle between the assessment as it is and as it would be after the update. Animate the switch, with edges drawing and counts rolling, because the video records it.
   - Link to this view from the run page ("See it in the graph").
5. **Exploded view.** With `?update=[run]`, parts whose requirements change get a small mint marker, and their hover card shows "2 requirements change". This is optional; do it last, if time allows.
6. **Apply update.** Apply writes the new requirement list, bumps the regulation's version on the assessment and shows "Applied" with the new counts. A second upload of the same version then says it is already applied.

## Copy

Sentence case, plain words, no exclamation marks, no em dashes or middle dots as separators, no "AI" badges. Number every claim. Example strings: "Paragraph 5.13.1.1 is new in 1.7.0.", "Moved from 5.1.4.1, wording unchanged.", "This file does not match UN R148 1.6.0 closely enough to compare paragraph by paragraph."

## Done when

- On the rear lamp assessment, comparing UN R148 with 1.7.0 from the start page, and uploading the R148 1.7.0 PDF from `regulations/pdf/` by drag and drop, both open the same run page with real hunks and requirement changes.
- The same works for UN R127 4.3.0 to 4.4.0 on the front bumper assessment.
- Uploading an unrelated regulation PDF and re-uploading the cited version are both refused with a clear sentence.
- The graph diff toggle works on both assessments, and the PDF drawer opens on the new paragraph.
- `make check` passes, a backend test covers the upload endpoint, the version guard and the whole-file guard, and `make test` still passes.
- You checked every page in the browser preview in dark mode at 1920×1080 and attached screenshots of the run page, the diff hunks and the graph diff.
- The work is committed straight to `main` (pull before pushing, never force push), with the precomputed runs committed alongside the code that produced them.
