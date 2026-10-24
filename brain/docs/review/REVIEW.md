# Independent review of the brain

Reviewed 24 October 2026, approximately 17:50–17:57 Europe/Berlin. This is a review of the working files, not a committed revision. Artifacts and logs were changing during inspection, so saved-artifact scores and fresh runs are distinguished below.

The only intentional repository addition from this review is this report. No implementation, corpus, model, existing output, or results CSV was changed; nothing was committed or pushed. The contents of `vlad/.env` were never printed or copied. Custom audit scripts bypassed dotenv loading and blocked provider calls. LLM results below were replayed from existing caches, with cache misses raising an exception rather than making a request. No corpus data was sent externally. A generic official-documentation search failed with an authorization error; current remote API compatibility remains unverified.

Read: the challenge PDF, root README/CLAUDE/AGENTS/design guidance, challenge/determinism/extraction/graph/approach docs, organizer transcript and summary, `vlad/` plans and framework docs, all brain/eval modules and tests, the dev spec/image/gold, index, schemas and official scoring/validation tools. The teammate-owned sub-goal was inspected for context only.

## 1. Executive summary

**Conditional go for a supervised submission; no-go for an unattended Sunday run.** The current strong-relevance pipeline is a meaningful improvement over the deterministic baseline. Its dev score does not establish bumper generalization or reliable cold execution.

Top five risks, ranked by expected score impact using the available evidence. This ordering is qualitative: there is no independent bumper gold or failure-rate estimate from which to calculate expected F2 losses.

| Rank | Risk | Evidence and likely consequence |
|---|---|---|
| 1 | Regulation and paragraph selection transfer from one lamp case | Whole missed regulations cap recall before rewriting. At the saved model's threshold, in-sample paragraph F2 is 0.467 versus 0.386 out-of-fold. Lamp-focused prompts and uncalibrated cross-domain probabilities remain. |
| 2 | Selected paragraphs do not translate reliably into matching atomic obligations | Gold-normalized paragraphs contribute 1–10 requirements each. Even with gold paragraphs, deterministic rewriting reaches only 0.641 lexical F2. Fidelity checks accept changed polarity, units and conditions. |
| 3 | A failed API batch can prevent any submission | An injected rewrite timeout propagates out of the executor. There is no application-level per-batch fallback or deadline. SDK read timeout defaults to 600 seconds, already longer than the claimed full-run time. |
| 4 | Evaluation can reward the wrong changes | Dev pipeline probabilities are in-sample; thresholds/prompts were selected on dev; synthetic cases reuse the same gold. The proxy accepts contradictory obligations and its assignment algorithm can undercount valid matches. |
| 5 | Table identity, inherited context and parser boundary gaps | Three gold requirements have table-qualified labels not emitted by the parser. Parent conditions are clipped to 60-character snippets; relevance clips text at 1,500 characters, including two gold table paragraphs. |

The old concern that plain-bumper output contains only two R42 requirements is stale: the current cached pipeline emits **105 requirements, including 10 from R42**. This improves coverage evidence, but it is still an unlabelled smoke test.

## 2. Verified numbers and reproduction

### Checks and execution boundaries

Used the existing environment, without dependency synchronization. Commands ran from `vlad/` with `PYTHONDONTWRITEBYTECODE=1` and `UV_CACHE_DIR=/private/tmp/certivity-review-uv-cache`.

```sh
uv run --offline --no-sync ruff check --no-cache brain eval
uv run --offline --no-sync mypy --cache-dir=/dev/null brain eval
uv run --offline --no-sync pytest -q -p no:cacheprovider
uv run --offline --no-sync python ../tools/validate.py out/dev-rear-lamp.json
uv run --offline --no-sync python ../tools/score_local.py out/dev-rear-lamp.json --json
uv run --offline --no-sync python -m eval.gold_check
```

Observed:

```text
All checks passed!
Success: no issues found in 22 source files
15 passed in 2.01s
OK: dev-rear-lamp.json is valid (778 requirements).
121/121 cited paragraphs found on their page
```

The official scorer returned regulation P/R = 1/1 and page P/R = 0.400/0.905660, with 120 submitted pages, 53 expected and 48 matched.

Instead of running mutating CLIs, inline Python called `parse_pdf`, `dataset`, `cross_validate`, `fit`, `run`, and `eval.score.score` in memory. The important calls were:

```python
corpus = load_all("base")
ds = dataset(CASES / "dev-rear-lamp", corpus)
oof = cross_validate(ds)
saved = Model.load(MODEL_PATH)
insample = saved.predict(ds.X)
refitted = fit(ds.X, ds.y)  # not saved
submission = run(spec, image=None, case_id=case.name, use_llm=False)
metrics = score(submission, expected)
for s in sources():
    rebuilt = parse_pdf(s.pdf, s.regulation, s.version, s.role)  # not written
```

