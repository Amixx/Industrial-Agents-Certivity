# 05 The sub-goal submission

## Prompt

You are joining a hackathon team mid-event (Certivity challenge, Munich). Read
`brain/docs/todo/README.md` first: it has the event, the rules and the tools. Work from the
repo root; the paths in this file are relative to it.

**First, check whether someone already owns this.** Look at `git log --all -- subgoal scripts`
and ask the team. If a sub-goal pipeline exists elsewhere, take over its open points instead of
starting again.

**The task** (`docs/CHALLENGE.md`, section 3). Input: the requirements derived from one
version of a regulation (`subgoal/dev/requirements_old.json`, 94 requirements) and a later
version of the same regulation (`subgoal/dev/old.pdf`, `subgoal/dev/new.pdf`; the dev pair is
UN R175). Output: which requirements change (`modified`, `removed`, or `added` with
`requirement_id` null), the new text, the reason, and the source page and paragraph. Schema:
`schemas/submission_subgoal.schema.json`; check with
`python tools/validate.py <file> --requirements-old subgoal/dev/requirements_old.json`.
Scored on the recall of the requirements flagged for change and the accuracy of the change. It
is 15% of the jury score, and the held-out pair arrives at 08:00 with the main case.

**What exists.** `scripts/diff_regulation.py` diffs two versions paragraph by paragraph and maps
the changes onto requirements. The dev gold (`subgoal/dev/expected.json`) has 24 changes: 17
added, 6 modified, 1 removed. Its reasons follow a fixed pattern, for example "Paragraph 5.1.2
of UN R175 was amended in version 1.0.0: 'resulting in continuous acceleration and' was added."
or "Paragraph 6.6.1.1 is new …". That pattern is generated from a paragraph diff, so a
deterministic diff can reproduce most of it.

**What to do.**
1. Run `scripts/diff_regulation.py` on the dev pair and write a scorer, `subgoal/score.py` or
   inside the script: recall of the flagged requirement ids, accuracy of the change type, and a
   check of `new_text` and `reason` against the gold (exact paragraph, plus text similarity).
2. Fix what the scorer shows: paragraphs missed by the diff, wrong mapping from paragraph to
   requirement, added requirements without a page, reasons not in the gold's pattern.
3. Consider reusing `brain/brain/ingest.py` for the paragraph split: it parses every regulation PDF
   into labelled paragraphs with pages, and all 121 dev gold citations resolve. The sub-goal
   PDFs can be parsed with `parse_pdf`.
4. For `new_text` of modified and added requirements, a model rewrite may help (the same style
   as the main goal). Measure with and without; paid calls need approval (rule 1).
5. Make it one command for Sunday: two PDFs and the old requirements in, a validated file out.
   Write that command into your task file for the runbook (task 06).

**Acceptance.**
- On dev: recall of flagged requirements at least 0.9, change type right for at least 0.9 of
  them, the file passes `tools/validate.py`.
- One command, documented, that runs on a new pair in under a minute without a model.

**Deliverables.** The scorer, the fixes, a dev submission file ready to upload, the Sunday
command, and the numbers under "Results".

**Do not.** Edit files under `brain/brain/` that other tasks own; import from them instead.

## Results

(fill in)
