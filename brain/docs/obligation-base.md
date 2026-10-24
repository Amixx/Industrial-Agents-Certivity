# Obligation base

A compiled, queryable representation of the regulations in one SQLite file: the document tree, the atomic obligations inside it as exact source spans, the entities they constrain and the typed links between them. It is built once, offline, and read by everything downstream (selection, the UI trace view, the change monitor). This plan covers only that representation and how it is built and checked. How a product is matched against it is a separate layer, planned separately. The existing pipeline (`brain.pipeline`) is untouched.

## Why

Measured on the current code (dev case `cases/dev-rear-lamp`, deterministic run):

- The LLM path reads every numbered paragraph of every selected regulation: 2,805 on dev, about 113 relevance calls, about 520k prompt tokens and 110k generated tokens per case. Most of what makes a paragraph citable does not depend on the product: which device it constrains, whether it is a requirement, a limit, a test procedure or administration, which vehicle categories it covers. That judgment should be made once, verified, and stored.
- Gold clusters in sections. If the right depth-2 sections were picked, the candidates drop from 2,805 to about 430 with no gold paragraph lost. The section tree has to be first class:

  | Regulation | Paragraphs | Gold paragraphs | Share kept at depth 1 | depth 2 | depth 3 |
  |---|---|---|---|---|---|
  | R48 | 1,187 | 35 | 58% | 10% | 6% |
  | R10 | 827 | 15 | 14% | 5% | 2% |
  | R148 | 386 | 40 | 74% | 37% | 27% |
  | R150 | 515 | 29 | 71% | 24% | 14% |

- Vocabulary: `synth-a06` ("tail light, brake light, back-up light, reflex reflector") puts R150 at lexical rank 47; `synth-a03` ("retro-reflecting" vs "retro-reflective") puts it at 0.22. Definitions, a small alias list and stemming fix both.
- The extracted scope is wrong for some regulations (R148 falls back to its introduction, GTR 9 to its technical rationale), and footnote boilerplate ("As defined in the Consolidated Resolution ... www.unece.org") eats a third of a 700-character budget.
- Gold granularity: 190 requirements from 119 paragraphs, about 1.6 per paragraph. Most are one sentence each; 13 gold sentences keep two "shall" clauses together; enumerations and table rows also appear. The obligation is the unit the platform judge matches, and its page is what the page level scores.

## Shape

A tree (containment: every node has one parent and a citation is an address in it) with typed edges laid over it (references, supersession; these cross branches and regulations and contain cycles), plus an entity layer the obligations point into.

### Nodes

```
node(id PK, regulation, version, kind, label, number, annex, part, appendix,
     parent_id, depth, ord, page, page_end, heading, text, page_breaks_json)
```

- `id` is the existing `Paragraph.id` (`"UN R148|1.6.0|5.5.7"`), a natural key. `kind`: regulation | annex | part | paragraph. Annex and part headings are nodes of their own kind; numbered paragraphs inside them carry `annex`, `part`, `appendix` and `number` as separate components, plus the display `label` used for citations (`"Annex 6 Part 4 3"`).
- `ord` is the document order within the regulation; every query orders by it.
- `regulation(id PK, number, version, title, role_doc)` holds one row per base regulation; `role_doc` (device_approval | installation | emc | vehicle_approval | light_source | gtr) is a rule's best guess with its provenance.
- `scope_candidate(regulation, node_id, rule, confidence, raw_text, clean_text, best)`: every plausible scope statement (a "Scope" heading, a "This Regulation applies to" sentence, a GTR Part B scope), with footnotes and URLs stripped in `clean_text`. The matching layer chooses; `best` is only a default.

### Obligations

```
obligation(id PK, node_id, ord, source_kind, char_start, char_end, page_start, page_end,
           quote_raw, text_norm, modality, n_modal, condition_type, condition_text,
           subject_text, response_text, exception_text, det_text,
           subject_entity_id, kind, level, categories_json, ears_text)
obligation_value(obligation_id, ord, quantity, min, max, unit, tolerance, raw)
obligation_ref(obligation_id, target_node_id, target_regulation, raw)
```