All **92 regulation PDFs listed by the index** parsed in 10.19 seconds; the 56 rebuilt base corpora were identical to the existing JSONL records. The two sub-goal PDFs are separate. The loaded base corpus has 25,209 records. This is not the older graph experiment's 23,886-node corpus.

The first inline audit ended with a review-script import error, attempting a nonexistent `gold_check.check`; the correct `gold_check.main` was subsequently run successfully, as shown above. Earlier completed results were unaffected.

### End-to-end dev results

Requirement scores everywhere in this report are **lexical proxy scores**, unless explicitly described otherwise.

| Run | Requirements | Regulation F2 | Page F2 | Requirement P / R / F2 | Matches |
|---|---:|---:|---:|---|---:|
| Fresh deterministic, reproduced | 778 | 1.000 | 0.723 | 0.144 / 0.589 / 0.364 | 112/190 |
| Old relevance run in CSV/log, not regenerated under old settings | 488 | 0.952 | 0.851 | 0.295 / 0.758 / 0.577 | 144/190 implied |
| Saved `out/dev-llm.json` observed during review | 407 | 0.952 | 0.877 | 0.359 / 0.768 / 0.626 | 146/190 |
| Fresh current pipeline, cache-only | 409 | 0.952 | 0.877 | 0.357 / 0.768 / 0.624 | 146/190 |

Current pipeline settings are **strong relevance, weight 0.7, threshold 0.10**, with a floor of `max(5, int(0.06 * n))` paragraphs per selected regulation. The handoff's weight 0.5 / threshold 0.08 is no longer the default. The relevance tier environment variable is implemented.

The 1,149-requirement pre-relevance result was not reproduced: the current implementation no longer exposes that configuration directly, and its artifact has been superseded. Do not present it as a current baseline.

Fresh deterministic Tier A runs reproduce the README:

| Case | n | Regulation F2 | Page F2 | Requirement F2 |
|---|---:|---:|---:|---:|
| full-filament | 675 | 1.000 | 0.747 | 0.379 |
| position-retro-led | 746 | 1.000 | 0.668 | 0.343 |
| reversing-filament | 294 | 1.000 | 0.734 | 0.353 |
| stop-lamp-led | 399 | 1.000 | 0.707 | 0.340 |
| stop-position-filament | 312 | 1.000 | 0.776 | 0.401 |

These are functional regressions, not five independent generalization tests.

### Decision model optimism

The training dataset has 2,915 records and **119 positive normalized paragraph keys**. The 121 raw gold citation entries collapse because table citations are mapped to their parent paragraph.

| Dataset/prediction | AUC | F2 at 0.06 | Best swept F2 | Best threshold |
|---|---:|---:|---:|---:|
| All training candidates, in-sample | 0.9060 | 0.4673 | 0.4890 | 0.12 |
| All training candidates, regulation OOF | 0.8412 | 0.3855 | 0.3855 | 0.06 |
| Numbered candidates only, in-sample | 0.9028 | — | 0.4897 | 0.12 |
| Numbered candidates only, regulation OOF | 0.8362 | — | 0.3864 | 0.06 |

At the operational 0.06 threshold, paragraph F2 optimism is **0.0818 absolute**, about 21% relative, on the full candidate set. Best-sweep optimism is about 0.1035. These are paragraph-level differences; they are not measured differences in requirement-level F2. The saved coefficients exactly match a fresh full-data fit.

Intercept adjustment matches the training mean, 0.040915 predicted versus 0.040823 observed. This does **not** establish calibration: in the 0.20–1.00 prediction bin, mean predicted probability is 0.261 versus observed frequency 0.426, even in-sample.

### Relevance results, replayed from cache

For cache-only replay, the provider was fixed to OpenAI, strong model `gpt-5.5`, bulk model `gpt-5.4-mini`; both remote implementation functions were replaced with a function that raises on a cache miss. The cached profile included the dev image. No new model requests were made.

On 2,805 numbered candidates with 119 positive labels:

| Scores | AUC | Best swept paragraph F2 | Threshold |
|---|---:|---:|---:|
| Decision model OOF | 0.8362 | 0.3864 | 0.06 |
| Bulk relevance alone | 0.9166 | 0.5042 | 0.11 |
| Bulk + OOF model, weight 0.5 | 0.9449 | 0.5728 | 0.12 |
| Strong relevance alone | 0.9716 | 0.7315 | 0.14 |
| Strong + OOF model, weight 0.5 | 0.9740 | 0.7394 | 0.10 |
| Strong + OOF model, weight 0.7 | 0.9765 | 0.7420 | 0.11 |

For strong/0.7 at the current threshold 0.10, the evaluator gives F2 **0.7286**, recall **0.916**, n=272, before the regulation floor. Thus the new source comment's stronger results are supported by cached data. Best thresholds remain selected on this same dev case.

