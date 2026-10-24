"""Requirement text as the regulation's own sentence: each requirement whose quote belongs to it
alone takes that quote as its text. The expert list keeps the source wording, and on dev the
platform matched 156 rows written this way against 149 for the same rows rewritten. Requirements
that share a quote (list items, table rows split from one sentence) keep the rewrite, since the
quote alone would repeat the whole sentence for each of them."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import replace

from .rewrite import Draft

MIN_CHARS = 20


def apply(drafts: Sequence[Draft]) -> list[Draft]:
    shared = Counter((d.paragraph.id, d.quote.strip()) for d in drafts)
    return [
        replace(d, text=d.quote.strip())
        if shared[(d.paragraph.id, d.quote.strip())] == 1 and len(d.quote.strip()) >= MIN_CHARS
        else d
        for d in drafts
    ]
