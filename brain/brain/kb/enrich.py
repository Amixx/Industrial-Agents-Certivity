"""Enrichment pass: model tags for the obligations of the knowledge base.

Obligations are batched by depth-2 section, about BATCH per call: a larger section is split
evenly, consecutive smaller sections share a call. The prompt lists each obligation's
`quote_raw` under a positional id (o1, o2, ...), the regulation's defined entities (e1, e2, ...)
and the condition attributes; the answer refers to them by those ids only.

Answers come from `brain.llm.complete_json`, or from files (`--import`), and pass the same
validation either way. Every write carries a provenance row `llm:<model>:<prompt hash>`; a field
set by an override is never written; a batch whose prompt hash already has a provenance row is
skipped.

Answer files (`--import FILE_OR_DIR --source-model NAME`): one JSON object per batch, either one
`.json` file per batch or one object per line of a `.jsonl` file:

    {"batch_id": "<from the exported batch>", "prompt_hash": "<likewise>", "answer": {...}}

`answer` follows the `schema` in the exported batch file (`--export-batches DIR`), which also
holds the system prompt and the batch content. Other keys are ignored, so an exported file with
`answer` added is a valid answer file. Per obligation the answer gives:

    {"id": "o1", "subject": "e3" | "n1" | null, "kind": "requirement", "level": "device",
     "categories": ["M1"], "response": "...", "exception": null, "ears": "...",
     "values": null | [{"raw": "250 mm", "quantity": 250, "min": null, "max": null,
                        "unit": "mm", "tolerance": null}],
     "conditions": [{"attribute": "colour", "op": "eq", "value": "red"}],
     "derived": [{"derivation": "clause" | "variant", "text": "...",
                  "variant": [{"attribute": "device_class", "value": "IA"}]}]}

and per batch `new_entities` (n1, n2, ...), `tested_by`, `installs`, `aliases` and `relations`.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .. import llm
from ..obligations import modality
from . import spans
from .build import DB, _apply_overrides, _hash, _load_overrides, _slug

BATCH = 20
CHARS_PER_TOKEN = 4
# Generated tokens per obligation: the EARS text is about as long as the quote, plus the tags.
GEN_TAG_TOKENS = 80
GEN_BATCH_TOKENS = 150

KINDS = [
    "requirement",
    "limit",
    "test_procedure",
    "marking",
    "administrative",
    "conformity_of_production",
    "definition",
    "transitional",
    "informative",
]
LEVELS = ["device", "installation", "esa", "vehicle", "component"]
ENTITY_KINDS = ["device", "component", "system", "vehicle", "function", "other"]
OPS = ["eq", "ne", "in", "not_in", "lt", "le", "gt", "ge"]
VEHICLE_CATEGORIES = [
    "M", "M1", "M2", "M3", "N", "N1", "N2", "N3", "O", "O1", "O2", "O3", "O4",
    "L", "L1", "L2", "L3", "L4", "L5", "L6", "L7", "T", "R", "S",
]  # fmt: skip
# (id, kind, values); an empty value list accepts any value.
ATTRIBUTES: list[tuple[str, str, list[str]]] = [
    ("vehicle_category", "enum", VEHICLE_CATEGORIES),
    ("colour", "enum", ["white", "red", "amber", "selective yellow", "blue", "green"]),
    ("device_class", "text", []),
    ("device_category", "text", []),
    (
        "light_source",
        "enum",
        ["filament", "LED", "gas-discharge", "replaceable", "non-replaceable"],
    ),
    ("side", "enum", ["front", "rear", "side"]),
    ("max_mass_kg", "number", []),
    ("design_speed_kmh", "number", []),
]

_NUM = re.compile(r"\d+(?:[.,]\d+)*")
_NEG = re.compile(
    r"\b(?:not|never|nor|neither|none|without|cannot|prohibited)\b|n't\b|\bno\b(?!\.\s*\d)", re.I
)

_SYSTEM = """You tag the obligations of one UN Regulation (or GTR) for a type-approval knowledge
base. The tags describe the regulation text itself, independent of any product. Each obligation
is an exact source span with a positional id (o1, o2, ...). Answer for every obligation id.

Per obligation:
- subject: the entity the obligation constrains, as an entity id from the list (e1, e2, ...), or
  a new entity you declare in new_entities (n1, n2, ...), or null when no entity fits.