Strong relevance returned 2,804 of 2,805 ids. The evaluator substitutes zero for an omitted score; the pipeline substitutes the decision-model score. That accounts for small boundary differences between diagnostic paths.

### Variability: what was and was not measured

Comparing cached strong-model ratings for evaluation-order batches against pipeline-order batches, which also include R26, gives:

- 2,804 overlapping ids; Pearson correlation **0.9250**; mean absolute probability change **0.01377**.
- **76** paragraph decisions disagree at LLM probability 0.10.
- LLM-only F2 at 0.10 changes from **0.7010 to 0.7152**.
- Using the same OOF model and pipeline missing-id fallback, the 0.7 blend's F2 changes from **0.72764 to 0.72776**, while selected counts change from 273 to 266.

This measures sensitivity across cached batch contexts, not independent repeated sampling of an identical prompt. Identical cache replay is exactly reproducible and says nothing about model variance. The claimed 0.55 correlation for earlier shuffled relevance runs was **not independently reproduced**. A clean repeated-run variance estimate needs fresh, versioned cache namespaces and a frozen configuration.

### Bumper smoke tests

| Fresh run | n | R42 | R127 | R26 | GTR 9 |
|---|---:|---:|---:|---:|---:|
| Plain bumper, deterministic | 530 | 11 | 186 | 64 | 269 |
| Plain bumper, current cached LLM | 105 | 10 | 36 | 26 | 33 |
| Sensors/fog, deterministic | 1,363 | 11 | 186 | 62 | 269 |
| Sensors/fog, current cached LLM | 553 | 8 | 49 | 21 | 30 |

The last row additionally emits R149:177, R148:88, R10:63 and R48:117. Saved artifacts had different counts, including 573 for sensors/fog. Their provenance is insufficient to attribute the changes uniquely.

The claimed bumper decision probabilities of at most about 0.1 are also stale. With the deterministic plain-bumper profile, maxima are R42 **0.142**, R127 **0.349**, R26 **0.349**, GTR 9 **0.348**. Medians remain low, approximately 0.014–0.033. This is evidence of distribution shift, not evidence that probabilities are calibrated for bumpers.

All six saved JSON artifacts inspected passed the in-process official validator and contained only base-version citations. The fresh pipeline outputs also passed its validation. Cached full runs took approximately 0.36–0.60 seconds; these are **not cold API runtimes**. Fresh deterministic runs took approximately 0.36–0.62 seconds excluding scoring.

## 3. Findings

### F1. One-case training and tuning are being mistaken for transfer evidence

**High.** `vlad/brain/decide.py:60`, `:109`, `:140`, `:153`; `vlad/brain/pipeline.py:57`; `vlad/eval/synth.py:91`.

The operational pipeline loads the full-dev fit. Holding out a regulation still retains the same product profile and related lighting functions in training. Tier A examples are gold subsets. Features being generic does not remove the learned association between lamp section structure and gold inclusion. The measured optimism is quantified above.

**Failure:** bumper safety requirements are suppressed because their feature combinations differ from lamp gold; dev improvements conceal that loss.

**Fix:** report OOF dev numbers alongside production-fit numbers; freeze thresholds before any independent labels; obtain a small independently reviewed bumper set. Compare LLM-only selection with blends for new domains. Rank normalization may help relative ordering, but must not be described as probability calibration. A regulation floor is already present and should be evaluated rather than added again.

### F2. Fidelity verification does not verify engineering meaning

**High.** `vlad/brain/verify.py:28`, `:39`; `vlad/brain/rewrite.py:170`.

`faithful` checks whether each numeric string occurs as a substring somewhere in the paragraph or ancestors. It ignores units, signs, relations, modality, conditions and quote provenance. Tested examples accepted: reversing “operate” to “not operate”; adding “at all times”; and introducing “20 cd” when the supplied context contains only “1200 mm”. An invented quote also passed. Numeric failures are dropped, not repaired or replaced with deterministic drafts.

**Failure:** a syntactically valid output states the wrong limit or applicability condition and fails the semantic match. Conversely, harmless numeric formatting changes can silently remove a correct requirement.

**Fix:** verify normalized quote spans; compare quantity/unit/operator tuples and polarity; preserve condition and exception slots; repair or fall back per failed draft. Treat numeric substring checking as a weak diagnostic, not INCOSE compliance or faithfulness certification.

### F3. API failure handling has no bounded completion strategy

**High; operational blocker for unattended use.** `vlad/brain/llm.py:111`, `:132`, `:162`; `vlad/brain/relevance.py:120`; `vlad/brain/rewrite.py:203`; `vlad/brain/pipeline.py:112`.

