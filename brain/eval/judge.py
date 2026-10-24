"""Requirement-level matching: each submitted requirement is matched one-to-one with an expected
one that states the same obligation (same scope, condition and constraint).

The platform uses a language model for this. Offline we use a lexical proxy (token overlap of the
texts, restricted to the same regulation), solved as an assignment problem; `llm_verdicts` can
replace the similarity matrix with model verdicts when an API key is configured.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

_TOKEN = re.compile(r"[a-z0-9]+(?:[.,]\d+)*")
_STOP = frozenset(
    "the a an of to and or in on at by for be is are shall with as that this which "
    "it its from than any all each".split()
)


def tokens(text: str) -> set[str]:
    return {t for t in _TOKEN.findall(text.lower()) if t not in _STOP}


_NEGATION = re.compile(r"\b(?:not|no|never|neither|nor|without)\b", re.I)
_NUMBER = re.compile(r"\d+(?:[.,]\d+)*")


def similarity(a: str, b: str) -> float:
    """Token Jaccard, zeroed when one text negates and the other does not, halved when both cite
    numbers but share none ("7.5 kN" vs "75 kN")."""
    ta, tb = tokens(a), tokens(b)
    sim = len(ta & tb) / max(1, len(ta | tb))
    if bool(_NEGATION.search(a)) != bool(_NEGATION.search(b)):
        return 0.0
    na, nb = set(_NUMBER.findall(a)), set(_NUMBER.findall(b))
    if na and nb and not na & nb:
        sim *= 0.5
    return sim


Pair = tuple[dict[str, Any], dict[str, Any]]


def match(
    submitted: list[dict[str, Any]],
    expected: list[dict[str, Any]],
    threshold: float = 0.45,
    sim: Callable[[str, str], float] = similarity,
) -> list[tuple[int, int, float]]:
    """One-to-one matches (submitted index, expected index, similarity) above `threshold`."""
    out: list[tuple[int, int, float]] = []
    regs = {r["source"]["regulation"] for r in expected}
    for reg in regs:
        si = [i for i, r in enumerate(submitted) if r["source"]["regulation"] == reg]
        ei = [j for j, r in enumerate(expected) if r["source"]["regulation"] == reg]
        if not si or not ei:
            continue
        m = np.zeros((len(si), len(ei)))
        for a, i in enumerate(si):
            for b, j in enumerate(ei):
                m[a, b] = sim(submitted[i]["text"], expected[j]["text"])
        # Maximise the number of acceptable matches first, similarity second.
        ok = m >= threshold
        rows, cols = linear_sum_assignment(-np.where(ok, 1.0 + m, 0.0))
        out.extend(
            (si[r], ei[c], float(m[r, c]))
            for r, c in zip(rows, cols, strict=True)
            if m[r, c] >= threshold
        )
    return out