- An obligation is a stable source span: `id = node_id + "#" + ord`, with `ord` by `char_start`. `source_kind`: sentence | enumeration_item | table_row | telegraphic.
- The unit is the sentence, as in most of the gold. A sentence with two modal clauses stays one obligation with `n_modal = 2`; the report measures how the gold treats those so the matching layer can decide whether to split. An enumeration item ("(a) ...") is its own obligation, carrying its lead-in clause as `condition_text`. A table row with a limit is its own obligation, with the column headers in `text_norm`.
- `quote_raw` is the exact substring `text[char_start:char_end]` of the node. `text_norm` drops list markers and inline headings. Fidelity checks (numbers, units, negation, conditions) run against `quote_raw`, never against rendered text.
- `page_start` and `page_end` come from `Paragraph.page_at(char_start)` and `page_at(char_end)`. Output cites `page_start`; the node's `page` is the fallback.
- `det_text` is the deterministic rendering (`brain.obligations`, `brain.rewrite.deterministic`). `ears_text`, `subject_entity_id`, `kind`, `level` and `categories_json` start as rule guesses or null and are filled by enrichment.
- `kind`: requirement | limit | test_procedure | marking | administrative | conformity_of_production | definition | transitional | informative. `level`: device | installation | esa | vehicle | component.
- `obligation_value` holds numbers with units, ranges and tolerances parsed from `quote_raw` (regex first, enrichment corrects). `obligation_ref` holds the paragraphs and annexes the obligation cites.

### Entities and edges

```
entity(id PK, name, kind, regulation, definition_node_id)   -- id: slug of the normalised name
alias(entity_id, text, norm, source)                          -- source: definition | seed | llm
edge(src, dst, type, provenance_id, PRIMARY KEY (src, dst, type))
```

- Edge types built now, each with a fixed direction:
  - `refers_to`: node → node it cites (from `brain.graph`);
  - `cites_regulation`: node → regulation it names ("UN Regulation No. 148");
  - `defines`: definition node → entity;
  - `supersedes`: consolidated regulation → legacy regulation, from "combines the provisions of ... Nos." (R148 over R4, R6, R7, R23, R38, R50, R77, R87, R91; R149 over R19, R98, R112, R113, R119, R123; R150 over R3, R27, R69, R70, R104).
- Containment is `node.parent_id`, not an edge. Reference loops are computed at query time (strongly connected components over `refers_to`), not stored.
- Deferred to enrichment (WP2): `installs` (installation paragraph → device paragraph it relies on), `tested_by` (requirement → test paragraph or annex), and entity relations (`is_a`, `part_of`), each written with provenance.
- `alias.norm` is lowercased and Porter-stemmed, so "retro-reflecting" and "retro-reflective" meet. The FTS5 tables (`fts_node`, `fts_obligation`, `fts_alias`) use the `porter` tokenizer.

### Provenance, overrides and determinism

```
provenance(id PK, source, model, prompt_hash, note)           -- source: parser | rule | llm | human
override(target_table, target_id, quote_hash, field, value, author, note)
manifest(key PK, value)   -- corpus file hashes, schema hash, aliases hash, git commit of brain/
```

- All ids are natural or content-derived keys with `UNIQUE` constraints; no autoincrement ids appear in any key. Inserts and queries use a stable `ORDER BY`. Row hashes for the determinism test exclude nothing because no row carries a timestamp.
- A correction is an `override` row keyed by the stable id plus the hash of its `quote_raw`. A rebuild never deletes overrides; it re-applies them after the build and reports any whose target no longer exists or whose quote changed. Precedence: human over llm over rule.

### Queries (`brain.kb.query`)

`toc(reg, depth)`, `subtree(node)`, `ancestors(node)`, `heading_path(node)`, `obligations(nodes)`, `ref_closure(nodes, max_hops)`, `loop_partners(node)`, `search(text)`, `entities_for(terms)`, `superseded_by(reg)`, `scope(reg)`.

`ref_closure` is a recursive CTE with `UNION` (deduplicating) and a hop counter bounded by `max_hops`, so it terminates on cycles.

## Constraints for all work

- Do not edit `brain/brain/pipeline.py`, `select_regs.py`, `llm.py`, `eval/suite.py` or `eval/results.csv`: others are changing them. Import from them read-only. New code lives in `brain/brain/kb/` and `brain/eval/kb_*.py`. Small, backwards-compatible additions to `brain/brain/obligations.py` (returning offsets) are allowed if needed; prefer a new function there over changing an existing signature.
- No paid LLM calls. Never set `BRAIN_LLM`. LLM-dependent code is tested with a fake `complete_json` (monkeypatch). Real enrichment runs happen later, after an approved cost estimate.
- The SQLite file is generated: `brain/data/kb.sqlite`, gitignored. Overrides live in a checked-in `brain/data/kb_overrides.jsonl` that the build loads.
- Follow `DESIGN.md` copy rules in docs. Run `make check` and `make test` before committing.

## Work packages

### WP1a (first, the critical gate): schema, deterministic build, spans and pages

Files: `brain/brain/kb/{__init__,schema.sql,build.py,spans.py}`, `brain/tests/test_kb_build.py`, `brain/tests/fixtures/kb/*`, `brain/.gitignore`.