An injected `TimeoutError` in one rewrite batch aborts `with_llm`. Profile, regulation review and relevance failures also propagate. Installed OpenAI SDK 3.37.0 defaults to two retries and a 600-second read timeout, so “no retries” would be inaccurate; there is no pipeline deadline or recovery after SDK exhaustion. Explicitly selecting a provider without credentials still makes `available()` true.

**Failure:** a single exhausted request near 13:00 prevents a valid final file despite successful earlier batches.

**Fix:** explicit request timeouts, a global run deadline, bounded jittered retries for retryable errors, reduced concurrency after rate limits, and per-batch deterministic fallback. Preserve completed batches. Authentication/schema errors should fail fast with a clearly identified fallback mode, not be retried indefinitely. A missing key only degrades gracefully when provider auto-detection actually resolves to `none`.

### F4. The lexical judge has both semantic and matching defects

**High for evaluation decisions.** `vlad/eval/judge.py:25`, `:55`.

“The lamp shall be red” versus “The lamp shall not be red” scores **0.667**, above the 0.45 threshold. Changing a 7.5 kN limit to 75 kN and a 510 Nm moment to 510 mm still scores **0.810** in a tested example. Conversely, correct standalone paraphrases can lose token overlap.

The assignment maximizes total similarity before thresholding. For `[[.90,.46],[.46,.44]]`, it returns one match; choosing the off-diagonal yields two valid matches. This is not maximum-cardinality matching over accepted pairs. The docstring's `llm_verdicts` function does not exist.

**Failure:** a tuning change appears beneficial because it preserves wording while changing the engineering obligation, or appears harmful because of assignment artifacts.

**Fix:** establish acceptable edges first and maximize match cardinality, breaking ties by similarity. Add numeric/polarity checks and calibrate against expert-reviewed pairs and platform dev scores. No defensible numeric conversion from proxy F2 to platform F2 is available from this review.

### F5. Paragraph probability is not the utility of its emitted requirements

**High.** `vlad/brain/relevance.py:21`, `:127`, `:134`; `vlad/brain/pipeline.py:60`; `vlad/brain/rewrite.py:102`.

The 119 normalized positive paragraphs have gold multiplicities `{1:84, 2:19, 3:9, 4:2, 5:3, 8:1, 10:1}`. One-to-one matching penalizes duplicate, over-split and merged outputs differently. A geometric blend is not automatically calibrated, and the floor deliberately overrides the threshold, including low-confidence definitions or administrative material.

**Failure:** two paragraphs receive the same relevance probability, but one yields one useful row and the other ten mostly redundant rows. Thresholding them identically lowers requirement F2.

**Fix:** select evidence at paragraph level, then assess atomic obligations with inherited applicability conditions. Estimate expected matched obligations per emitted row, and report per-paragraph output counts and duplicate rates. See the cutoff derivation below.

### F6. Regulation review lacks full applicability evidence and consistent decisions

**High.** `vlad/brain/select_regs.py:52`, `:126`, `:164`, `:201`, `:218`.

Selection is dynamic across corpus regulations, which is appropriate. But LLM review sees title, the first 700 scope characters and a consolidation list, not actual transitional provisions or supporting paragraph citations. “Rules learned from expert answers” encode the lamp's device/installation/EMC pattern. The final selection uses `applies`, independently of `p_applies`; missing verdicts silently retain lexical decisions. Empty verdicts were tested and preserve the original four dev regulations.

**Failure:** replacement components or an unusual vehicle category are treated as new consolidated approvals; a missing verdict silently preserves a false negative. A boolean false can exclude a regulation despite a high stated probability.

**Fix:** validate coverage, uniqueness and bounded probabilities; define one decision rule; retry only omitted verdicts. Lexical fallback is a reasonable continuity policy if explicitly flagged, with omitted cases reviewed before upload. Supply scope and transition evidence with labels/pages, and product facts explaining why each applies. Do not change the regulation cutoff to an F2 formula without calibrating what its probability means.

R26 is **a scored false positive for the dev answer**, not inherently an irrelevant regulation: its scope covers M1 external projections, and §6.5 explicitly covers bumpers. Removing its 17 rows from the saved 407-row dev artifact improves regulation F2 to 1.000, page F2 to 0.887 and lexical requirement F2 to 0.635. This is not justification for a global R26 exclusion.

For bumpers, R42 §6.1 addresses post-impact operation; R26 §6.5 addresses bumper geometry. R127 §5.1 and GTR 9 normative §5.1 share several legform limits. Different regulation identifiers remain different citations. The index permits both, so neither a blanket GTR exclusion nor copying both blindly is established by the lamp gold. Review the held-out spec and scope evidence with the regulatory teammate.

### F7. The deterministic profile fails on negation and modest format changes

**High for fallback; medium otherwise.** `vlad/brain/profile.py:16`, `:50`, `:80`, `:138`; `vlad/brain/features.py:106`.

