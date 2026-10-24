# Sub-goal regulation diff: implementation plan

> **Done (25 Oct).** This is the plan as written on 24 Oct. The code it names as
> `brain/brain/subgoal.py`, `brain/eval/subgoal_score.py` and `brain/eval/subgoal_survey.py` now
> lives in the package `brain/brain/subgoal/`; what was built and why it differs from this plan is
> in `docs/regulation-change.md` and in the Results of `brain/docs/todo/05-subgoal.md`.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One command that turns an old and a new regulation PDF plus `requirements_old.json` into a valid sub-goal submission, with 100% flag recall and 100% change accuracy on dev, no model and no network, in under a minute.

**Architecture:** A new module `brain/brain/subgoal.py` parses both PDFs with `brain.ingest.parse_pdf`, aligns old and new paragraphs (same label, renumbered, split), maps each old requirement to the sentence span it came from, and fills the four gold reason templates from a word-level diff. Added requirements come from new sentence spans that no old span accounts for, in the top-level sections the old requirements cite, written with `brain.rewrite.deterministic`. A strict local scorer, `brain/eval/subgoal_score.py`, comes first.

**Tech Stack:** Python 3.12, uv, PyMuPDF (through `brain.ingest`), `difflib`, pytest, ruff, mypy.

**Spec:** `brain/docs/todo/05-subgoal.md` (task prompt). Gold: `subgoal/dev/expected.json`.

## Global Constraints

- No paid model calls. `BRAIN_LLM` stays unset. The pipeline must run with no model and no network.
- Import from `brain/brain/ingest.py` and `brain/brain/rewrite.py`; never edit them (tasks 02 and 06 own them). Needed changes go in the task file under "Results" and to the team.
- Owned files only: `docs/regulation-change.md`, `brain/brain/subgoal.py`, `brain/eval/subgoal_score.py`, `brain/eval/subgoal_survey.py`, `brain/tests/test_subgoal.py`, `out/subgoal-*`.
- Output: `{"team_id": "team-06", "case_id": ..., "changes": [...]}`, valid under `python tools/validate.py <file> --requirements-old <file>`.
- Every run of the pipeline on dev is saved as `out/subgoal-dev-<variant>.json` plus `.log`, with a row in `out/README.md` (date and time CEST, branch, commit, method, change count, local scores, spend $0).
- Before every commit, from `brain/`: `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`.
- Commit straight to `main`; `git pull` first; never force push. Docs and commit messages follow `DESIGN.md`, including its AI-isms list.
- Freeze at 02:00 (only task 06 changes the engine after that).
- The solution must be general. Never branch on `UN R175`, a label from the dev gold, or a gold string.

## Facts established while gathering context

These decide the design; the architecture doc restates them.

