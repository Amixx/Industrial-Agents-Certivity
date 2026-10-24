"""Text rules of the sub-goal diff: normalised words, the word diff, quotes and length limits."""

from __future__ import annotations

import difflib
import re
from collections import Counter
from collections.abc import Sequence
from typing import Literal

Op = tuple[Literal["replace", "insert", "delete"], str, str, int]

MAX_TEXT = 2000  # schemas/submission_subgoal.schema.json: new_text maxLength
ITEM = r"\((?:[a-z]|[ivx]{1,4})\)\s"  # "(a) ", "(iv) "
# A unit ends after . ; : (not after a paragraph number such as "5.1.5."), after a comma before an
# item marker, or anywhere before an item marker that starts a capitalised item.
UNIT_END = re.compile(rf"(?<=[.;:])(?<!\d\.)\s+(?=[A-Z(])|(?<=,)\s+(?={ITEM})|\s+(?={ITEM}[A-Z])")
# A footnote marker glued to a word: "vehicle6", "6This" (not "M1" or "N2G").
FOOTNOTE = re.compile(r"(?<=[a-z]{3})\d{1,2}\b|\b\d{1,2}(?=[A-Z][a-z])")


def norm(text: str) -> str:
    return " ".join(text.split())


def bare(text: str) -> list[str]:
    """Lower-case words without punctuation, with "70%" and "6 seconds" spelled one way."""
    text = text.replace("%", " per cent ").replace("µ", "μ")
    text = re.sub(r"(\d)\s*(?:seconds?|sec)\b", r"\1 s", text)
    return re.sub(r"[^\w]+", " ", text).lower().split()


def sentences(text: str) -> list[str]:
    return [s for s in UNIT_END.split(norm(text)) if s]


def word_ops(old: str, new: str) -> list[Op]:
    """Word-level differences as (tag, old phrase, new phrase, old word index)."""
    a, b = old.split(), new.split()
    ops: list[Op] = []
    matcher = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "equal":
            ops.append((tag, " ".join(a[i1:i2]), " ".join(b[j1:j2]), i1))  # type: ignore[arg-type]
    return ops


def substantive(ops: Sequence[Op], old: str = "") -> list[Op]:
    """The operations that change words, not only punctuation or spelling variants.

    The word before each operation in `old` is context, so "6 seconds" against "6 s" is a variant.
    A renumbered footnote marker ("6This" against "1 This") is a variant too.
    """
    words = old.split()
    out = []
    for op in ops:
        before = words[op[3] - 1] if 0 < op[3] <= len(words) else ""
        if bare(f"{before} {op[1]}") == bare(f"{before} {op[2]}"):
            continue
        if (FOOTNOTE.search(op[1]) or FOOTNOTE.search(op[2])) and unmarked(op[1]) == unmarked(
            op[2]
        ):
            continue
        out.append(op)
    return out


def unmarked(text: str) -> list[str]:
    """Words without footnote markers, glued ("6This") or loose ("1 This")."""
    return [t for t in bare(FOOTNOTE.sub("", text)) if not (t.isdigit() and len(t) <= 2)]


def describe(ops: Sequence[Op]) -> str:
    parts = []
    for tag, old, new, _ in ops:
        if tag == "replace":
            parts.append(f"'{old}' became '{new}'")
        elif tag == "insert":
            parts.append(f"'{new}' was added")
        else:
            parts.append(f"'{old}' was removed")
    return "; ".join(parts)


def quote(text: str, limit: int) -> str:
    """The text, cut to `limit` characters with "…" when longer, as the gold reasons quote."""
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


ROMAN_ITEM = re.compile(r"^\([ivx]{1,4}\)\s")
TERMINAL = re.compile(r"[.;:)\"”']$")


def shorten(text: str, keep: Sequence[str], limit: int = MAX_TEXT) -> str:
    """The text within `limit` characters, losing as little of what changed as possible.

    An unfinished last unit (the old requirement was cut at the schema's limit) goes first. Then
    whole sub-lists ("…, i.e.: (i) …; (ii) …") that hold none of the `keep` phrases go, largest
    first, and their lead-in ends with ";". Only then is the end cut.
    """
    parts = sentences(text)
    if len(parts) > 1 and not TERMINAL.search(parts[-1]):
        parts = parts[:-1]
    # Phrases of one or two words ("In", "the") would mark every unit as changed.
    kept = [f" {' '.join(bare(k))} " for k in keep if len(bare(k)) >= 3 or re.search(r"\d", k)]

    def changed(unit: str) -> bool:
        words = f" {' '.join(bare(unit))} "
        return any(k in words or (words.strip() and words in k) for k in kept)

    while len(" ".join(parts)) > limit:
        groups = []
        for k, lead in enumerate(parts):
            if not lead.endswith(":"):
                continue
            end = k + 1
            while end < len(parts) and ROMAN_ITEM.match(parts[end]):
                end += 1
            if end > k + 1 and not any(changed(u) for u in parts[k + 1 : end]):
                groups.append((sum(len(u) for u in parts[k + 1 : end]), k, end))
        if not groups:
            break
        _, k, end = max(groups)
        lead = re.sub(r",?\s*(?:i\.e\.|e\.g\.)?,?\s*:$", ";", parts[k])
        parts = parts[:k] + [lead] + parts[end:]
    return fit(" ".join(parts), limit)


def fit(text: str, limit: int = MAX_TEXT) -> str:
    """The text, cut at the last sentence or list item that ends within `limit` characters."""
    if len(text) <= limit:
        return text
    head = text[:limit]
    end = max(head.rfind(". "), head.rfind("; "), head.rfind(": "))
    return head[: end + 1] if end > limit // 2 else quote(text, limit)


def overlap(a: str, b: str) -> float:
    """Shared words over total words, ignoring order: a requirement often reorders its clauses."""
    ca, cb = Counter(bare(a)), Counter(bare(b))
    total = sum(ca.values()) + sum(cb.values())
    return 2 * sum((ca & cb).values()) / total if total else 0.0