Tested `A bumper for an m1 car, without radar, cameras or LED lamps.` produces no product/category, sets electronics=true, and emits **103 R10 requirements**. A structured minimal “Front bumper / M1 / Bumper fascia” spec emits **zero requirements** because multiword lexical phrases fail to route it. Empty input also returns a valid empty submission. LLM union cannot remove a deterministic false positive such as negated electronics.

**Fix:** retain raw product prose, normalize category case, parse explicit absences, and distinguish present/absent/unknown facts. Use discriminative noun/synonym routing for sparse specs. Add a nonempty-output and core-regulation review gate; schema validity alone is insufficient.

### F8. Prompt and context choices still embed lamp assumptions

**Medium to high.** `vlad/brain/relevance.py:28`, `:72`, `:88`; `vlad/brain/rewrite.py:92`, `:106`, `:161`, `:177`.

The relevance prompt fixes a one-in-25 inclusion prior from the lamp and emphasizes colour/photometry/installation/ESA. All rewrite examples are lamps, including dev regulations. Features themselves are largely generic; the profile regex covers sensors and bumper vocabulary, so calling all features lamp-specific would be inaccurate.

Parent prose is clipped to 60 characters. R42 §6.1.2 gets `6.1 After each impact test made in accordance with the condition`, omitting the procedure/Annex 3 reference. Existing bumper rewrites successfully restore the full condition, but the supplied snippet alone does not prove it. Relevance truncates two gold table paragraphs longer than 1,500 characters; rewrite truncates an R10 paragraph exceeding 4,000.

**Failure:** later constraints, table qualifications or inherited exceptions disappear, particularly across batch boundaries.

**Fix:** include complete governing clauses, definitions and necessary references, plus the structured product profile in rewriting. Replace lamp-specific examples with mixed-domain examples and remove the hard-coded prevalence prior. Split long text at meaningful boundaries while retaining one source paragraph identity.

### F9. Gold coverage checks conceal table-label differences

**Medium.** `vlad/brain/decide.py:34`; `vlad/eval/gold_check.py:25`; `vlad/brain/ingest.py:143`; official `tools/score_local.py:65`.

`gold_check` strips `Table...`, while its denominator counts the original labels. The official normalizer retains table suffixes. Thus “121/121” is parent-coverage evidence, not exact scorer-label coverage. Two gold requirements cite `5.1.4.4.1. Table 3`; one cites `Annex 6 Part 6 3. Table A6-1`. Their exact normalized labels are absent. Correct pages currently rescue page scoring.

The parser also rejects lowercase label bodies, merging genuine children. R42 §5.4.1 (“a circle surrounding the letter E...”) is embedded in §5.4; R150 Annex 6 Part 6 §3.1/§3.2 exposure durations are merged into §3. Flattened tables preserve numbers but not dependable row/column semantics.

**Failure:** a held-out table obligation gets a parent label and the wrong page, losing paragraph rescue; a quantity is associated with the wrong table condition.

**Fix:** use one scorer-compatible citation normalizer, with a separate explicit parent-label mapping for training. Report exact versus parent-resolved coverage. Preserve table records and valid lowercase continuation labels using structural position rather than a capital-letter requirement alone.

### F10. Page spans are useful, but quote-page provenance is not exported

**Medium for UI; lower demonstrated scoring impact.** `vlad/brain/models.py:34`; `vlad/brain/ingest.py:188`; `vlad/brain/pipeline.py:135`.

Export always uses `p.page`, the paragraph-label page. This agrees with documented gold convention and correct paragraph matching usually rescues page differences. It is not necessarily the page of a quoted sentence. `page_at` is not called in the output path and assumes consecutive nonempty pages. A tested paragraph with text on PDF pages 3 and 5 returns page 4 for its second segment.

**Fix:** store `(offset, actual_pdf_page)` boundaries and verified quote spans. Keep the scoring citation convention explicit, and separately provide exact quote page(s) for UI highlighting. Do not globally change page attribution merely because text spans pages.

### F11. Cache invalidation is mostly sound, persistence is not atomic

**Medium.** `vlad/brain/llm.py:74`, `:99`, `:107`, `:117`.

SHA-256 of sorted JSON includes provider, model, system/user prompts, schema and effort. Prompt edits do invalidate it; JSON key ordering is stable. It omits `max_tokens` and local endpoint identity. Reads are unvalidated and writes directly replace the destination contents.

**Failure:** concurrent identical UI requests read a partially written JSON file, or changing a local server while keeping its model name returns another server's cached answer. Distinct normal batch prompts usually have different keys, so this is not evidence that every executor run races.

**Fix:** write to a unique temporary file then atomically replace; validate loaded results; recover from corrupt entries. Include endpoint and generation configuration; store a provenance manifest alongside outputs. Avoid treating cache replay as a stochastic robustness test.