- `brain.ingest.parse_pdf` gives every gold paragraph its gold label and page on `new.pdf` (5.1.4.1 p5, 5.1.6.2 p6, 6.5.2 p10, 6.6.2.2 p11, …). It also reproduces the gold's text quirks: the gold quotes 5.1.6.2 as "Acceleration while creeping, In the case…", which is ingest's heading joined to the body with ", ". The gold was most likely generated from this parser, so use it, not the script's parser.
- `scripts/diff_regulation.py` already gets all 7 modified and removed ids right on dev. Its gaps are in the added set: it emits 18 added rows against the gold's 17, with 7 wrong (12.1.x transitional provisions, 5.1.12, the 6.6.1.2 lead-in) and 6 missing (5.1.4.1, 6.5.3, 6.6.2.2 items (a) to (d) split per item, the second half of 6.6.1.1). Port its `word_ops`, `describe`, `bare`, `best_span` and `apply_ops` into the typed module; don't rewrite them from scratch.
- Old requirements cite top-level sections 3 to 8 only. The gold adds nothing in section 12 (Transitional provisions).
- Old 6.5 was split: R-084, R-085 and R-086 map to new 6.5.2, 6.6 and 6.6.1.2; R-087 to R-089 come from sentences that survive unchanged and are not flagged; R-090's sentence is gone (removed). So a requirement is flagged only when the edit touches its own span. A paragraph edit elsewhere does not flag it.
- Quote cut, measured against ingest's text: an added quote is the obligation's sentence or list item, `text[:99].rstrip() + "…"` when longer than 100 characters, else the whole text. A removed quote is the old source sentence, `text[:89].rstrip() + "…"`. Three gold quotes break this rule (6.6.1.1's second row, 5.1.4.1 and 6.5.3 at 109 characters). Don't fit them: the exact-reason ceiling on dev is 21 of 24 by design.
- Gold `new_text` for modified rows is sometimes the old requirement with the edits applied (R-015) and sometimes the new span nearly verbatim (R-018, R-086). The platform's "change accuracy" is most likely the change type per flagged requirement. `new_text` similarity is reported, not gated.

## Review Focus

1. **Formatting-only change** (rewrapped lines, "70%" against "70 per cent", a moved page break, a footnote marker): nothing flagged. Pinned in Task 2 (`test_format_only_is_not_flagged`) and the synthetic pairs in Task 6.
2. **Renumbered section with unchanged text** (6.5 becomes 6.6, every child shifts): no modified or added rows, only the label moves. Pinned in Task 2 (`test_renumbered_section_is_not_flagged`).
3. **Annex paragraphs and tables** (labels like `Annex 3 2.1`, table cell text in the body): no crash, and annex labels in the output match ingest's. Pinned in Task 6 (survey over all 36 pairs, which must finish without an exception).
4. **A requirement whose cited paragraph is a parent** (cites `6.5` but its sentence sits in `6.5.3` in the old PDF): it is mapped through the descendants. Pinned in Task 3 (`test_requirement_citing_parent_is_mapped_to_child`).
5. **A held-out pair whose version label is not in `regulations/index.json`**: the CLI takes `--to-version` and fails with a clear message if it can find none. Pinned in Task 5 (`test_cli_requires_version_when_unknown`).

---

### Task 0: Architecture doc, then stop for agreement

**Files:**
- Create: `docs/regulation-change.md`

- [ ] **Step 1: Write the doc**, one or two pages, answering the eight questions in the spec ("Part 1"). Use the facts above. The decisions to state:
  1. Parser: `brain.ingest.parse_pdf` for both versions, because it reproduces the gold's text and labels (5.1.6.2 example), handles annex labels and page stitching, and is already tested; page headers and footnotes are dropped by ingest.
  2. Alignment, three passes on `bare()` tokens with `difflib` ratio: (a) same label, ratio ≥ 0.5 is a pair; (b) unpaired old against unpaired new, ratio ≥ 0.8 is renumbered; (c) any old paragraph whose sentences don't all appear in its pair is split: each old sentence span goes to the single best new span with ratio ≥ 0.5 (one new span per old span, best score wins), else it is deleted. "(formerly X)" is written when the new label of a requirement's span differs from the old label.
  3. Classification: unchanged when `bare()` tokens are equal (this covers formatting); amended when word ops survive `substantive`; new for new spans no old span claimed; deleted for old spans no new span claimed.
  4. Mapping: a requirement's old span is `best_span(req.text, [cited paragraph and its descendants])`; flagged only if its own span has ops or is deleted.
  5. Change records: modified `new_text` is `apply_ops` on the requirement when every op applies, else the new span; added is one row per obligation (sentence with "shall", or list item under a lead-in ending in ":"), written with `brain.rewrite.deterministic`, scoped to the top-level sections the old requirements cite; removed when the old span has no new span.
  6. The four reason templates verbatim from the spec, sources from the new PDF.
  7. No model. If added `new_text` later needs one, it is optional and the deterministic text stays the default.
  8. Change monitor: `diff_assessment(regulation, old_pdf, new_pdf, requirements, to_version) -> dict` returning the submission dict plus, per change, `old_span` and `new_span` (the sentence that changed), for `web/backend` to call.
- [ ] **Step 2: Commit** the doc (`Write the sub-goal architecture: one parser, span alignment, templated reasons`).
- [ ] **Step 3: Stop and show it to the team.** Two choices are theirs, not ours: (a) `brain/brain/subgoal.py` on `brain.ingest` rather than extending `scripts/diff_regulation.py`; (b) scoping added rows to the sections the old requirements cite rather than a list of administrative headings. Build only after a yes.

### Task 1: Strict local scorer

**Files:**
- Create: `brain/eval/subgoal_score.py`
- Test: `brain/tests/test_subgoal.py`

**Interfaces:**
- Produces: `score(submission: dict, expected: dict) -> Report`, where `Report` is a dataclass with `flag_recall: float`, `change_accuracy: float`, `added_recall: float`, `reason_exact: float`, `new_text_similarity: float` (mean `difflib` ratio over matched rows), `extra: int` (submitted rows matching no gold row) and `mismatches: list[str]`. CLI: `uv run python -m eval.subgoal_score <file> [--expected ../subgoal/dev/expected.json]`, prints the numbers and every mismatch, exits 0.
- Matching: modified and removed rows match on `requirement_id`; added rows match one to one within the same `source.paragraph` by best `new_text` ratio, with a floor of 0.5 (below it the row counts as extra). `flag_recall` = matched gold rows / gold rows; `change_accuracy` = matched rows with the same `change` / matched rows.

- [ ] **Step 1: Write the failing tests**

```python
def test_gold_scores_itself_perfectly():
    gold = json.loads(EXPECTED.read_text())
    r = score(gold, gold)
    assert (r.flag_recall, r.change_accuracy, r.reason_exact, r.extra) == (1.0, 1.0, 1.0, 0)

def test_wrong_change_type_costs_accuracy_not_recall():
    gold = json.loads(EXPECTED.read_text())
    sub = copy.deepcopy(gold)
    sub["changes"][6]["change"] = "modified"          # R-090 removed -> modified
    r = score(sub, gold)
    assert r.flag_recall == 1.0 and r.change_accuracy == 23 / 24
    assert any("R-090" in m for m in r.mismatches)

def test_added_rows_match_within_their_paragraph():
    gold = json.loads(EXPECTED.read_text())
    sub = copy.deepcopy(gold)
    sub["changes"][7]["source"]["paragraph"] = "9.9"   # 5.1.6.2 moved away
    r = score(sub, gold)
    assert r.flag_recall == 23 / 24 and r.extra == 1
```

- [ ] **Step 2: Run** `cd brain && uv run pytest tests/test_subgoal.py -q`. Expected: FAIL, `eval.subgoal_score` not found.
- [ ] **Step 3: Implement** `score` and the CLI in `brain/eval/subgoal_score.py`.
- [ ] **Step 4: Run** the tests, then `uv run python -m eval.subgoal_score ../subgoal/dev/expected.json`. Expected: PASS; the CLI prints recall 1.000, accuracy 1.000.
- [ ] **Step 5: Baseline the script.** Convert the script's dev output to the schema (rename `requirementId`, drop `oldText`) in a scratch file and score it. Record the numbers under "Results" in `brain/docs/todo/05-subgoal.md`. Expected about 7/7 on modified and removed ids and 11/17 on added.
- [ ] **Step 6: Commit** (`Score sub-goal files against the dev gold`).

### Task 2: Word diff and paragraph alignment

**Files:**
- Create: `brain/brain/subgoal.py`
- Test: `brain/tests/test_subgoal.py`

**Interfaces:**
- Consumes: `brain.models.Paragraph` (`label`, `page`, `text`, `heading`, `parent`).
- Produces:
  - `Op = tuple[Literal["replace", "insert", "delete"], str, str, int]` (tag, old phrase, new phrase, old word index)
  - `bare(text: str) -> list[str]`, `word_ops(old: str, new: str) -> list[Op]`, `substantive(ops: list[Op]) -> list[Op]` (drops ops whose sides are equal under `bare`), `describe(ops: list[Op]) -> str`, ported from the script.
  - `sentences(text: str) -> list[str]`: sentence and list-item units, with `(a)`, `(i)` items as their own units.
  - `@dataclass(frozen=True) class Span: label: str; page: int; text: str`
  - `@dataclass(frozen=True) class Link: old: Span | None; new: Span | None; ops: tuple[Op, ...]` (`old` None: new; `new` None: deleted; empty `ops`: unchanged)
  - `align(old: list[Paragraph], new: list[Paragraph]) -> list[Link]`, at span level, using the three passes and thresholds from Task 0.
  - `kind(link: Link) -> Literal["unchanged", "amended", "new", "deleted"]`: renumbered and split links with no ops are `"unchanged"`.
  - `best_span(target: str, paragraphs: list[Paragraph]) -> tuple[float, str | None, str | None]` and `apply_ops(req_text: str, old_span: str, ops: list[Op]) -> tuple[str, int]`, ported from the script for Task 3.

- [ ] **Step 1: Write the failing tests.** Build paragraphs in code with a small `para(label, text, page=1)` helper.

```python
def test_describe_uses_gold_wording():
    ops = substantive(word_ops("from standstill.", "both from standstill and, as relevant, while creeping."))
    assert set(describe(ops).split("; ")) == {"'standstill.' became 'standstill and, as relevant, while creeping.'",
                                              "'both' was added"}

def test_format_only_is_not_flagged():
    links = align([para("5.1", "A speed of 70% shall be\nheld for 6 seconds.")],
                  [para("5.1", "A speed of 70 per cent shall be held for 6 s.")])
    assert all(not l.ops for l in links)

def test_renumbered_section_is_not_flagged():
    old = [para("6.5", "The target shall be stationary."), para("6.6", "The test shall be repeated twice.")]
    new = [para("6.6", "The target shall be stationary."), para("6.7", "The test shall be repeated twice.")]
    links = align(old, new)
    assert {(l.old.label, l.new.label) for l in links} == {("6.5", "6.6"), ("6.6", "6.7")}
    assert all(not l.ops for l in links)

def test_split_paragraph_maps_each_sentence_to_its_new_home():
    old = [para("6.5", "The offset shall be 0.2 m. The vehicle shall be stationary. A warm-up run may be made.")]
    new = [para("6.5.2", "The offset shall be 0.5 m."), para("6.6.1", "The vehicle shall be stationary.")]
    by_old = {l.old.text: l for l in align(old, new) if l.old}
    assert by_old["The offset shall be 0.2 m."].new.label == "6.5.2"
    assert by_old["The vehicle shall be stationary."].ops == ()
    assert by_old["A warm-up run may be made."].new is None

def test_new_paragraph_is_unclaimed():
    links = align([para("5.1", "X shall be red.")], [para("5.1", "X shall be red."), para("5.2", "Y shall be blue.")])
    assert [l.new.label for l in links if l.old is None] == ["5.2"]
```

  Edit order: keep `difflib`'s document order. The gold's order is not consistent (5.1.4 and 6.5.2 list a later edit first, 5.1.5 follows document order), so no sort reproduces all of it; exact-reason misses from order alone go under Results, not into a rule.
- [ ] **Step 2: Run** `uv run pytest tests/test_subgoal.py -q`. Expected: the five new tests FAIL on import.
- [ ] **Step 3: Implement** the functions in `brain/brain/subgoal.py`. Paragraph text is compared on `bare()` tokens; spans keep the original text for quoting.
- [ ] **Step 4: Run** the tests. Expected: PASS.
- [ ] **Step 5: Commit** (`Align old and new regulation paragraphs at sentence level`).

### Task 3: Requirement mapping and the modified and removed records

**Files:**
- Modify: `brain/brain/subgoal.py`
- Test: `brain/tests/test_subgoal.py`

**Interfaces:**
- Consumes: `align`, `Link`, `Span`, `describe`, `best_span` (ported) from Task 2.
- Produces:
  - `quote(text: str, limit: int) -> str`: `text` if `len(text) <= limit`, else `text[: limit - 1].rstrip() + "…"`. Added quotes use `limit=100`, removed `limit=90`.
  - `map_requirements(requirements: list[dict], old: list[Paragraph], links: list[Link], regulation: str, to_version: str) -> list[dict]`: modified and removed change dicts in the schema, in requirement order.
  - Reason strings, exactly:
    - `f"Paragraph {new} of {reg} was amended in version {v}: {describe(ops)}."`
    - `f"Paragraph {new} (formerly {old}) of {reg} was amended in version {v}: {describe(ops)}."`
    - `f"Paragraph {old} of {reg} was amended in version {v}; the provision '{quote(old_span, 90)}' no longer appears."` (no `new_text`, no `source`)

- [ ] **Step 1: Write the failing tests**

```python
def test_quote_cuts_like_the_gold():
    text = "Acceleration while creeping, In the case a collision is not prevented, the ACPE shall reduce the effective demand"
    assert quote(text, 100) == "Acceleration while creeping, In the case a collision is not prevented, the ACPE shall reduce the ef…"

def test_requirement_citing_parent_is_mapped_to_child():
    old = [para("6.5", "Test conditions"), para("6.5.3", "The offset shall be 0.2 m.")]
    new = [para("6.5", "Test conditions"), para("6.5.3", "The offset shall be 0.5 m.")]
    reqs = [{"id": "R-1", "text": "The offset shall be 0.2 m.", "source": {"page": 1, "paragraph": "6.5"}}]
    [c] = map_requirements(reqs, old, align(old, new), "UN R1", "2.0.0")
    assert c["change"] == "modified" and c["source"]["paragraph"] == "6.5.3"

def test_edit_elsewhere_in_paragraph_does_not_flag():
    old = [para("6.5", "The offset shall be 0.2 m. The vehicle shall be stationary.")]
    new = [para("6.5", "The offset shall be 0.5 m. The vehicle shall be stationary.")]
    reqs = [{"id": "R-2", "text": "The vehicle shall be stationary.", "source": {"page": 1, "paragraph": "6.5"}}]
    assert map_requirements(reqs, old, align(old, new), "UN R1", "2.0.0") == []

@needs_dev_pdfs
def test_dev_modified_and_removed_match_gold():
    changes = run_dev()          # helper: parse ../subgoal/dev PDFs and map ../subgoal/dev/requirements_old.json
    got = {(c["requirement_id"], c["change"]) for c in changes if c["requirement_id"]}
    assert got == {("R-015", "modified"), ("R-018", "modified"), ("R-021", "modified"), ("R-084", "modified"),
                   ("R-085", "modified"), ("R-086", "modified"), ("R-090", "removed")}
    sources = {c["requirement_id"]: c.get("source", {}).get("paragraph") for c in changes}
    assert sources["R-084"] == "6.5.2" and sources["R-085"] == "6.6" and sources["R-086"] == "6.6.1.2"
```

  `needs_dev_pdfs` is `pytest.mark.skipif(not (ROOT / "subgoal/dev/old.pdf").exists(), ...)`.
- [ ] **Step 2: Run** the tests. Expected: FAIL.
- [ ] **Step 3: Implement** `quote` and `map_requirements`. A requirement's old span is the best span over its cited paragraph and that paragraph's descendants; it is flagged only if the link holding that span has ops or no new span. `new_text` is `apply_ops` on the requirement text when every op applies, else the new span text.
- [ ] **Step 4: Run** the tests. Expected: PASS.
- [ ] **Step 5: Commit** (`Map old requirements onto changed spans and template their reasons`).

### Task 4: Added records

**Files:**
- Modify: `brain/brain/subgoal.py`
- Test: `brain/tests/test_subgoal.py`

**Interfaces:**
- Consumes: `Link` (rows with `old is None`), `quote`, `brain.rewrite.deterministic(p: Paragraph, graph: Graph) -> list[Draft]`, `brain.graph.build`.
- Produces:
  - `obligations(span: Span, lead_in: str | None) -> list[tuple[str, str]]`: (quoted unit, unit for the rewrite) per obligation. A sentence with "shall" or "may" is one unit, and a sentence of the form "X shall A, and may B" gives two rows with the same quote. Each list item under a lead-in ending in ":" is one unit, quoted alone and rewritten with the lead-in.
  - `added_changes(new: list[Paragraph], links: list[Link], sections: set[str], regulation: str, to_version: str) -> list[dict]`. `sections` holds the top-level numbers the old requirements cite (`{"3", "4", "5", "6", "7", "8"}` on dev). Reason: `f"Paragraph {label} of {reg} is new in version {v}: '{quote(unit, 100)}'."`

- [ ] **Step 1: Write the failing tests**

```python
def test_list_items_become_one_row_each_with_the_item_quoted():
    span = Span("6.6.2.2", 11, "The procedure shall be as follows: (a) Position the vehicle. (b) Hold the vehicle stationary.")
    rows = obligations(span, None)
    assert [q for q, _ in rows] == ["(a) Position the vehicle.", "(b) Hold the vehicle stationary."]

def test_section_outside_requirement_scope_adds_nothing():
    new = [para("12.1.1", "Contracting Parties shall accept approvals.")]
    links = [Link(None, Span("12.1.1", 12, new[0].text), ())]
    assert added_changes(new, links, {"5", "6"}, "UN R1", "2.0.0") == []

@needs_dev_pdfs
def test_dev_added_rows_match_gold_paragraphs():
    changes = run_dev()
    got = Counter(c["source"]["paragraph"] for c in changes if c["change"] == "added")
    assert got == Counter({"5.1.4.1": 1, "5.1.6.2": 1, "6.4.2": 1, "6.5.1": 1, "6.5.3": 1, "6.5.5": 1,
                           "6.6.1.1": 3, "6.6.2.1": 3, "6.6.2.2": 5})
```

  If the dev counts only fit with a rule that names a dev label or string, stop and write the conflict under Results instead of fitting it.
- [ ] **Step 2: Run** the tests. Expected: FAIL.
- [ ] **Step 3: Implement** `obligations` and `added_changes`. The lead-in sentence itself ("… shall be as follows:") is never a row of its own. `new_text` comes from `rewrite.deterministic` on a copy of the paragraph whose text is the unit; fall back to the unit text if it returns nothing.
- [ ] **Step 4: Run** the tests. Expected: PASS.
- [ ] **Step 5: Commit** (`Add one requirement per new obligation, scoped to the cited sections`).

### Task 5: The Sunday command, and 100 / 100 on dev

**Files:**
- Modify: `brain/brain/subgoal.py` (add `run` and `main`)
- Modify: `out/README.md` (run log row and dated section)
- Create: `out/subgoal-dev-det.json`, `out/subgoal-dev-det.log`
- Test: `brain/tests/test_subgoal.py`

**Interfaces:**
- Produces:
  - `run(old_pdf: Path, new_pdf: Path, requirements: list[dict], case_id: str, team_id: str = "team-06", to_version: str | None = None) -> dict`: the submission. The regulation comes from `requirements[0]["source"]["regulation"]`; `to_version`, when None, is the `version_label` of the entry in `regulations/index.json` whose file sha256 matches `new_pdf`, else `ValueError("pass --to-version: <sha256> is not in regulations/index.json")`.
  - `diff_assessment(...)`, the change-monitor wrapper from Task 0, returning `run`'s dict with `old_span` and `new_span` on each change.
  - CLI, from `brain/`: `uv run python -m brain.subgoal --old-pdf ... --new-pdf ... --requirements-old ... --case-id ... --out ... [--to-version ...] [--team-id team-06]`. It runs `tools/validate.py` with `--requirements-old` on its output and exits non-zero if invalid.

- [ ] **Step 1: Write the failing tests**

```python
def test_cli_requires_version_when_unknown(tmp_path):
    other = tmp_path / "new.pdf"; other.write_bytes(DEV_NEW.read_bytes() + b"%")
    with pytest.raises(ValueError, match="pass --to-version"):
        run(DEV_OLD, other, DEV_REQS, case_id="x")

@needs_dev_pdfs
def test_dev_scores_100_100():
    r = score(run(DEV_OLD, DEV_NEW, DEV_REQS, case_id="subgoal-dev"), json.loads(EXPECTED.read_text()))
    assert (r.flag_recall, r.change_accuracy, r.extra) == (1.0, 1.0, 0)
```

- [ ] **Step 2: Run** the tests. Expected: FAIL.
- [ ] **Step 3: Implement** `run`, `diff_assessment` and `main`.
- [ ] **Step 4: Run** the tests, then the command on dev:

```bash
cd brain && time uv run python -m brain.subgoal --old-pdf ../subgoal/dev/old.pdf --new-pdf ../subgoal/dev/new.pdf \
  --requirements-old ../subgoal/dev/requirements_old.json --case-id subgoal-dev --out ../out/subgoal-dev-det.json \
  2> ../out/subgoal-dev-det.log
uv run python -m eval.subgoal_score ../out/subgoal-dev-det.json
```

  Expected: tests PASS; recall 1.000, accuracy 1.000, extra 0, under 60 s. Note `reason_exact` and `new_text_similarity` too. Every mismatch below 100 / 100 is a bug to find, not a limit.
- [ ] **Step 5: Record** the run: a row in `out/README.md` (CEST time, `main`, commit, "deterministic, no model", 24 changes, local scores, $0) and a dated section on what changed.
- [ ] **Step 6: Run the four checks and commit** (`Turn a pair of regulation PDFs into a sub-goal submission in one command`), including the `out/` files.
- [ ] **Step 7: Ask the team for one platform upload** of `out/subgoal-dev-det.json` (uploads are shared, 5 per hour). Add the platform's scores and upload time to the same `out/README.md` row, to `brain/docs/todo/README.md` (status of task 05) and to "Results" in `05-subgoal.md`. Commit.

### Task 6: Prove it is general

**Files:**
- Create: `brain/eval/subgoal_survey.py`
- Modify: `brain/tests/test_subgoal.py`
- Modify: `brain/docs/todo/05-subgoal.md` (Results)

**Interfaces:**
- Consumes: `align`, `run` from Tasks 2 and 5; `brain.ingest.load(regulation, role)`; `brain.ingest.sources()`.
- Produces: `uv run python -m eval.subgoal_survey` prints one row per regulation with both versions: amended, new, deleted, renumbered, split span counts and seconds. `synthetic_pairs(paragraphs: list[Paragraph]) -> list[tuple[str, list[Paragraph], list[Paragraph], set[tuple[str, str]]]]`: (name, old, new, expected `(old_label or "", kind)` set) for six edits: renumber a section, insert a paragraph, delete one, change a number, split a paragraph, whitespace only.

- [ ] **Step 1: Write the failing test**

```python
@needs_corpus
@pytest.mark.parametrize("regulation", ["UN R48", "UN R10", "UN R149"])
def test_synthetic_edits_are_found_exactly(regulation):
    for name, old, new, expected in synthetic_pairs(load(regulation, "base")):
        found = {(l.old.label if l.old else "", kind(l)) for l in align(old, new) if kind(l) != "unchanged"}
        assert found == expected, name
```

  `kind` comes from Task 2. The renumber and whitespace pairs expect the empty set. `needs_corpus` skips when `brain/data/corpus/UN_R48_base.jsonl` is missing.
- [ ] **Step 2: Run** it. Expected: FAIL.
- [ ] **Step 3: Implement** `synthetic_pairs` and the survey.
- [ ] **Step 4: Run** the test, then the survey over all 36 pairs. Expected: PASS, no exception, each pair under 60 s. Paste the table under Results.
- [ ] **Step 5: Read the three pairs with the most renumbering and one pair several versions apart**, and run `brain.subgoal` on two or three of them. For `requirements_old`, use the deterministic rows of `brain.pipeline` for that regulation (ids renamed `R-001`, …). Check by reading: nothing flagged for formatting only, renumbering looks right, no crash on annexes or tables. Write what you found under Results, with the commands. Fix any bug with a test first.
- [ ] **Step 6: Run the four checks and commit** (`Survey every base and latest pair and test the diff on synthetic edits`).

### Task 7: Sunday steps

**Files:**
- Modify: `brain/docs/todo/05-subgoal.md` (a "Sunday steps" section for task 06)

- [ ] **Step 1: Write the steps**: the held-out pair lands in `subgoal/<folder>/` (also on `git pull upstream main`); the exact `brain.subgoal` command with `--case-id` set to the folder name; `--to-version` from `regulations/index.json` if the sha256 lookup fails; validation with `python tools/validate.py <file> --requirements-old subgoal/<folder>/requirements_old.json`; upload it to the sub-goal challenge, which has its own 5-per-hour limit separate from the main goal; the last valid upload counts, so upload once and don't follow it with an experiment.
- [ ] **Step 2: Rehearse** the steps on dev from a clean shell, timing them, and commit (`Write the Sunday steps for the sub-goal`).
