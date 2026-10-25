"""Alignment of old and new units: sentences and list items, with the paragraph heading set aside.

Passes: exact (unchanged, renumbered, moved), merged (one unit holds several of the other
version's, as when a parser glues paragraphs together), then similar (amended, split).
"""

from __future__ import annotations

import difflib
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from brain.models import Paragraph

from .text import Op, bare, norm, sentences, substantive, word_ops

Kind = Literal["unchanged", "amended", "new", "deleted"]

MIN_SIMILARITY = 0.5  # a new unit closer than this to an old one is its amended version
SAME_PARAGRAPH = 0.4  # the same, within one paragraph number: a provision rewritten in place
MERGED_COVER = 0.8  # share of a unit's words its pieces must cover to count as merged


@dataclass(frozen=True)
class Span:
    """One unit of a paragraph: a sentence or a list item."""

    label: str
    page: int
    text: str
    index: int = 0  # position among all units of its version
    lead: str = ""  # the paragraph heading, on the paragraph's first unit only


@dataclass(frozen=True)
class Link:
    """An old unit and the new unit it became. `old` is None for a new unit, `new` for a deleted."""

    old: Span | None
    new: Span | None
    ops: tuple[Op, ...] = ()


def body(p: Paragraph) -> tuple[str, str]:
    """(heading, text without it). A heading ending in ":" is a lead-in and stays in the text."""
    text = norm(p.text)
    heading = norm(p.heading or "")
    if heading and not heading.endswith(":") and text.startswith(heading):
        rest = text[len(heading) :].strip()
        # A "heading" that runs into lowercase text is the first line of a sentence.
        if not rest or not rest[0].islower():
            return heading, rest
    return "", text


def units(paragraphs: Sequence[Paragraph]) -> list[Span]:
    out: list[Span] = []
    for p in paragraphs:
        heading, text = body(p)
        for k, s in enumerate(sentences(text)):
            out.append(Span(p.label, p.page, s, len(out), heading if k == 0 else ""))
    return out


def _ops(old: Span, new: Span) -> tuple[Op, ...]:
    return tuple(substantive(word_ops(old.text, new.text), old.text))


def _words(key: Sequence[str]) -> list[str]:
    """Tokens without bare numbers: paragraph labels glued into the text are numbers."""
    return [t for t in key if not t.isdigit()]


def _covering(long: Sequence[str], pieces: dict[int, Sequence[str]]) -> list[int]:
    """The pieces (at least two) found word for word in `long` that together cover 80% of it."""
    text = " " + " ".join(_words(long)) + " "
    size = len(_words(long))
    found = [
        k for k, p in pieces.items() if len(_words(p)) >= 3 and f" {' '.join(_words(p))} " in text
    ]
    covered = sum(len(_words(pieces[k])) for k in found)
    return found if len(found) >= 2 and size >= 6 and covered >= MERGED_COVER * size else []


def align(old: Sequence[Paragraph], new: Sequence[Paragraph]) -> list[Link]:
    """Links of each old unit to its new units (or one link to None if deleted), then one link
    per unclaimed new unit.

    Passes: exact, merged (one unit of a version holds several of the other, as when a parser
    glues paragraphs together), then similar.
    """
    a, b = units(old), units(new)
    ka = [tuple(bare(s.text)) for s in a]
    kb = [tuple(bare(s.text)) for s in b]
    pairs: dict[tuple[int, int], bool] = {}  # (old, new) -> compare wording
    done: set[int] = set()
    claimed: set[int] = set()

    by_key: dict[tuple[str, ...], list[int]] = defaultdict(list)
    for j, key in enumerate(kb):
        by_key[key].append(j)
    for i, key in enumerate(ka):
        free = [j for j in by_key.get(key, []) if j not in claimed]
        if key and free:
            j = next((j for j in free if b[j].label == a[i].label), free[0])
            pairs[i, j] = False
            done.add(i)
            claimed.add(j)

    for i in [i for i in range(len(a)) if i not in done and ka[i]]:
        for j in _covering(ka[i], {j: kb[j] for j in range(len(b)) if j not in claimed}):
            pairs[i, j] = False
            done.add(i)
            claimed.add(j)
    for j in [j for j in range(len(b)) if j not in claimed and kb[j]]:
        for i in _covering(kb[j], {i: ka[i] for i in range(len(a)) if i not in done}):
            pairs[i, j] = False
            done.add(i)
            claimed.add(j)

    rest_a = [i for i in range(len(a)) if i not in done and ka[i]]
    rest_b = [j for j in range(len(b)) if j not in claimed and kb[j]]
    scored: list[tuple[float, bool, int, int]] = []
    matcher: difflib.SequenceMatcher[str] = difflib.SequenceMatcher(autojunk=False)
    for j in rest_b:
        matcher.set_seq2(kb[j])  # type: ignore[arg-type]
        for i in rest_a:
            matcher.set_seq1(ka[i])  # type: ignore[arg-type]
            same = a[i].label == b[j].label
            floor = SAME_PARAGRAPH if same else MIN_SIMILARITY
            if matcher.real_quick_ratio() < floor or matcher.quick_ratio() < floor:
                continue
            ratio = matcher.ratio()
            if ratio >= floor:
                scored.append((ratio, same, i, j))

    # Within the same paragraph first, then across paragraphs, best score first in each.
    strong = [t for t in scored if t[0] >= MIN_SIMILARITY]
    for _, _, i, j in sorted(strong, key=lambda t: (not t[1], -t[0], t[2], t[3])):
        if i not in done and j not in claimed:
            pairs[i, j] = True
            done.add(i)
            claimed.add(j)
    # A provision rewritten in place: the one old unit left in a paragraph and the one new unit
    # left under the same label, if they are at least SAME_PARAGRAPH alike.
    left_a = Counter(a[i].label for i in range(len(a)) if i not in done and ka[i])
    left_b = Counter(b[j].label for j in range(len(b)) if j not in claimed and kb[j])
    for ratio, same, i, j in scored:
        label = a[i].label
        if same and ratio < MIN_SIMILARITY and left_a[label] == 1 and left_b[label] == 1:
            if i not in done and j not in claimed:
                pairs[i, j] = True
                done.add(i)
                claimed.add(j)

    by_old: dict[int, list[int]] = defaultdict(list)
    for i, j in sorted(pairs):
        by_old[i].append(j)
    links: list[Link] = []
    for i, s in enumerate(a):
        if i not in by_old:
            links.append(Link(s, None))
        for j in by_old.get(i, []):
            links.append(Link(s, b[j], _ops(s, b[j]) if pairs[i, j] else ()))
    return links + [Link(None, s) for j, s in enumerate(b) if j not in claimed]


def kind(link: Link) -> Kind:
    if link.old is None:
        return "new"
    if link.new is None:
        return "deleted"
    return "amended" if link.ops else "unchanged"
