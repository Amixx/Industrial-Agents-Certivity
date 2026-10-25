PRAGMA foreign_keys = ON;

CREATE TABLE regulation (
  id TEXT PRIMARY KEY, number TEXT NOT NULL, version TEXT NOT NULL, title TEXT NOT NULL,
  role_doc TEXT, provenance_id TEXT, UNIQUE(number, version)
);
CREATE TABLE node (
  id TEXT PRIMARY KEY, regulation TEXT NOT NULL REFERENCES regulation(id), version TEXT NOT NULL,
  kind TEXT NOT NULL, label TEXT NOT NULL, number TEXT NOT NULL, annex TEXT, part TEXT,
  appendix TEXT, parent_id TEXT REFERENCES node(id), depth INTEGER NOT NULL, ord INTEGER NOT NULL,
  page INTEGER NOT NULL, page_end INTEGER NOT NULL, heading TEXT, text TEXT NOT NULL,
  page_breaks_json TEXT NOT NULL, UNIQUE(regulation, ord)
);
CREATE TABLE scope_candidate (
  id TEXT PRIMARY KEY, regulation TEXT NOT NULL REFERENCES regulation(id), node_id TEXT REFERENCES node(id),
  rule TEXT NOT NULL, confidence REAL NOT NULL, raw_text TEXT NOT NULL, clean_text TEXT NOT NULL, best INTEGER NOT NULL
);
CREATE TABLE obligation (
  id TEXT PRIMARY KEY, node_id TEXT NOT NULL REFERENCES node(id), ord INTEGER NOT NULL,
  source_kind TEXT NOT NULL, char_start INTEGER NOT NULL, char_end INTEGER NOT NULL,
  page_start INTEGER NOT NULL, page_end INTEGER NOT NULL, quote_raw TEXT NOT NULL,
  text_norm TEXT NOT NULL, modality TEXT NOT NULL, n_modal INTEGER NOT NULL,
  condition_type TEXT NOT NULL, condition_text TEXT, subject_text TEXT, response_text TEXT,
  exception_text TEXT, det_text TEXT, subject_entity_id TEXT, kind TEXT, level TEXT,
  categories_json TEXT, ears_text TEXT, sub INTEGER NOT NULL DEFAULT 0,
  parent_obligation_id TEXT REFERENCES obligation(id), derivation TEXT NOT NULL DEFAULT 'source',
  variant_json TEXT, provenance_id TEXT,
  UNIQUE(node_id, ord, sub), UNIQUE(node_id, char_start, char_end, sub)
);
CREATE TABLE obligation_value (
  obligation_id TEXT NOT NULL REFERENCES obligation(id), ord INTEGER NOT NULL, quantity REAL,
  min REAL, max REAL, unit TEXT, tolerance REAL, raw TEXT NOT NULL,
  PRIMARY KEY(obligation_id, ord)
);
CREATE TABLE obligation_ref (
  obligation_id TEXT NOT NULL REFERENCES obligation(id), target_node_id TEXT, target_regulation TEXT,
  raw TEXT NOT NULL, PRIMARY KEY(obligation_id, raw)
);
CREATE TABLE entity (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL, regulation TEXT NOT NULL REFERENCES regulation(id),
  definition_node_id TEXT REFERENCES node(id), UNIQUE(name, regulation)
);
CREATE TABLE alias (
  entity_id TEXT NOT NULL REFERENCES entity(id), text TEXT NOT NULL, norm TEXT NOT NULL, source TEXT NOT NULL,
  PRIMARY KEY(entity_id, text)
);
CREATE TABLE edge (
  src TEXT NOT NULL, dst TEXT NOT NULL, type TEXT NOT NULL, provenance_id TEXT,
  PRIMARY KEY(src, dst, type)
);
CREATE TABLE attribute (id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, kind TEXT NOT NULL, values_json TEXT NOT NULL);
CREATE TABLE obligation_condition (
  obligation_id TEXT NOT NULL REFERENCES obligation(id), attribute TEXT NOT NULL, op TEXT NOT NULL,
  value TEXT NOT NULL, provenance_id TEXT, PRIMARY KEY(obligation_id, attribute, op, value)
);
CREATE TABLE override (
  target_table TEXT NOT NULL, target_id TEXT NOT NULL, quote_hash TEXT NOT NULL, field TEXT NOT NULL,
  value TEXT NOT NULL, author TEXT NOT NULL, note TEXT NOT NULL,
  PRIMARY KEY(target_table, target_id, quote_hash, field)
);
CREATE TABLE field_provenance (
  target_table TEXT NOT NULL, target_id TEXT NOT NULL, field TEXT NOT NULL, provenance_id TEXT NOT NULL,
  PRIMARY KEY(target_table, target_id, field)
);
CREATE TABLE enrich_rejection (
  prompt_hash TEXT NOT NULL, target TEXT NOT NULL, reason TEXT NOT NULL,
  PRIMARY KEY(prompt_hash, target, reason)
);
CREATE TABLE manifest (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE provenance (
  id TEXT PRIMARY KEY, source TEXT NOT NULL, model TEXT, prompt_hash TEXT, note TEXT NOT NULL
);
CREATE VIRTUAL TABLE fts_node USING fts5(id UNINDEXED, text, heading, tokenize='porter');
CREATE VIRTUAL TABLE fts_obligation USING fts5(id UNINDEXED, text_norm, det_text, tokenize='porter');
CREATE VIRTUAL TABLE fts_alias USING fts5(entity_id UNINDEXED, text, norm, tokenize='porter');