- kind: requirement (a design or behaviour requirement), limit (a numeric limit or tolerance),
  test_procedure (how a test is done), marking, administrative (approval procedure, forms,
  communication), conformity_of_production, definition, transitional, informative.
- level: device (the approved device or component type), installation (fitting on the vehicle),
  esa (electrical/electronic sub-assembly), vehicle (the whole vehicle), component (a part of
  the device).
- categories: the vehicle categories the obligation covers when the text or its section says
  so (M1, N, O, L3, ...), else [].
- response: the required behaviour or property, copied from the source; exception: the
  "except"/"unless"/"however" part, copied, or null.
- ears: one standalone requirement in EARS style ("When <trigger>, the <subject> shall
  <response>."), with a minimal edit of the source: keep every number, unit, reference and
  negation exactly as written, and add none.
- values: null when the numbers with units are already parsed correctly, else every value with
  a unit: raw (copied from the source), quantity or min/max, unit, tolerance.
- conditions: structured preconditions over the attributes listed (attribute, op, value).
- derived: usually []. Two cases:
  - clause: the sentence holds several independent requirements ("shall meet A, B and C" or
    two "shall" clauses); give each as a standalone sentence that repeats the shared condition.
  - variant: the text is generic or tabular and states different values per class, colour,
    vehicle category or light source; give one sentence per attribute combination, bound to
    those attribute values in `variant`.
  Derived text uses only numbers and negations that appear in the source span, copied
  character for character.

Per batch:
- new_entities: things obligations constrain that the entity list lacks (ref n1, n2, ...).
- tested_by: an obligation and the paragraph or annex label that holds its test ("Annex 4",
  "6.2"); installs: an installation obligation and the device paragraph it relies on, with its
  regulation if another one.
- aliases: other names the text uses for an entity; relations: is_a or part_of between
  entities.
Leave out anything you are unsure of."""


def _nullable(schema: dict[str, Any]) -> dict[str, Any]:
    return {"anyOf": [schema, {"type": "null"}]}


def _object(**props: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": props,
        "required": list(props),
        "additionalProperties": False,
    }


_STR = {"type": "string"}
_NUMBER = {"type": "number"}


def _array(item: dict[str, Any]) -> dict[str, Any]:
    return {"type": "array", "items": item}


SCHEMA = _object(
    new_entities=_array(
        _object(ref=_STR, name=_STR, kind={"type": "string", "enum": ENTITY_KINDS})
    ),
    obligations=_array(
        _object(
            id=_STR,
            subject=_nullable(_STR),
            kind={"type": "string", "enum": KINDS},
            level={"type": "string", "enum": LEVELS},
            categories=_array(_STR),
            response=_nullable(_STR),
            exception=_nullable(_STR),
            ears=_STR,
            values=_nullable(
                _array(
                    _object(
                        raw=_STR,
                        quantity=_nullable(_NUMBER),
                        min=_nullable(_NUMBER),
                        max=_nullable(_NUMBER),
                        unit=_nullable(_STR),
                        tolerance=_nullable(_NUMBER),
                    )
                )
            ),
            conditions=_array(
                _object(attribute=_STR, op={"type": "string", "enum": OPS}, value=_STR)
            ),
            derived=_array(
                _object(
                    derivation={"type": "string", "enum": ["clause", "variant"]},
                    text=_STR,
                    variant=_array(_object(attribute=_STR, value=_STR)),
                )
            ),
        )
    ),
    tested_by=_array(_object(obligation=_STR, target=_STR)),
    installs=_array(_object(obligation=_STR, regulation=_nullable(_STR), target=_STR)),
    aliases=_array(_object(entity=_STR, text=_STR)),
    relations=_array(
        _object(type={"type": "string", "enum": ["is_a", "part_of"]}, src=_STR, dst=_STR)
    ),
)


def conforms(value: Any, schema: dict[str, Any]) -> bool:
    """Whether `value` matches the subset of JSON Schema that SCHEMA uses."""
    if "anyOf" in schema:
        return any(conforms(value, s) for s in schema["anyOf"])
    kind = schema["type"]
    if kind == "null":
        return value is None
    if kind == "string":
        return isinstance(value, str) and value in schema.get("enum", [value])
    if kind == "number":
        return isinstance(value, int | float) and not isinstance(value, bool)
    if kind == "array":
        return isinstance(value, list) and all(conforms(v, schema["items"]) for v in value)
    return (
        isinstance(value, dict)
        and set(value) == set(schema["properties"])
        and all(conforms(value[k], s) for k, s in schema["properties"].items())
    )


@dataclass
class Batch:
    id: str
    regulation: str
    obligations: list[str]  # obligation ids; o1 is obligations[0]
    entities: list[str]  # entity ids; e1 is entities[0]
    content: str
    quotes: dict[str, str]
    prompt_hash: str = field(init=False)

    def __post_init__(self) -> None:
        self.prompt_hash = prompt_hash(_SYSTEM, self.content, SCHEMA)


def prompt_hash(system: str, content: str, schema: dict[str, Any]) -> str:
    return _hash(
        json.dumps({"system": system, "content": content, "schema": schema}, sort_keys=True)
    )


def _section(path: list[str], node_id: str) -> str:
    return path[1] if len(path) >= 2 else node_id


def _chunks(items: list[Any], size: int) -> list[list[Any]]:
    n = -(-len(items) // size)
    step = -(-len(items) // n)
    return [items[i : i + step] for i in range(0, len(items), step)]


def _attribute_lines(conn: sqlite3.Connection) -> str:
    lines = []
    for aid, _, values in attributes(conn):
        lines.append(f"{aid}: {', '.join(values) if values else '(any value)'}")
    return "\n".join(lines)


def attributes(conn: sqlite3.Connection) -> list[tuple[str, str, list[str]]]:
    known = {aid: (aid, kind, values) for aid, kind, values in ATTRIBUTES}
    for aid, kind, values_json in conn.execute("SELECT id, kind, values_json FROM attribute"):
        known.setdefault(aid, (aid, kind, json.loads(values_json)))
    return [known[k] for k in sorted(known)]


def batches(conn: sqlite3.Connection, regulation: str) -> list[Batch]:
    """The enrichment batches of one regulation, in document order."""
    nodes = {
        r["id"]: r
        for r in conn.execute(
            "SELECT id, label, heading, text, parent_id, kind, ord FROM node WHERE regulation=?",
            (regulation,),
        )
    }
    title = conn.execute("SELECT title FROM regulation WHERE id=?", (regulation,)).fetchone()
    if title is None:
        raise SystemExit(f"unknown regulation {regulation}")
    entities = conn.execute(
        "SELECT id, name FROM entity WHERE regulation=? AND definition_node_id IS NOT NULL "
        "ORDER BY id",
        (regulation,),
    ).fetchall()
    rows = conn.execute(
        "SELECT o.id, o.node_id, o.source_kind, o.quote_raw, o.condition_text "
        "FROM obligation o JOIN node n ON n.id = o.node_id "
        "WHERE n.regulation=? AND o.derivation='source' ORDER BY n.ord, o.ord",
        (regulation,),
    ).fetchall()

    def path(node_id: str) -> list[str]:
        out = []
        parent = nodes[node_id]["parent_id"]
        while parent in nodes:
            out.append(parent)
            parent = nodes[parent]["parent_id"]
        return out[::-1]

    sections: list[tuple[str, list[sqlite3.Row]]] = []
    for row in rows:
        key = _section(path(row["node_id"]), row["node_id"])
        if sections and sections[-1][0] == key:
            sections[-1][1].append(row)
        else:
            sections.append((key, [row]))
    groups: list[list[sqlite3.Row]] = []
    packable = False
    for _, items in sections:
        if len(items) > BATCH:
            groups.extend(_chunks(items, BATCH))
            packable = False
        elif packable and len(groups[-1]) + len(items) <= BATCH:
            groups[-1].extend(items)
        else:
            groups.append(list(items))
            packable = True

    def heading(node_id: str) -> str:
        n = nodes[node_id]
        return f"{n['label']} {n['heading'] or n['text'][:60]}".strip()

    entity_lines = "\n".join(f"e{i + 1}: {e['name']}" for i, e in enumerate(entities))
    head = (
        f"Regulation: {regulation} ({title[0]})\n\nEntities:\n{entity_lines or '(none)'}\n\n"
        f"Attributes:\n{_attribute_lines(conn)}\n"
    )
    out = []
    for i, group in enumerate(groups):
        parts = []
        current = None
        for j, row in enumerate(group):
            node_id = row["node_id"]
            if node_id != current:
                current = node_id
                node = nodes[node_id]
                parent = nodes.get(node["parent_id"])
                parts.append(f"\nParagraph {node['label']}")
                ancestors = path(node_id)
                if ancestors:
                    parts.append(f"Heading path: {' > '.join(heading(n) for n in ancestors)}")
                if parent is not None and parent["kind"] == "paragraph":
                    parts.append(f"Parent clause: {parent['text'][:300]}")
            lead = (
                f" (lead-in: {row['condition_text']})"
                if row["source_kind"] == "enumeration_item" and row["condition_text"]
                else ""
            )
            parts.append(f"o{j + 1} [{row['source_kind']}]{lead}: {row['quote_raw']}")
        content = head + "\n".join(parts) + "\n\nAnswer for every obligation id."
        out.append(
            Batch(
                id=f"{regulation}|{i:04d}",
                regulation=regulation,
                obligations=[r["id"] for r in group],
                entities=[e["id"] for e in entities],
                content=content,
                quotes={r["id"]: r["quote_raw"] for r in group},
            )
        )
    return out


def numbers(text: str) -> set[str]:
    return {m.replace(",", ".") for m in _NUM.findall(text)}


def quantities(text: str) -> set[float]:
    """Every reading of the numbers in text, with a comma as decimal mark or as thousands
    separator; paragraph labels such as 4.1.1 have none."""
    out: set[float] = set()
    for m in _NUM.findall(text):
        for s in (m.replace(",", "."), m.replace(",", "")):
            try:
                out.add(float(s))
            except ValueError:
                pass
    return out


def measured(text: str) -> set[str]:
    """The numbers of text that carry a unit; references, figure numbers and footnote marks
    have none."""
    return {n for v in spans.values(text) for n in numbers(v[5])}


def negations(text: str) -> int:
    return len(_NEG.findall(text))


def fidelity(text: str, quote: str, *, exact: bool) -> str | None:
    """Why `text` misquotes the numbers or negations of `quote`, or None."""
    added = numbers(text) - numbers(quote)
    if added:
        return f"adds numbers {sorted(added)}"
    dropped = (numbers(quote) - numbers(text)) & measured(quote)
    if exact and dropped:
        return f"drops numbers {sorted(dropped)}"
    if negations(text) > negations(quote):
        return "adds a negation"
    if exact and negations(text) < negations(quote):
        return "drops a negation"
    return None


@dataclass
class Result:
    written: int = 0
    derived: int = 0
    edges: int = 0
    rejected: list[tuple[str, str]] = field(default_factory=list)
    skipped: int = 0


class Writer:
    """Validates one answer against its batch and writes it."""

    def __init__(self, conn: sqlite3.Connection, model: str) -> None:
        self.conn = conn
        self.model = model
        self.attrs = {aid: values for aid, _, values in attributes(conn)}
        self.overrides = _load_overrides()

    def done(self, batch: Batch) -> bool:
        return (
            self.conn.execute(
                "SELECT 1 FROM provenance WHERE source='llm' AND prompt_hash=?",
                (batch.prompt_hash,),
            ).fetchone()
            is not None
        )

    def _protected(self, oid: str, column: str) -> bool:
        return (
            self.conn.execute(
                "SELECT 1 FROM provenance WHERE id=?", (f"override:{oid}:{column}",)
            ).fetchone()
            is not None
        )

    def _set(self, prov: str, oid: str, column: str, value: Any) -> None:
        if self._protected(oid, column):
            return
        self.conn.execute(f"UPDATE obligation SET {column}=? WHERE id=?", (value, oid))
        self.conn.execute(
            "INSERT OR REPLACE INTO field_provenance VALUES ('obligation',?,?,?)",
            (oid, column, prov),
        )

    def _condition_error(self, attribute: str, value: str) -> str | None:
        if attribute not in self.attrs:
            return f"unknown attribute {attribute}"
        allowed = self.attrs[attribute]
        if allowed and any(v.strip() not in allowed for v in value.split(",")):
            return f"unknown value {value} for {attribute}"
        return None

    def _obligation_error(
        self, item: dict[str, Any], quote: str, refs: dict[str, str]
    ) -> str | None:
        if item["subject"] is not None and item["subject"] not in refs:
            return f"unknown entity {item['subject']}"
        bad = [c for c in item["categories"] if c not in VEHICLE_CATEGORIES]
        if bad:
            return f"unknown categories {bad}"
        for c in item["conditions"]:
            error = self._condition_error(c["attribute"], c["value"])
            if error:
                return error
        found = quantities(quote)
        for v in item["values"] or []:
            if v["raw"] not in quote:
                return f"value {v['raw']!r} not in quote"
            plus_minus = "±" in v["raw"]
            for x in (v["quantity"], v["min"], v["max"], v["tolerance"]):
                if x is None or (plus_minus and x == 0):
                    continue
                if not any(abs(n - abs(x)) < 1e-9 for n in found):
                    return f"value {x} not in quote"
        return fidelity(item["ears"], quote, exact=True)

    def _derived_error(self, d: dict[str, Any], quote: str) -> str | None:
        if d["derivation"] == "variant" and not d["variant"]:
            return "variant without attribute values"
        if d["derivation"] == "clause" and d["variant"]:
            return "clause with attribute values"
        for v in d["variant"]:
            error = self._condition_error(v["attribute"], v["value"])
            if error:
                return error
        return fidelity(d["text"], quote, exact=False)

    def _clear_derived(self, oid: str) -> None:
        ids = [
            r[0]
            for r in self.conn.execute(
                "SELECT id FROM obligation WHERE parent_obligation_id=?", (oid,)
            )
        ]
        for did in ids:
            for sql in (
                "DELETE FROM obligation_condition WHERE obligation_id=?",
                "DELETE FROM obligation_value WHERE obligation_id=?",
                "DELETE FROM field_provenance WHERE target_table='obligation' AND target_id=?",
                "DELETE FROM fts_obligation WHERE id=?",
                "DELETE FROM obligation WHERE id=?",
            ):
                self.conn.execute(sql, (did,))

    def _derive(self, prov: str, parent: sqlite3.Row, items: list[dict[str, Any]]) -> list[str]:
        self._clear_derived(parent["id"])
        made = []
        for n, d in enumerate(items, start=1):
            did = f"{parent['id']}/{n}"
            text = d["text"]
            ctype, ctext = spans.condition(text)
            variant = {v["attribute"]: v["value"] for v in d["variant"]} or None
            self.conn.execute(
                "INSERT INTO obligation (id, node_id, ord, source_kind, char_start, char_end, "
                "page_start, page_end, quote_raw, text_norm, modality, n_modal, condition_type, "
                "condition_text, det_text, subject_entity_id, kind, level, categories_json, "
                "ears_text, sub, parent_obligation_id, derivation, variant_json, provenance_id) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    did,
                    parent["node_id"],
                    parent["ord"],
                    parent["source_kind"],
                    parent["char_start"],
                    parent["char_end"],
                    parent["page_start"],
                    parent["page_end"],
                    parent["quote_raw"],
                    text,
                    modality(text),
                    len(re.findall(r"\b(?:shall|must|may)\b", text, re.I)),
                    ctype,
                    ctext,
                    text,
                    parent["subject_entity_id"],
                    parent["kind"],
                    parent["level"],
                    parent["categories_json"],
                    text,
                    n,
                    parent["id"],
                    d["derivation"],
                    json.dumps(variant, sort_keys=True) if variant else None,
                    prov,
                ),
            )
            self.conn.execute("INSERT INTO fts_obligation VALUES (?,?,?)", (did, text, text))
            for attribute, value in sorted((variant or {}).items()):
                self.conn.execute(
                    "INSERT OR IGNORE INTO obligation_condition VALUES (?,?,?,?,?)",
                    (did, attribute, "eq", value, prov),
                )
            for order, value in enumerate(spans.values(text)):
                self.conn.execute(
                    "INSERT INTO obligation_value VALUES (?,?,?,?,?,?,?,?)", (did, order, *value)
                )
            made.append(did)
        return made

    def _node(self, regulation: str, label: str) -> str | None:
        label = label.strip().rstrip(".")
        row = self.conn.execute(
            "SELECT id FROM node WHERE regulation=? AND label IN (?, ?)",
            (regulation, label, label + "."),
        ).fetchone()
        return row[0] if row else None

    def apply(self, batch: Batch, answer: Any, result: Result) -> None:
        prov = f"llm:{self.model}:{batch.prompt_hash}"
        if not isinstance(answer, dict) or set(answer) != set(SCHEMA["properties"]):
            self.conn.execute(
                "INSERT OR IGNORE INTO enrich_rejection VALUES (?,?,?)",
                (batch.prompt_hash, batch.id, "malformed answer"),
            )
            result.rejected.append((batch.id, "malformed answer"))
            return
        rejected: list[tuple[str, str]] = []
        refs = {f"e{i + 1}": eid for i, eid in enumerate(batch.entities)}
        positions = {f"o{i + 1}": oid for i, oid in enumerate(batch.obligations)}
        new_entities = []
        for item in answer.get("new_entities", []):
            if not conforms(item, SCHEMA["properties"]["new_entities"]["items"]):
                rejected.append((batch.id, "malformed new entity"))
                continue
            eid = f"{batch.regulation}:{_slug(item['name'])}"
            if not re.fullmatch(r"n\d+", item["ref"]) or not _slug(item["name"]):
                rejected.append((batch.id, f"bad new entity {item['ref']}"))
                continue
            refs[item["ref"]] = eid
            new_entities.append((eid, item))
        self.conn.execute(
            "INSERT OR REPLACE INTO provenance VALUES (?,?,?,?,?)",
            (prov, "llm", self.model, batch.prompt_hash, f"enrichment batch {batch.id}"),
        )
        for aid, kind, values in ATTRIBUTES:
            self.conn.execute(
                "INSERT OR IGNORE INTO attribute VALUES (?,?,?,?)",
                (aid, aid, kind, json.dumps(values)),
            )
        used: set[str] = set()
        tagged: dict[str, dict[str, Any]] = {}
        item_schema = SCHEMA["properties"]["obligations"]["items"]
        for item in answer.get("obligations", []):
            if not conforms(item, item_schema) or item["id"] not in positions:
                rejected.append((batch.id, "malformed obligation tag"))
                continue
            oid = positions[item["id"]]
            if oid in tagged:
                rejected.append((oid, "tagged twice"))
                continue
            error = self._obligation_error(item, batch.quotes[oid], refs)
            if error:
                rejected.append((oid, error))
                continue
            tagged[oid] = item
        for oid in batch.obligations:
            if oid not in tagged:
                if not any(target == oid for target, _ in rejected):
                    rejected.append((oid, "no tag"))
                continue
            item = tagged[oid]
            if item["subject"]:
                used.add(item["subject"])
            for column, value in (
                ("subject_entity_id", refs.get(item["subject"] or "")),
                ("kind", item["kind"]),
                ("level", item["level"]),
                ("categories_json", json.dumps(sorted(set(item["categories"])))),
                ("response_text", item["response"]),
                ("exception_text", item["exception"]),
                ("ears_text", item["ears"]),
            ):
                self._set(prov, oid, column, value)
            if item["values"] is not None:
                self.conn.execute("DELETE FROM obligation_value WHERE obligation_id=?", (oid,))
                for order, v in enumerate(item["values"]):
                    self.conn.execute(
                        "INSERT INTO obligation_value VALUES (?,?,?,?,?,?,?,?)",
                        (
                            oid,
                            order,
                            v["quantity"],
                            v["min"],
                            v["max"],
                            v["unit"],
                            v["tolerance"],
                            v["raw"],
                        ),
                    )
                self.conn.execute(
                    "INSERT OR REPLACE INTO field_provenance VALUES ('obligation_value',?,'*',?)",
                    (oid, prov),
                )
            self.conn.execute(
                "DELETE FROM obligation_condition "
                "WHERE obligation_id=? AND provenance_id LIKE 'llm:%'",
                (oid,),
            )
            for c in item["conditions"]:
                self.conn.execute(
                    "INSERT OR IGNORE INTO obligation_condition VALUES (?,?,?,?,?)",
                    (oid, c["attribute"], c["op"], c["value"], prov),
                )
            derived = []
            for d in item["derived"]:
                error = self._derived_error(d, batch.quotes[oid])
                if error:
                    rejected.append((oid, f"derived: {error}"))
                else:
                    derived.append(d)
            parent = self.conn.execute("SELECT * FROM obligation WHERE id=?", (oid,)).fetchone()
            made = self._derive(prov, parent, derived)
            result.derived += len(made)
            result.written += 1
        for key, schema_key in (("aliases", "aliases"), ("relations", "relations")):
            for item in answer.get(key, []):
                if not conforms(item, SCHEMA["properties"][schema_key]["items"]):
                    rejected.append((batch.id, f"malformed {key}"))
                    continue
                ends = [item["entity"]] if key == "aliases" else [item["src"], item["dst"]]
                if any(e not in refs for e in ends):
                    rejected.append((batch.id, f"{key}: unknown entity {ends}"))
                    continue
                used.update(ends)
        for eid, item in new_entities:
            if item["ref"] not in used:
                continue
            self.conn.execute(
                "INSERT OR IGNORE INTO entity VALUES (?,?,?,?,?)",
                (eid, item["name"], item["kind"], batch.regulation, None),
            )
            self.conn.execute(
                "INSERT OR REPLACE INTO field_provenance VALUES ('entity',?,'*',?)", (eid, prov)
            )
        for item in answer.get("aliases", []):
            if (
                not conforms(item, SCHEMA["properties"]["aliases"]["items"])
                or item["entity"] not in refs
            ):
                continue
            eid = refs[item["entity"]]
            text = item["text"].strip()
            if not text:
                continue
            self.conn.execute(
                "INSERT OR IGNORE INTO alias VALUES (?,?,?,?)", (eid, text, text.casefold(), "llm")
            )
            self.conn.execute(
                "INSERT OR IGNORE INTO fts_alias VALUES (?,?,?)", (eid, text, text.casefold())
            )
            self.conn.execute(
                "INSERT OR REPLACE INTO field_provenance VALUES ('alias',?,?,?)", (eid, text, prov)
            )
        edges: list[tuple[str, str, str]] = []
        for item in answer.get("relations", []):
            if conforms(item, SCHEMA["properties"]["relations"]["items"]) and {
                item["src"],
                item["dst"],
            } <= set(refs):
                edges.append((refs[item["src"]], refs[item["dst"]], item["type"]))
        for key in ("tested_by", "installs"):
            for item in answer.get(key, []):
                if not conforms(item, SCHEMA["properties"][key]["items"]):
                    rejected.append((batch.id, f"malformed {key}"))
                    continue
                src = positions.get(item["obligation"])
                if src is None:
                    rejected.append((batch.id, f"{key}: unknown obligation {item['obligation']}"))
                    continue
                regulation = item.get("regulation") or batch.regulation
                target = self._node(regulation, item["target"])
                if target is None:
                    rejected.append((src, f"{key}: unknown target {regulation} {item['target']}"))
                    continue
                if key == "installs":
                    oid = self.conn.execute(
                        "SELECT node_id FROM obligation WHERE id=?", (oid,)
                    ).fetchone()[0]
                edges.append((src, target, key))
        for src, dst, kind in sorted(set(edges)):
            self.conn.execute(
                "INSERT OR REPLACE INTO edge VALUES (?,?,?,?)", (src, dst, kind, prov)
            )
            result.edges += 1
        for target, reason in sorted(set(rejected)):
            self.conn.execute(
                "INSERT OR IGNORE INTO enrich_rejection VALUES (?,?,?)",
                (batch.prompt_hash, target, reason),
            )
        result.rejected.extend(sorted(set(rejected)))
        derived_ids = {
            r[0]
            for r in self.conn.execute(
                "SELECT id FROM obligation WHERE parent_obligation_id IN "
                f"({','.join('?' * len(batch.obligations))})",
                batch.obligations,
            )
        }
        relevant = [
            o
            for o in self.overrides
            if o["target_table"] == "obligation" and o["target_id"] in derived_ids
        ]
        if relevant:
            _apply_overrides(self.conn, relevant)


def connect(db: Path) -> sqlite3.Connection:
    if not db.exists():
        raise SystemExit(f"{db} is missing; run python -m brain.kb.build")
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def all_batches(conn: sqlite3.Connection, regs: Iterable[str]) -> list[Batch]:
    return [b for reg in regs for b in batches(conn, reg)]


def estimate(conn: sqlite3.Connection, regs: list[str]) -> list[tuple[str, int, int, int, int]]:
    """Per regulation: calls, obligations, prompt tokens, generated tokens."""
    schema_chars = len(json.dumps(SCHEMA))
    rows = []
    for reg in regs:
        bs = batches(conn, reg)
        prompt = sum(len(_SYSTEM) + len(b.content) + schema_chars for b in bs) // CHARS_PER_TOKEN
        generated = sum(
            GEN_BATCH_TOKENS
            + sum(len(q) // CHARS_PER_TOKEN + GEN_TAG_TOKENS for q in b.quotes.values())
            for b in bs
        )
        rows.append((reg, len(bs), sum(len(b.obligations) for b in bs), prompt, generated))
    return rows


def run(conn: sqlite3.Connection, regs: list[str], tier: llm.Tier, workers: int = 4) -> Result:
    """Tag every batch of `regs` that has no provenance under its prompt hash yet."""
    writer = Writer(conn, llm.model_for(tier))
    result = Result()
    todo = []
    for b in all_batches(conn, regs):
        if writer.done(b):
            result.skipped += 1
        else:
            todo.append(b)

    def call(b: Batch) -> Any:
        return llm.complete_json(_SYSTEM, b.content, SCHEMA, tier=tier, effort="low")

    with ThreadPoolExecutor(workers) as pool:
        for b, answer in zip(todo, pool.map(call, todo), strict=True):
            writer.apply(b, answer, result)
            conn.commit()
    return result


def export(conn: sqlite3.Connection, regs: list[str], out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    bs = all_batches(conn, regs)
    for b in bs:
        payload = {
            "batch_id": b.id,
            "prompt_hash": b.prompt_hash,
            "regulation": b.regulation,
            "obligations": b.obligations,
            "entities": b.entities,
            "system": _SYSTEM,
            "content": b.content,
            "schema": SCHEMA,
        }
        (out / f"{_slug(b.id)}.json").write_text(
            json.dumps(payload, indent=1, ensure_ascii=False) + "\n"
        )
    return len(bs)


def read_answers(path: Path) -> list[dict[str, Any]]:
    files = sorted(path.glob("*.json*")) if path.is_dir() else [path]
    out: list[dict[str, Any]] = []
    for f in files:
        if f.suffix == ".jsonl":
            out.extend(json.loads(line) for line in f.read_text().splitlines() if line.strip())
        else:
            out.append(json.loads(f.read_text()))
    return out


def import_answers(conn: sqlite3.Connection, path: Path, model: str) -> Result:
    """Validate and write answer files; each names its batch by batch id and prompt hash."""
    answers = read_answers(path)
    known = {row[0] for row in conn.execute("SELECT id FROM regulation")}
    named = {str(a.get("batch_id", "")).rsplit("|", 1)[0] for a in answers}
    by_hash = {b.prompt_hash: b for b in all_batches(conn, sorted(named & known))}
    writer = Writer(conn, model)
    result = Result()
    for a in answers:
        b = by_hash.get(str(a.get("prompt_hash")))
        if b is None:
            result.rejected.append((str(a.get("batch_id", "?")), "no batch with this prompt hash"))
            continue
        if writer.done(b):
            result.skipped += 1
            continue
        writer.apply(b, a.get("answer"), result)
    conn.commit()
    return result


def _report(result: Result) -> None:
    print(
        f"tagged {result.written} obligations, {result.derived} derived, {result.edges} edges, "
        f"{len(result.rejected)} rejected, {result.skipped} batches already done"
    )
    for target, reason in result.rejected[:20]:
        print(f"  rejected {target}: {reason}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--db", type=Path, default=DB)
    parser.add_argument("--regs", nargs="+", help="regulation ids, default all")
    parser.add_argument("--tier", choices=["strong", "bulk"], default="bulk")
    parser.add_argument("--workers", type=int, default=4)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--estimate", action="store_true", help="print the cost, call nothing")
    mode.add_argument("--export-batches", type=Path, metavar="DIR")
    mode.add_argument("--import", dest="import_path", type=Path, metavar="FILE_OR_DIR")
    parser.add_argument("--source-model", help="model name recorded for imported answers")
    args = parser.parse_args(argv)
    if args.import_path and not args.source_model:
        parser.error("--import needs --source-model")
    conn = connect(args.db)
    regs = args.regs or [r[0] for r in conn.execute("SELECT id FROM regulation ORDER BY id")]
    if args.estimate:
        rows = estimate(conn, regs)
        print(f"{'regulation':<14}{'calls':>7}{'obligations':>13}{'prompt tok':>12}{'gen tok':>10}")
        for reg, calls, n, prompt, gen in rows:
            print(f"{reg:<14}{calls:>7}{n:>13}{prompt:>12}{gen:>10}")
        calls = sum(r[1] for r in rows)
        n = sum(r[2] for r in rows)
        prompt = sum(r[3] for r in rows)
        gen = sum(r[4] for r in rows)
        print(f"{'total':<14}{calls:>7}{n:>13}{prompt:>12}{gen:>10}")
        return 0
    if args.export_batches:
        n = export(conn, regs, args.export_batches)
        print(f"wrote {n} batch files to {args.export_batches}")
        return 0
    if args.import_path:
        _report(import_answers(conn, args.import_path, args.source_model))
        return 0
    if not llm.available():
        print(
            "no LLM configured (BRAIN_LLM); use --estimate, --export-batches or --import",
            file=sys.stderr,
        )
        return 1
    _report(run(conn, regs, args.tier, args.workers))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
