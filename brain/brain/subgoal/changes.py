"""Change records: modified and removed rows for old requirements, added rows for new paragraphs."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Sequence
from typing import Any

from brain.features import UNITS
from brain.models import Paragraph

from .align import Link, Span, units
from .text import (
    ITEM,
    MAX_TEXT,
    Op,
    describe,
    fit,
    norm,
    overlap,
    quote,
    shorten,
    substantive,
    word_ops,
)

ADDED_QUOTE = 100  # characters of a new provision quoted in an added reason
REMOVED_QUOTE = 90  # characters of an old provision quoted in a removed reason
MODAL = re.compile(r"\b(?:shall|must|may)\b")
SECOND_MODAL = re.compile(r",\s+and\s+(?=(?:shall|must|may)\b)")
FOR_SUBJECT = re.compile(r"^For\s+(.+?),?\s+the\s", re.I)  # "For tests without a target the ACPE …"
PROCEDURE = re.compile(r"\b(?:procedure|test|measurement|check|inspection)", re.I)
TAIL = re.compile(r",\s+(?=[A-Z][a-z])")  # "(b) 4 km/h rearward, As reasonably practical …"


def _within(label: str, cited: str) -> bool:
    return label == cited or label.startswith(cited + ".") or label.startswith(cited + " ")


def best_run(target: str, spans: Sequence[Span]) -> list[Span]:
    """The run of consecutive units that best matches `target`; earlier runs win near-ties.

    A run of a lead-in ("… as follows:") and one item is cut to the item, so a change to the
    lead-in alone does not flag the requirements derived from its items.
    """
    size = len(target.split())
    best: tuple[float, list[Span]] = (0.0, [])
    for i in range(len(spans)):
        run: list[Span] = []
        for s in spans[i:]:
            if run and s.index != run[-1].index + 1:
                break
            run.append(s)
            score = overlap(target, " ".join(u.text for u in run))
            if score > best[0] + 0.05:
                best = (score, list(run))
            if sum(len(u.text.split()) for u in run) > 2 * size + 10:
                break
    run = best[1]
    return run[1:] if len(run) == 2 and run[0].text.endswith(":") else run


def apply_ops(req_text: str, old_text: str, ops: Sequence[Op]) -> tuple[str, int]:
    """The requirement with the wording changes applied where the changed phrase occurs in it."""
    words = old_text.split()
    text = req_text
    applied = 0
    for tag, old, new, i in ops:
        if tag in ("replace", "delete") and old in text:
            text = text.replace(old, new, 1)
            applied += 1
        elif tag == "insert":
            for k in (4, 3, 2):
                anchor = " ".join(words[max(0, i - k) : i])
                if i >= k and anchor in text:
                    text = text.replace(anchor, anchor + " " + new, 1)
                    applied += 1
                    break
    return norm(text), applied


def _region(
    run: Sequence[Span], by_old: dict[int, list[Link]], new_units: Sequence[Span]
) -> list[Span]:
    """The new units the run became, with unclaimed new units between them in the same paragraphs.

    When the run starts or ends with deleted units, unclaimed new units next to it in the same new
    paragraph count as their replacement.
    """
    claimed = {link.new.index for links in by_old.values() for link in links if link.new}
    mine = {link.new.index for s in run for link in by_old[s.index] if link.new}
    if not mine:
        return []
    lo, hi = min(mine), max(mine)
    if not any(link.new for link in by_old[run[0].index]):
        while lo > 0 and lo - 1 not in claimed and new_units[lo - 1].label == new_units[lo].label:
            lo -= 1
    if not any(link.new for link in by_old[run[-1].index]):
        last = len(new_units) - 1
        while (
            hi < last and hi + 1 not in claimed and new_units[hi + 1].label == new_units[hi].label
        ):
            hi += 1
    labels = {new_units[j].label for j in mine}
    return [
        u
        for u in new_units[lo : hi + 1]
        if u.index in mine or (u.index not in claimed and u.label in labels)
    ]


def map_requirements(
    requirements: Sequence[dict[str, Any]],
    old: Sequence[Paragraph],
    links: Sequence[Link],
    regulation: str,
    to_version: str,
) -> list[dict[str, Any]]:
    """Modified and removed changes, in requirement order. Unchanged requirements are left out."""
    old_units = units(old)
    by_old: dict[int, list[Link]] = defaultdict(list)
    for link in links:
        if link.old:
            by_old[link.old.index].append(link)
    new_units = sorted((link.new for link in links if link.new), key=lambda s: s.index)
    changes: list[dict[str, Any]] = []
    for req in requirements:
        cited = req["source"]["paragraph"]
        candidates = [s for s in old_units if _within(s.label, cited)] or old_units
        run = best_run(req["text"], candidates)
        if not run:
            continue
        old_label = run[0].label
        old_text = " ".join(s.text for s in run)
        region = _region(run, by_old, new_units)
        if not region:
            changes.append(
                {
                    "requirement_id": req["id"],
                    "change": "removed",
                    "reason": f"Paragraph {old_label} of {regulation} was amended in version "
                    f"{to_version}; the provision '{quote(old_text, REMOVED_QUOTE)}' no longer "
                    "appears.",
                }
            )
            continue
        mine = {link.new.index for u in run for link in by_old[u.index] if link.new}
        unchanged = all(link.new and not link.ops for u in run for link in by_old[u.index])
        if unchanged and all(u.index in mine for u in region):
            continue  # moved, merged or split without a change of wording
        new_text = " ".join(s.text for s in region)
        ops = substantive(word_ops(old_text, new_text), old_text)
        if not ops:
            continue
        label = region[0].label
        formerly = f" (formerly {old_label})" if label != old_label else ""
        patched, applied = apply_ops(req["text"], old_text, ops)
        # The old requirement with the edits applied keeps its explicit subject ("The accelerator
        # control misapplication test procedures …"); the new sentence alone may not ("The test
        # procedures …"). The new wording is used only when an edit finds no place in it.
        text = patched if applied == len(ops) else new_text
        if len(text) > MAX_TEXT or len(req["text"]) >= MAX_TEXT:
            text = shorten(text, [op[2] for op in ops if op[2]])
        changes.append(
            {
                "requirement_id": req["id"],
                "change": "modified",
                "new_text": text,
                "reason": f"Paragraph {label}{formerly} of {regulation} was amended in version "
                f"{to_version}: {describe(ops)}.",
                "source": {"page": region[0].page, "paragraph": label},
                "old_span": old_text,
                "new_span": new_text,
            }
        )
    return changes


def top(label: str) -> str:
    """The top-level section of a label: "5" for "5.1.4", "Annex 3" for "Annex 3 2.1"."""
    words = label.split()
    return " ".join(words[:2]) if words[0] == "Annex" else label.split(".")[0]


def _quoted(unit: Span) -> str:
    return f"{unit.lead} {unit.text}" if unit.lead else unit.text


def _lower(text: str) -> str:
    return text[0].lower() + text[1:] if text[:2] != text[:2].upper() else text


def _with_lead(unit: Span, text: str) -> str:
    """A run-in heading ("Acceleration while creeping,") is a condition: "For acceleration while
    creeping, …"."""
    if not unit.lead.endswith(","):
        return text
    return f"For {_lower(unit.lead.rstrip(', '))}, {_lower(text)}"