### F12. API request shape is plausible, live support is unverified

**Medium pending cold test.** `vlad/brain/llm.py:132`, `:181`, `:189`.

All four request schemas pass a local check that every object forbids extra properties and requires its declared fields. Regulation ids have an enum. This supports basic strict-schema structure; it does not guarantee full output coverage or remote model support. OpenAI requests reserve twice `max_tokens` for completion plus reasoning, pass effort strings unchanged, and raise on length/refusal. Anthropic also enables a dated beta/fallback configuration. No fresh API call was made to establish compatibility.

**Failure:** a model override, local server or provider beta rejects parameters; reasoning exhausts the cap; a missing/empty result reaches downstream dictionary indexing.

**Fix:** smoke-test the exact configured provider/model/effort/schema before Sunday; set explicit timeouts and output budgets by batch; verify finish reasons and returned schemas. Add provider capability handling rather than assuming every OpenAI-compatible server supports strict JSON schema or every model accepts all efforts. The failed documentation lookup is not evidence that the application key is invalid.

### F13. Human overrides work, but are not a complete review gate

**Medium.** `vlad/brain/pipeline.py:75`, `:149`, `:165`; `vlad/brain/relevance.py:134`.

Known-regulation include/exclude works in tests. Unknown ids such as `UN R999` are silently ignored. Putting a regulation in both lists selects it if it was initially excluded, but excludes it if initially selected. Forcing inclusion does not raise its probability, so feature scoring can still suppress its paragraphs. A floor guarantees paragraph candidates, not emitted requirements.

Only the first 15 choices are exported as metadata. This **does not truncate the regulations used for requirements**, but can hide a forced, low-probability selection from the UI. Missing images are handled without a crash. A synthetic regulation containing only an unnumbered obligation yields no candidates, also without a crash.

**Fix:** reject unknown/conflicting overrides, export all selected decisions and omissions, and show per-regulation paragraph/requirement counts. Require explicit review of selected regulations with zero output. Test zero-numbered and partially missing corpora; `run` only auto-ingests when no base JSONL exists at all.

### F14. Passing validation is necessary but not a completion criterion

**Medium.** `vlad/brain/pipeline.py:145`, `:152`; `vlad/brain/verify.py:64`; `tools/validate.py:21`, `:283`.

Extra fields (`confidence`, `quote`, `regulations`, `profile`) are allowed by default, and all inspected outputs passed. Base-only loading plus `clean` correctly enforce base labels in the examined pipeline. Official validation itself also accepts known latest labels, so keep the independent base check.

The schema permits zero requirements. The in-memory validator does not enforce the serialized 5 MB file limit; that limit is checked when the CLI reads a file. Large quotes/metadata can cross it even below the 5,000-item limit.

**Fix:** always validate the actual final file with the CLI, verify bytes/count/base versions, and require nonempty, reviewed coverage before upload. Use the actual registered team id; `team-00` is only a default.

### F15. Maintainability is acceptable, coverage misses the risky interfaces

**Low for duplication; medium for coverage.** `vlad/brain/rewrite.py:161`; `vlad/brain/relevance.py:72`; `vlad/brain/features.py:69`; `vlad/brain/select_regs.py:41`; `vlad/brain/obligations.py:95`.

Modules are readable and checks pass. Duplicated heading-path helpers share the same truncation policy; normalization helpers differ on hyphens, so consolidation needs an explicit policy. The planned `Obligation`/slot pathway is largely bypassed by `Draft` rewriting. Graph regulation links are counted but do not drive a regulation-expansion loop, and referenced definitions are not systematically passed to the rewriter. Several ignores and `Any` boundaries weaken response validation.

**Failure:** malformed or incomplete LLM output, timeout recovery, threshold behavior or overrides regress without the current 15 tests noticing.

**Fix:** prioritize tests for partial/duplicate ids, contradictory verdicts, provider failures, fidelity mutations, floor/threshold interactions and override conflicts. Consolidate helpers after those behaviors are specified. Do not spend Sunday on a broad refactor or implement graph propagation merely to match the original plan.

### PDF spot-check record

Selected five numbered normative paragraphs per bumper regulation using `random.Random(20261024).sample(..., 5)` independently for each regulation. Compared starts, labels, page headers and end segments against the local base PDFs. All 20 starts and their final page segments matched. Two naive last-80-character searches initially crossed a page boundary; checking the stored final-page segment resolved both.

