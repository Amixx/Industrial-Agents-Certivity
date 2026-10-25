"""Post-process rewritten requirements into the expert's paragraph-level granularity."""

from __future__ import annotations

import json
import os
import re
from collections import OrderedDict
from collections.abc import Sequence
from dataclasses import replace

from . import llm
from .graph import Graph
from .rewrite import Draft

# ruff: noqa: E501

ENABLED = os.environ.get("BRAIN_CONSOLIDATE") == "1"
BATCH = 30
# The submission platform rejects requirement text over 2,000 characters.
MAX_TEXT = 2000

ITEM = re.compile(r"^\s*\(?([a-z]|[ivx]{1,4}|\d{1,2})\)\s")
MODAL = re.compile(r"\b(shall|must|may|is required|are required)\b", re.I)

_SYSTEM = """You decide how a regulatory expert turns a paragraph containing a list into requirements.
- MERGE: the list items are cases, conditions, alternatives or circumstances under which ONE obligation or permission applies (e.g. "lamps with: (a) X; (b) Y shall bear ...", "the intensity may vary: (a) when ...; (b) when ..."). The expert writes one requirement for the whole paragraph.
- SPLIT: each list item is a separate thing that must be done, borne, met or provided, with its own content or value (e.g. "shall bear: (i) the trade name; (ii) the code; (iii) the voltage", or items each with its own limit). The expert writes one requirement per item.
Answer for every paragraph."""

_SCHEMA = {
    "type": "object",
    "required": ["paragraphs"],
    "properties": {
        "paragraphs": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["key", "decision"],
                "properties": {
                    "key": {"type": "string"},
                    "decision": {"type": "string", "enum": ["MERGE", "SPLIT"]},
                },
            },
        }
    },
}


def _key(regulation: str, label: str) -> tuple[str, str]:
    return regulation, label.strip().rstrip(".").lower()


def _candidate_groups(
    drafts: Sequence[Draft], graph: Graph
) -> OrderedDict[tuple[str, str], list[Draft]]:
    grouped: OrderedDict[tuple[str, str], list[Draft]] = OrderedDict()
    for draft in drafts:
        grouped.setdefault(_key(draft.paragraph.regulation, draft.paragraph.label), []).append(
            draft
        )
    return OrderedDict(
        (key, rows)
        for key, rows in grouped.items()
        if len(rows) >= 2
        and graph.paragraphs.get(rows[0].paragraph.id) is not None
        and any(ITEM.match(row.text) and not MODAL.search(row.text) for row in rows)
    )


def _ask(chunk: list[tuple[tuple[str, str], str]]) -> dict[str, str]:
    items = [{"key": f"{regulation}|{label}", "text": text} for (regulation, label), text in chunk]
    data = llm.complete_json(
        _SYSTEM,
        "Paragraphs (JSON):\n" + json.dumps(items, ensure_ascii=False, indent=1),
        _SCHEMA,
        tier="strong",
    )
    return {item["key"]: item["decision"] for item in data["paragraphs"]}


def _merge(drafts: Sequence[Draft], graph: Graph) -> list[Draft]:
    if not llm.available():
        return list(drafts)
    candidates = _candidate_groups(drafts, graph)
    if not candidates:
        return list(drafts)
    requests = [
        (key, graph.paragraphs[rows[0].paragraph.id].text)
        for key, rows in candidates.items()
        if len(re.sub(r"\s+", " ", graph.paragraphs[rows[0].paragraph.id].text).strip()) <= MAX_TEXT
    ]
    decisions: dict[str, str] = {}
    for start in range(0, len(requests), BATCH):
        decisions.update(_ask(requests[start : start + BATCH]))
    out: list[Draft] = []
    merged: set[tuple[str, str]] = set()
    for draft in drafts:
        key = _key(draft.paragraph.regulation, draft.paragraph.label)
        decision = decisions.get(f"{key[0]}|{key[1]}")
        if decision == "MERGE":
            if key in merged:
                continue
            text = re.sub(r"\s+", " ", graph.paragraphs[draft.paragraph.id].text).strip()
            out.append(replace(draft, text=text, quote=text))
            merged.add(key)
        else:
            out.append(draft)
    return out


def _collapse_shared_quotes(drafts: Sequence[Draft]) -> list[Draft]:
    counts: dict[tuple[str, str], int] = {}
    for draft in drafts:
        key = (draft.paragraph.id, draft.quote.strip())
        counts[key] = counts.get(key, 0) + 1
    out: list[Draft] = []
    collapsed: set[tuple[str, str]] = set()
    for draft in drafts:
        key = (draft.paragraph.id, draft.quote.strip())
        if counts[key] > 1:
            if key in collapsed:
                continue
            out.append(replace(draft, text=key[1]))
            collapsed.add(key)
        else:
            out.append(draft)
    return out


def _drop_exact_duplicates(drafts: Sequence[Draft]) -> list[Draft]:
    seen: set[str] = set()
    out: list[Draft] = []
    for draft in drafts:
        if draft.text in seen:
            continue
        seen.add(draft.text)
        out.append(draft)
    return out


def apply(drafts: Sequence[Draft], graph: Graph) -> list[Draft]:
    """Merge list cases, collapse shared quotes, then drop repeated requirement text."""
    merged = _merge(drafts, graph)
    return _drop_exact_duplicates(_collapse_shared_quotes(merged))