def fuse(lead_in: str, item: str, tail: str = "") -> str:
    """One requirement from a lead-in and a list item: "X shall be as follows:" + "(a) Hold …"
    gives "X shall be to hold …". An item with its own modal verb stands alone. `tail` is a
    clause after the last item that applies to every item."""
    body = re.sub(rf"^{ITEM}", "", item).strip()
    if MODAL.search(body):
        # The item states its own obligation; a procedure lead-in still sets when it applies.
        subject = lead_in[: m.start()].strip() if (m := MODAL.search(lead_in)) else ""
        if PROCEDURE.search(subject):
            body = f"During {_lower(subject)}, {_lower(body)}"
        return body.rstrip(".") + "."
    head = re.sub(r"\s+as follows$", " to", lead_in.rstrip(":").strip())
    body = re.sub(r"[;,]?\s+(?:or|and)$", "", body).rstrip(" ,;")
    text = f"{head} {_lower(body)}" + (f" {_lower(tail)}" if tail else "")
    return text.rstrip(".") + "."


def _sentence_rows(unit: Span) -> list[tuple[str, str]]:
    text = unit.text
    if not MODAL.search(text):
        return [(_quoted(unit), _with_lead(unit, text))] if UNITS.search(text) else []
    second = SECOND_MODAL.search(text)
    if not second:
        return [(_quoted(unit), _with_lead(unit, text))]
    first = text[: second.start()].rstrip(" ,") + "."
    if m := FOR_SUBJECT.match(text):
        subject = m[1][0].upper() + m[1][1:]
    else:
        subject = text[: MODAL.search(text).start()].strip()  # type: ignore[union-attr]
    return [
        (_quoted(unit), _with_lead(unit, first)),
        (_quoted(unit), _with_lead(unit, f"{subject} {text[second.end() :]}")),
    ]