| Regulation | Sampled label | PDF page(s) |
|---|---|---|
| R42 | Annex 3 2.3.1 | 7 |
| R42 | 5.4 | 2–3 |
| R42 | Annex 3 2.7.4 | 7 |
| R42 | 3.1.5 | 2 |
| R42 | 8.2 | 4 |
| R127 | Annex 6 2.4.4 | 44 |
| R127 | 6.1.2 | 20 |
| R127 | 2.34 | 10–11 |
| R127 | Annex 3 1 | 25 |
| R127 | 2.8 | 3–4 |
| R26 | 9.2 | 11 |
| R26 | 4.1.9 | 3 |
| R26 | Annex 3 2 | 14 |
| R26 | 2.11 | 2 |
| R26 | 6.4.2 | 5–6 |
| GTR 9 | 6.3.1.1.1 | 87 |
| GTR 9 | 3.29 | 75 |
| GTR 9 | 7.4.2 | 103 |
| GTR 9 | 3.5 | 72 |
| GTR 9 | 6.3.1.1.6.3 | 88 |

This is a text/page attribution spot-check, not visual certification of all table cells or complete parser recall. GTR 9's normative numbering restarts on page 71 and is separated from rationale. Current R51 and R49 have 673 and 2,151 numbered records respectively; the older graph doc's unparsed-regulation warning is stale for this parser.

## 4. Formulation critique and experiments

### Keep paragraph evidence selection, make obligation decisions explicit

The decomposition is reasonable: paragraph records preserve citation ownership, and a second step can make legal fragments standalone. It is much better aligned with the task than a shall-only filter. But a paragraph is an evidence unit, not necessarily one independently scored requirement. Governing conditions, alternatives and exceptions must remain attached when obligations split.

With gold parent paragraphs supplied, these reproduced baselines differ substantially:

| Rendering | n | Proxy recall | Proxy F2 |
|---|---:|---:|---:|
| Every verbatim sentence | 304 | 0.826 | 0.738 |
| Only verbatim shall sentences | 137 | 0.532 | 0.563 |
| Current deterministic rewrite | 168 | 0.626 | 0.641 |

The 0.738 result reproduces the claimed “oracle”, but **it is not an upper bound**: a better rewrite or granularity can score higher. The exact claim of 42 gold requirements originating in sentences without “shall” was not established by a documented alignment method. Only one gold output itself lacks “shall”; assigning source sentences by maximum lexical overlap gives 70 source sentences without it, illustrating alignment ambiguity. The ablation above establishes the practical failure of shall-only extraction without relying on the exact count.

For a fixed expected set size G and submitted size N, `F2 = 5 TP / (4 G + N)`. Adding one independent row with expected probability p of a *new* match improves expected F2 when `p > F2 / 5`. That derivation does not justify applying the rule to a paragraph's chance of any citation. A paragraph emitting k rows must contribute expected additional matches exceeding `F2 * k / 5`; duplicates compete for the same one-to-one match. Nor does the derivation make geometric blends or lexical regulation scores calibrated probabilities.

At G=190, an output of 488 rows cannot exceed F2 0.761 even with perfect recall; 778 rows cannot exceed 0.618. A 2.5× gold size is therefore a possible tradeoff, not an optimization target. The current 409-row run is about 2.15× gold, with proxy recall 0.768. Choose output size from measured marginal matches, not a fixed multiple.

### Five concrete experiments

Expected gains below are hypotheses or measured opportunities, not bumper forecasts. Freeze the starting configuration and compare all three score levels.

| Experiment | Expected benefit | Cost | Measurement |
|---|---|---|---|
| 1. Independent bumper labels and transfer ablation | Highest-confidence way to recover domain-specific misses; size unknown. Strong dev blend improves paragraph F2 over strong-only by only about 0.01 at their best thresholds, so test whether its cross-domain suppression is worthwhile. | Expert review of 60–100 stratified paragraphs, including relevant general clauses and absent-feature negatives; cache reuse for model comparisons. | Compare LLM-only, weights 0.5/0.7, rank-normalized model scores and floor on/off using `eval.relevance_check` logic. Evaluate frozen thresholds on a separate adjudicated split; score complete silver cases with `eval.score`. |
| 2. Rendering/atomicity with fixed selected evidence | The gold-paragraph ablation leaves a 0.097 proxy-F2 gap between current deterministic rendering and all sentences; part may be recovered by preserving context and correcting split decisions. Not a guaranteed gain. | One cached rewrite pass per variant plus review of 30 matched/unmatched pairs. | Hold selected paragraph ids fixed. Compare verbatim, minimal EARS and slot-preserving EARS; vary enumeration and multi-shall splits. Run `eval.score`, inspect one-to-one duplicates and use limited platform dev uploads to resolve proxy disagreement. |
| 3. Evidence-based regulation cards | Eliminates known scored false positives without a static list. Removing R26 from the observed saved dev artifact gives about +0.010 requirement F2 and +0.048 regulation F2; held-out benefit unknown. | Extract scope/transitional evidence locally, one regulation-review call, expert review of R42/R26/R127/GTR 9 decisions. | Re-run selection and full `eval.score`; retain included/excluded rationale with actual labels/pages. Do not use lamp gold to forbid a bumper regulation. |
| 4. Context stability and repeated relevance | Reduce threshold flips and missed sections. Current strong cached contexts disagree on 76 raw paragraph decisions; blend F2 was nearly unchanged, so prove a benefit before paying for ensembles. | Three independent relevance runs with distinct audit cache namespaces; optionally an average/top-disagreement adjudication. | Extend `eval.relevance_check` to report Pearson/Spearman, selected-set Jaccard, per-regulation recall and mean/std/min F2 at one frozen threshold. Benchmark a stronger model or larger structural context only if uncertainty remains. |
| 5. Deadline and failure injection | Prevents all-or-nothing loss of a valid submission; no intrinsic F2 uplift on successful cached runs. | Local mocks plus one authorized cold run with the exact Sunday provider configuration. | Inject timeout, rate-limit exhaustion, refusal, malformed cache and missing ids into profile/review/relevance/rewrite. Require a validated fallback file within a fixed wall-clock budget; measure cold duration and fallback score through `eval.score`/`tools/validate.py`. |

