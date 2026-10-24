"""Paragraph text -> candidate obligations, one per sentence that carries a modal verb.

The expected requirements are the regulation's own "shall" sentences, lightly rewritten into
standalone obligations (EARS style: "The stop lamp shall emit red light."; "When ..., the ...
shall ..."). This module does the deterministic part: sentence splitting, modality, EARS
condition detection and the subject from the heading path. An LLM rewrite can refine the text
later (brain.rewrite), but the verbatim sentence always stays as the quote.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from .models import ConditionType, Modality, Obligation, Paragraph

# A sentence ends at . ; or : followed by a capital, an opening bracket or a quote, unless the dot
# closes a number ("paragraph 3.3.4.2. or"), an abbreviation ("No. 48", "e.g. the") or a label.
_BOUNDARY = re.compile(r"(?<=[.;:])\s+(?=[A-Z\"“(])")
_ABBREV = re.compile(
    r"(?:\b(?:No|Nos|Par|para|e\.g|i\.e|etc|approx|Fig|min|max|cf|vs|Annex)\.)$", re.IGNORECASE
)
MODALS: list[tuple[re.Pattern[str], Modality]] = [
    (re.compile(r"\bshall\s+not\b|\bshall\s+(?:\w+\s+)?not\b", re.I), "shall not"),
    (re.compile(r"\bshall\b", re.I), "shall"),
    (re.compile(r"\bmust\s+not\b", re.I), "must not"),
    (re.compile(r"\bmust\b", re.I), "must"),
    (re.compile(r"\bmay\b", re.I), "may"),
]
CONDITIONS: list[tuple[re.Pattern[str], ConditionType]] = [
    (re.compile(r"^(?:If|In the event)\b", re.I), "if"),
    (re.compile(r"^(?:When|Whenever|After|Before|Upon|On completion|During)\b", re.I), "when"),
    (re.compile(r"^(?:While|As long as)\b", re.I), "while"),
    (re.compile(r"^(?:Where|In the case|In case|For)\b", re.I), "where"),
]
_LIST_ITEM = re.compile(r"^\(?([a-z]|[ivx]{1,4}|\d{1,2})\)\s+")
_TRAILING_HEADING = re.compile(r"^[A-Z][^.:]{0,80}:\s+")


def sentences(text: str) -> list[tuple[int, str]]:
    """(offset, sentence) pairs. A boundary after an abbreviation ("No. 48") is not one."""
    pieces: list[tuple[int, str]] = []
    start = 0
    for m in _BOUNDARY.finditer(text):
        chunk = text[start : m.start()]
        if _ABBREV.search(chunk):
            continue
        pieces.append((start, chunk.strip()))
        start = m.end()
    pieces.append((start, text[start:].strip()))
    return [(o, s) for o, s in pieces if s]


def modality(sentence: str) -> Modality:
    for pattern, kind in MODALS:
        if pattern.search(sentence):
            return kind
    return "other"


def condition(sentence: str) -> tuple[ConditionType, str | None]:
    for pattern, kind in CONDITIONS:
        if pattern.search(sentence):
            comma = sentence.find(",")
            return kind, sentence[:comma].strip() if 0 < comma < 300 else None
    return "none", None


def subject(paragraph: Paragraph, by_id: dict[str, Paragraph]) -> str | None:
    """The nearest heading in the paragraph's path that names a thing, e.g. "Stop lamps"."""
    for pid in [paragraph.id, *reversed(paragraph.path)]:
        p = by_id.get(pid)
        title = p.heading if p else None
        if p and not title and p.text and len(p.text) < 90 and not modality(p.text) == "shall":
            title = p.text
        if title:
            title = re.sub(r"\s*\([^)]*\)\s*$", "", title).rstrip(":. ").strip()
            if title and not re.match(
                r"^(General|Definitions?|Specifications?|Requirements?|"
                r"Measurement|Colour|Failure provisions|Additional)",
                title,
            ):
                return title
    return None


def clean(sentence: str, paragraph: Paragraph) -> str:
    """Drop a leading heading ("Colour: The colour ...") and a list marker."""
    s = sentence
    if paragraph.heading and s.startswith(paragraph.heading):
        s = s[len(paragraph.heading) :].strip()
    s = _LIST_ITEM.sub("", s)
    return s.strip()


def extract(
    paragraph: Paragraph,
    by_id: dict[str, Paragraph],
    keep: Iterable[Modality] = ("shall", "shall not", "must", "must not"),
) -> list[Obligation]:
    keep = set(keep)
    out: list[Obligation] = []
    subj = subject(paragraph, by_id)
    for n, (_, raw) in enumerate(sentences(paragraph.text)):
        sentence = clean(raw, paragraph)
        mod = modality(sentence)
        if mod not in keep or len(sentence) < 15:
            continue
        ctype, cond = condition(sentence)
        out.append(
            Obligation(
                id=f"{paragraph.id}#{n}",
                paragraph_id=paragraph.id,
                regulation=paragraph.regulation,
                version=paragraph.version,
                label=paragraph.label,
                page=paragraph.page,
                sentence=sentence,
                modality=mod,
                subject=subj,
                condition_type=ctype,
                condition=cond,
                text=sentence[:2000],
            )
        )
    return out


def extract_all(paragraphs: list[Paragraph], **kwargs: object) -> list[Obligation]:
    by_id = {p.id: p for p in paragraphs}
    return [o for p in paragraphs for o in extract(p, by_id, **kwargs)]  # type: ignore[arg-type]