def obligations(spans: Sequence[Span]) -> list[tuple[str, str]]:
    """(quote, requirement text) for each obligation in a new paragraph's units.

    Items under a lead-in with a modal verb ("… shall be as follows:") are one row each. A lead-in
    without one ("… is not required when:") stays one row with its items. Other sentences count
    when they have a modal verb or a number with a unit; "X shall A, and may B" gives two rows.
    """
    rows: list[tuple[str, str]] = []
    k = 0
    while k < len(spans):
        unit = spans[k]
        items: list[Span] = []
        if unit.text.endswith(":"):
            while k + 1 + len(items) < len(spans) and re.match(
                ITEM, spans[k + 1 + len(items)].text
            ):
                items.append(spans[k + 1 + len(items)])
        if items and MODAL.search(unit.text):
            texts = [i.text for i in items]
            parts = TAIL.split(texts[-1], maxsplit=1) if len(items) > 1 else [texts[-1]]
            tail = parts[1] if len(parts) == 2 else ""
            texts[-1] = parts[0]
            rows += [
                (_quoted(i), fuse(unit.text, t, tail)) for i, t in zip(items, texts, strict=True)
            ]
        elif items:
            joined = " ".join([unit.text] + [i.text for i in items])
            if MODAL.search(joined) or UNITS.search(joined):
                rows.append((f"{unit.lead} {joined}" if unit.lead else joined, joined))
        else:
            rows += _sentence_rows(unit)
        k += 1 + len(items)
    return rows


def added_changes(
    links: Sequence[Link], sections: set[str], regulation: str, to_version: str
) -> list[dict[str, Any]]:
    """One added change per obligation of each new paragraph in the given top-level sections.

    A paragraph is new when some of its units are new and none, lead-ins aside, came from the old
    version. A new
    sentence inside an old paragraph is part of that paragraph's amendment, not an added row.
    """
    claimed = {link.new.index for link in links if link.old and link.new}
    by_label: dict[str, list[Span]] = defaultdict(list)
    for unit in sorted((link.new for link in links if link.new), key=lambda s: s.index):
        by_label[unit.label].append(unit)
    changes: list[dict[str, Any]] = []
    for label, spans in by_label.items():
        if top(label) not in sections:
            continue
        if all(s.index in claimed for s in spans) or any(
            s.index in claimed and not s.text.endswith(":") for s in spans
        ):
            continue
        for quoted, text in obligations(spans):
            changes.append(
                {
                    "requirement_id": None,
                    "change": "added",
                    "new_text": fit(text),
                    "reason": f"Paragraph {label} of {regulation} is new in version {to_version}: "
                    f"'{quote(quoted, ADDED_QUOTE)}'.",
                    "source": {"page": spans[0].page, "paragraph": label},
                }
            )
    return changes
