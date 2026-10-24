"""Deterministic, source-preserving obligation span extraction."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..models import Paragraph
from ..obligations import CONDITIONS, modality

_BOUNDARY = re.compile(r"(?<=[.;:])\s+(?=[A-Z\"“(])")
_LIST = re.compile(r"^\s*(?:\([a-z]|\([ivx]{1,4}|\(\d{1,2})\)\s+", re.I)
_ITEM = re.compile(r"(?<!\w)(\([a-z]\)|\([ivx]{1,4}\)|\(\d{1,2}\))\s+", re.I)
_TELEGRAPHIC = re.compile(r"^(?:In\s+)?[A-Z][\w\s/,()\-]{1,60}:\s+.+$", re.S)
_NUMBER = re.compile(
    r"(?P<a>[+-]?\d+(?:[.,]\d+)?)(?:\s*(?:to|[-–])\s*(?P<b>[+-]?\d+(?:[.,]\d+)?))?\s*(?P<unit>%|mm|cm|m|km|cd|Hz|kHz|MHz|V|A|W|N|kg|s|min|h|°|degrees?|[µμ]s|dB(?:\s+microvolts?/m)?)(?=\s|[,.;)]|$)",
    re.I,
)


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    raw: str
    source_kind: str


def _sentences(text: str) -> list[tuple[int, int]]:
    starts = [0]
    for m in _BOUNDARY.finditer(text):
        starts.append(m.end())
    return [(s, starts[i + 1] if i + 1 < len(starts) else len(text)) for i, s in enumerate(starts)]


def _kind(raw: str) -> str:
    if re.search(r"\btable\b", raw, re.I) and _NUMBER.search(raw):
        return "table_row"
    if _ITEM.match(raw):
        return "enumeration_item"
    if _TELEGRAPHIC.match(raw.strip()) and not re.search(r"\b(?:shall|must|may)\b", raw, re.I):
        return "telegraphic"
    return "sentence"


def extract(paragraph: Paragraph) -> list[Span]:
    """Return modal sentences and constrained telegraphic/table text as exact spans."""
    text = paragraph.text
    out: list[Span] = []
    for start, end in _sentences(text):
        raw = text[start:end].strip()
        left = start + len(text[start:end]) - len(text[start:end].lstrip())
        if not raw:
            continue
        if modality(raw) in {"shall", "shall not", "must", "must not", "may"} or re.search(
            r"\b(?:not permitted|prohibited|not permissible)\b", raw, re.I
        ):
            for item in _split_items(raw, left):
                out.append(item)
        elif _TELEGRAPHIC.match(raw) and _NUMBER.search(raw):
            out.append(Span(left, left + len(raw), raw, "telegraphic"))
    return sorted(out, key=lambda s: (s.start, s.end))


def _split_items(raw: str, offset: int) -> list[Span]:
    markers = list(_ITEM.finditer(raw))
    if not markers:
        return [Span(offset, offset + len(raw), raw, _kind(raw))]
    lead = raw[: markers[0].start()].strip()
    result: list[Span] = []
    if lead and re.search(r"\b(?:shall|must)\b", lead, re.I):
        lead_start = (
            offset + len(raw[: markers[0].start()]) - len(raw[: markers[0].start()].lstrip())
        )
        result.append(Span(lead_start, lead_start + len(lead), lead, "sentence"))
    for i, marker in enumerate(markers):
        end = markers[i + 1].start() if i + 1 < len(markers) else len(raw)
        item = raw[marker.start() : end].strip()
        item_offset = (
            offset
            + marker.start()
            + len(raw[marker.start() : end])
            - len(raw[marker.start() : end].lstrip())
        )
        if item and (re.search(r"\b(?:shall|must)\b", item, re.I) or _NUMBER.search(item)):
            result.append(Span(item_offset, item_offset + len(item), item, "enumeration_item"))
    return result or [Span(offset, offset + len(raw), raw, _kind(raw))]


def normalized(raw: str, heading: str | None = None) -> str:
    text = raw.strip()
    if heading and text.startswith(heading):
        text = text[len(heading) :].strip()
    return _LIST.sub("", text).strip()


def condition(raw: str) -> tuple[str, str | None]:
    for pattern, kind in CONDITIONS:
        if pattern.search(raw):
            comma = raw.find(",")
            return kind, raw[:comma].strip() if 0 < comma < 300 else None
    return "none", None


def values(
    raw: str,
) -> list[tuple[float | None, float | None, float | None, str, float | None, str]]:
    result: list[tuple[float | None, float | None, float | None, str, float | None, str]] = []
    for match in _NUMBER.finditer(raw):
        a = float(match["a"].replace(",", "."))
        b = float(match["b"].replace(",", ".")) if match["b"] else None
        result.append(
            (
                a if b is None else None,
                a if b is not None else None,
                b,
                match["unit"],
                None,
                match.group(0),
            )
        )
    return result