- `python -m brain.kb.build` builds all 56 base regulations in under two minutes: regulation, node, obligation (with spans, pages, values, refs), entity from definitions, the four edge types, provenance, manifest, overrides applied. The full schema above is created here, including the enrichment columns and tables, so later packages do not change it.
- Tests, each on a real paragraph from the corpus:
  - a paragraph that crosses a page break: an obligation after the break gets the later page;
  - an enumeration with a lead-in clause; a table row with a limit; a sentence with two "shall" clauses; a telegraphic line ("In height: not less than 250 mm ..."); an annex and an annex-part citation;
  - `quote_raw` is always an exact substring of the node text;
  - every dev gold citation resolves to a node, and every dev gold requirement maps to exactly one obligation span with the gold's page, or is listed as unsupported with a cause;
  - two builds produce identical row hashes; a reference cycle does not break the build.
- Prints the dev gold span coverage (supported, unsupported by cause). Target: at least 95% of the 190 mapped to the right span and page.

### WP1b (after WP1a): queries, vocabulary, scope, report

Files: `brain/brain/kb/{query.py,ontology.py,scope.py}`, `brain/data/aliases.json`, `brain/eval/kb_report.py`, `brain/tests/test_kb_query.py`. It adds two calls to `build.py` (aliases with FTS, scope candidates) and nothing else there.

- The query API above. `aliases.json` is a seed list of lighting, bumper and EMC vocabulary (tail light, brake light, back-up light, reflex reflector, bumper, ...), mapped to entity ids.
- Tests: `ref_closure` on a cycle with repeated nodes and a disconnected branch; `entities_for(["retro-reflecting"])` and `entities_for(["brake light"])` find the right entities; `scope("UN R148")` and `scope("UN GTR 9")` return a real scope statement.
- `kb_report.py` prints, for dev and every `synthetic/cases/*` case: span coverage, obligations per gold paragraph against gold requirements per paragraph, how the gold treats two-clause sentences and enumerations, the depth-1/2/3 section table above, the best scope candidate and `role_doc` for R48, R148, R150, R10, R42, R127, GTR 9, R26, R149, and the rank of every gold regulation when the case's spec terms go through `entities_for` and are matched against scope candidates, top-level headings and entity names (target: every gold regulation within the top 12, including `synth-a06` and `synth-a03`).

### WP2 (after WP1a, in parallel with WP1b): enrichment pass

Files: `brain/brain/kb/enrich.py`, `brain/tests/test_kb_enrich.py`.

- `python -m brain.kb.enrich --regs "UN R48" "UN R148" ... --tier strong|bulk [--estimate]`. `--estimate` prints calls, prompt tokens and generated tokens per regulation without calling anything.
- Batches by depth-2 section, about 20 obligations per call. The prompt holds the heading path, the parent clause, each obligation's `quote_raw`, the regulation's entity list and the attribute list; the response uses positional ids, so nothing long is echoed back.
- Tags per obligation: `subject_entity_id` (or a proposed new entity), `kind`, `level`, `categories_json`, `response_text`, `exception_text`, corrected `obligation_value` rows, `ears_text`. Per section: `tested_by` and `installs` edges, aliases, `is_a` and `part_of`. Structured conditions go into `obligation_condition(obligation_id, attribute, op, value, provenance_id)` over `attribute(id, name, kind, values_json)`, both created in WP1a.
- Validation rejects a tag whose `ears_text` adds or drops a number or a negation relative to `quote_raw`, or whose entity or attribute id is unknown. Every write carries a provenance row; it never overwrites an `override`. Resumable: skips obligations already tagged under the same prompt hash. Runs through `brain.llm.complete_json`, so the disk cache, providers and `BRAIN_LLM` gating apply.
- `kb_report.py --enriched` (added after WP1b lands): tag coverage per regulation, the kind and level distribution of gold obligations against all obligations, and how often a gold obligation's subject entity is one the case spec names.
- Tests against a fake `complete_json`: the writes, the validation, the resume, override precedence, the estimate.

### WP3 (gated, after WP2): enrichment run

- `--estimate` first, approved by the owner before any call. Scale: the 13 regulations a lamp or a front bumper can touch (R48, R148, R150, R10, R42, R127, GTR 9, R26, R149, R152, R79, R94, R51) hold 6,892 paragraphs, 5,865 modal sentences and about 520k tokens of text; the whole corpus is about 1.84M tokens.
- Run, then `kb_report.py --enriched` on dev and the synthetic suite, and a manual read of 30 random tags per regulation.

## Order

WP1a, then WP1b and WP2 in parallel, then WP3. Each package lands as its own commit on the `obligation-base` branch.

## Risks

- Every gold set is a lamp, so tag quality is only measured on lighting and EMC regulations. Read the bumper regulations' tags by hand.
- Tables in the PDFs may be flattened by extraction; WP1a's unsupported list shows how many gold requirements that costs.
- The enrichment model may invent entities or conditions. Validation, provenance and overrides make that visible and reversible.