For semantic calibration, stratify 30 actual dev pairs across high overlap, low overlap, numeric/condition disputes and duplicate candidates. Have a reviewer decide same scope/condition/constraint, then compare lexical decisions and platform dev headline scores. A 30-pair calibration was not completed in this read-only review; the adversarial examples prove failure modes, not their natural prevalence.

EARS is a sensible rendering preference; nothing here establishes that strict template conformance itself improves matching. Do not force “may”, definitions or alternative compliance routes into unconditional obligations. The graph evidence supports using references as context rather than blindly propagating positive labels; the earlier propagation loss was not independently rerun.

## 5. Sunday go/no-go runbook

### Go when all of these hold

- [ ] Freeze code, model, prompts, provider/model names, relevance tier, weights, thresholds and cache namespace. Save their hashes/settings with the candidate; do not compare changing artifacts as if they were one experiment.
- [ ] At 08:00 obtain the actual held-out spec/image and verify all required base files and parsed corpora are present. Re-profile the actual input; do not reuse the synthetic bumper profile as fact.
- [ ] Review positive, absent and unknown product features. Confirm electronics, lamps/sensors, vehicle category, and unspecified geometry remain distinguishable.
- [ ] Review every selected regulation with scope evidence. Resolve R42/R26/R127/GTR 9 applicability explicitly; retain uncertainty and alternatives without inventing a universal exclusion rule.
- [ ] Confirm per-regulation counts and inspect core sections, including R42 §6.1 children, R26 §6.5 and R127/GTR 9 legform clauses where applicable. A selected regulation with zero output requires attention.
- [ ] Run one cold end-to-end job on the exact configured provider, with a measured deadline and tested recovery. Cache-only speed is insufficient evidence for the claimed 4–5-minute runtime.
- [ ] Keep a complete, separately named deterministic fallback and a reviewed candidate. Avoid overwriting the last accepted file while experimenting.
- [ ] Validate the actual final serialized JSON with `tools/validate.py`; check its size, count, unique ids, base labels, team id and `case_id=heldout-front-bumper`. Spot-check quantities, inherited conditions and exact citations.
- [ ] Use the human include/exclude gate with known, nonconflicting ids, then inspect the resulting requirement counts rather than trusting the override flag alone.
- [ ] Submit early enough to recover. Respect five valid uploads/hour; the **last valid held-out upload counts**. Keep the final reviewed file unless a replacement has concrete evidence of improvement. Uploads close at 13:00.

### No-go triggers

- No valid, nonempty, reviewed held-out file exists before the final upload window.
- Cold API/model/schema compatibility or timeout recovery has never been tested.
- A run exits after a failed batch and no validated fallback is available.
- A core selected regulation has no requirements, citations use latest versions, or the file fails CLI validation/size limits.
- The choice to replace the last valid upload rests only on a higher lexical proxy score or on an unlabelled bumper smoke test.

For the demo and jury, the pipeline structure, parser-owned citations and optional deterministic path are defensible. The current defaults use cloud strong-model relevance and bulk rewriting; local deployability has not been demonstrated here. Reuse the corpus/version/citation machinery for the teammate's sub-goal without changing its ownership or scope. Present the measured limits candidly.

### Reviewed source identifiers

SHA-256 prefixes observed at 17:53:28: `relevance.py b7fb195d7d42ddb1`, `pipeline.py b89f37746335f3f2`, `rewrite.py 6e231036388c4183`, `decide.py 55d59addcafe2a21`, `ingest.py acb05e6641c180d5`, `llm.py b47f5801ba3b2b51`. Later edits require rechecking affected findings and numbers.
