"""Change records: modified and removed rows for old requirements, added rows for new paragraphs."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Sequence
from typing import Any

from brain.features import UNITS
from brain.models import Paragraph

from .align import Link, Span, units
from .text import (
    ITEM,
    MAX_TEXT,
    Op,
    bare,
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
# A modal verb with what binds to it: "shall not", "shall aim to", "must also".
MODAL_PHRASE = re.compile(
    r"\b(?:shall|must|may)(?:\s+(?:not|only|also))*(?:\s+aim\s+(?:not\s+)?to)?"
)
# A second verb phrase after "and" or "but": "… and assessed by …", "…, and shall provide …".
CONJOINED = re.compile(r",?\s+(?:and|but)\s+((?:shall|must|may)\b\s*)?((?:\w+ly\s+)?(\w+))")
PRONOUN = re.compile(r"^(?:This|It)\s+(?=(?:shall|must|may)\b)")
# ", and <a subject of up to six words> shall …": a second obligation with its own subject.
CLAUSE = re.compile(r",\s+and\s+(?=(?:[a-z][\w-]*\s+){1,6}?(?:shall|must|may)\b)")
CONDITION = re.compile(r"^((?:If|When|Where|While|Whilst)\b[^,]*),\s+(?:then\s+)?")
OWN_LEAD = re.compile(r"(.*\b(?:shall|must|may)\b.*?),?\s+and\s+the\s+following\s+shall\s+apply:$")
PARTICIPLE = re.compile(r"(?:ed|en|wn|kept|made|held|sent|set|put|done|built)$")
ACRONYM = re.compile(r"\b[A-Z][A-Z0-9]{2,5}\b")
# Acronyms of standards and bodies, which a regulation cites but is not about.
NOT_SYSTEMS = {"ISO", "IEC", "ECE", "SAE", "ASTM", "TRANS", "CEN", "DIN", "UNECE", "EEC", "GRSG"}
NOT_SYSTEMS |= {"GRVA", "GRSP", "GRE", "GRB", "GRPE", "GRRF", "WLTP", "ADR"}


def _paragraph_edits(label: str, old_units: Sequence[Span], new_units: Sequence[Span]) -> list[Op]:
    """The word edits between a paragraph's old and new text, under the same label."""
    old = " ".join(u.text for u in old_units if u.label == label)
    new = " ".join(u.text for u in new_units if u.label == label)
    return substantive(word_ops(old, new), old) if old and new else []


def system_name(paragraphs: Sequence[Paragraph], minimum: int = 10) -> str:
    """The system the regulation is about, by its acronym ("ACPE" in UN R175), or "".

    Candidates are the acronyms defined in parentheses in the scope, section 1 ("This Regulation
    applies to … (ACPE)"); the most frequent across the document wins if it occurs `minimum` times.
    """
    scope = " ".join(
        p.text for p in paragraphs if not p.annex and (p.label == "1" or p.label.startswith("1."))
    )
    candidates = set(re.findall(r"\(([A-Z][A-Z0-9]{2,5})\)", scope)) - NOT_SYSTEMS
    counts = Counter(a for p in paragraphs for a in ACRONYM.findall(p.text) if a in candidates)
    if not counts:
        return ""
    name, n = counts.most_common(1)[0]
    return name if n >= minimum else ""


def _renamed(text: str, headings: Sequence[str], new_words: str, system: str) -> str:
    """The text with a name the new version no longer has replaced by the system's name.

    A requirement often names the test or part its paragraph was about ("For the accelerator
    control misapplication test, …", from the old heading). When that heading's words appear
    nowhere in the new version, the name is stale: "accelerator control misapplication test"
    becomes "ACPE test", keeping the head noun.
    """
    for heading in headings:
        words = heading.rstrip(",.:").split()
        if len(words) < 2 or f" {' '.join(bare(heading))} " in new_words:
            continue
        name = " ".join(words)
        head = words[-1].lower()
        text = re.sub(re.escape(name), f"{system} {head}" if system else head, text, flags=re.I)
    return text


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


def own_words_edit(req_text: str, edits: Sequence[Op]) -> str | None:
    """The requirement with the paragraph's replacements applied, when it holds a replaced phrase
    of at least two words; None when it holds none (a one-word match such as "it" is chance)."""
    own = [op for op in edits if op[0] == "replace" and len(op[1].split()) >= 2]
    own = [op for op in own if op[1] in req_text]
    if not own:
        return None
    text = req_text
    for _, old, new, _ in own:
        text = text.replace(old, new, 1)
    return re.sub(r"[\s,;]+\.$", ".", norm(text))


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
    new: Sequence[Paragraph] = (),
    system: str = "",
    inclusive: bool = False,
) -> list[dict[str, Any]]:
    """Modified and removed changes, in requirement order. Unchanged requirements are left out.

    With the new version's paragraphs and the system's name, a name the new version no longer
    has is replaced in the modified text (see `_renamed`). `inclusive` also flags a requirement
    whose own sentences stay unchanged in a paragraph amended around them, that moved unchanged
    to a new number, or whose cited paragraph has a changed paragraph below it (for recall; the
    dev gold flags none of these).
    """
    old_units = units(old)
    old_by_label = {p.label: p for p in old}
    old_by_id = {p.id: p for p in old}
    new_words = f" {' '.join(bare(' '.join(p.text for p in new)))} " if new else ""
    by_old: dict[int, list[Link]] = defaultdict(list)
    for link in links:
        if link.old:
            by_old[link.old.index].append(link)
    new_units = sorted((link.new for link in links if link.new), key=lambda s: s.index)
    changed_labels = {
        span.label
        for link in links
        if link.ops or link.old is None or link.new is None
        for span in (link.old, link.new)
        if span
    }
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
        new_text = " ".join(s.text for s in region)
        ops = substantive(word_ops(old_text, new_text), old_text)
        if (unchanged and all(u.index in mine for u in region)) or not ops:
            # Moved, merged or split without a change of wording; or unchanged in a paragraph
            # amended around it, which only the inclusive mode reports.
            moved_to = region[0].label
            if inclusive and moved_to != old_label and all(u.label == moved_to for u in region):
                changes.append(
                    {
                        "requirement_id": req["id"],
                        "change": "modified",
                        "new_text": fit(req["text"]),
                        "reason": f"Paragraph {moved_to} (formerly {old_label}) of {regulation} "
                        f"was renumbered in version {to_version}; its wording did not change.",
                        "source": {"page": region[0].page, "paragraph": moved_to},
                        "old_span": old_text,
                        "new_span": new_text,
                    }
                )
            elif inclusive and all(u.label == old_label for u in region):
                if edits := _paragraph_edits(old_label, old_units, new_units):
                    changes.append(
                        {
                            "requirement_id": req["id"],
                            "change": "modified",
                            "new_text": fit(own_words_edit(req["text"], edits) or req["text"]),
                            "reason": f"Paragraph {old_label} of {regulation} was amended in "
                            f"version {to_version}: {describe(edits)}.",
                            "source": {"page": region[0].page, "paragraph": old_label},
                            "old_span": old_text,
                            "new_span": new_text,
                        }
                    )
                elif below := sorted(
                    lab for lab in changed_labels if lab != cited and _within(lab, cited)
                ):
                    changes.append(
                        {
                            "requirement_id": req["id"],
                            "change": "modified",
                            "new_text": fit(req["text"]),
                            "reason": f"Paragraph {cited} of {regulation} was amended in version "
                            f"{to_version}: paragraph {below[0]} below it changed.",
                            "source": {"page": region[0].page, "paragraph": old_label},
                            "old_span": old_text,
                            "new_span": new_text,
                        }
                    )
            continue
        label = region[0].label
        formerly = f" (formerly {old_label})" if label != old_label else ""
        patched, applied = apply_ops(req["text"], old_text, ops)
        # The old requirement with the edits applied keeps its explicit subject ("The accelerator
        # control misapplication test procedures …"); the new sentence alone may not ("The test
        # procedures …"). The new wording is used only when an edit finds no place in it.
        text = patched if applied == len(ops) else new_text
        if new_words and (para := old_by_label.get(old_label)):
            chain = [para, *(old_by_id[i] for i in reversed(para.path) if i in old_by_id)]
            text = _renamed(text, [p.heading for p in chain if p.heading], new_words, system)
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
                "new_units": [u.index for u in region],
            }
        )
    return changes


def cited_sections(requirements: Sequence[dict[str, Any]], old: Sequence[Paragraph]) -> set[str]:
    """The top-level sections the requirements cite. A label the old version does not have (a
    table id such as "tb:678427e5…") counts the sections of the paragraphs on its page."""
    labels = {p.label for p in old}
    sections = set()
    for req in requirements:
        label, page = req["source"]["paragraph"], req["source"].get("page")
        if label in labels or not page:
            sections.add(top(label))
        else:
            sections |= {top(p.label) for p in old if p.page <= page <= p.page_end}
    return sections


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
    if re.search(r"\bfollowing\b", head):
        head += ":"  # "… both of the following conditions are fulfilled: the driver is …"
    body = re.sub(r"[;,]?\s+(?:or|and)$", "", body).rstrip(" ,;")
    text = f"{head} {_lower(body)}" + (f" {_lower(tail)}" if tail else "")
    return text.rstrip(".") + "."


def _sentence_rows(unit: Span, every: bool = False) -> list[tuple[str, str]]:
    text = unit.text
    if not MODAL.search(text):
        keep = every or UNITS.search(text)
        return [(_quoted(unit), _with_lead(unit, text))] if keep else []
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


def verbs(spans: Sequence[Span]) -> set[str]:
    """The words a modal verb governs anywhere in the text ("shall provide", "may deviate")."""
    found = set()
    for unit in spans:
        for m in MODAL_PHRASE.finditer(unit.text):
            if word := re.match(r"\s+([a-z]+)", unit.text[m.end() :]):
                found.add(word[1])
    return found - {"be", "not", "only", "also"}


def split_obligation(text: str, known: set[str]) -> list[str]:
    """One sentence per verb phrase joined to the first modal verb: "X shall be documented by A
    and assessed by B." gives "X shall be documented by A." and "X shall be assessed by B.".

    A conjunct counts when it has its own modal verb, is a participle after "shall be", or starts
    with a verb in `known`. Nouns joined by "and" stay one obligation; [] when nothing splits.
    """
    m = MODAL_PHRASE.search(text)
    if not m:
        return []
    subject = text[: m.start()].strip()
    modal = m[0]
    rest = text[m.end() :]
    if passive := re.match(r"\s+be\b", rest):
        modal += " be"
        rest = rest[passive.end() :]
    cuts: list[tuple[int, int, bool]] = []  # (conjunction, verb, own modal verb)
    for c in CONJOINED.finditer(rest):
        word = c[3]
        start = cuts[-1][1] if cuts else 0
        before = rest[start : c.start()]
        # Bare paired verbs ("documented and explained") are one obligation, and so are
        # infinitives inside a complement ("the ability to recognize and offer …").
        complement = len(before.split()) >= 2 and not re.search(r"\bto\s+\w+$", before)
        if c[1] or (complement and (PARTICIPLE.search(word) if passive else word in known)):
            cuts.append((c.start(), c.start(1) if c[1] else c.start(2), bool(c[1])))
    if not cuts:
        return []
    parts = [f"{subject} {modal}{rest[: cuts[0][0]]}"]
    for k, (_, verb, own) in enumerate(cuts):
        end = cuts[k + 1][0] if k + 1 < len(cuts) else len(rest)
        parts.append(f"{subject} {'' if own else modal + ' '}{rest[verb:end]}")
    return [re.sub(r"[\s,;:.]+$", "", p) + "." for p in parts]


def split_clauses(text: str) -> list[str]:
    """One sentence per clause with its own subject and modal verb: "If X, then A shall B, and C
    shall D." gives "If X, then A shall B." and "If X, C shall D."; [] when there is one."""
    m = CLAUSE.search(text)
    if not m or not MODAL.search(text[: m.start()]):
        return []
    second = text[m.end() :]
    if cond := CONDITION.match(text):
        second = f"{cond[1]}, {second}"
    else:
        second = second[0].upper() + second[1:]
    return [text[: m.start()].rstrip(" ,") + ".", second.rstrip(" .") + "."]


def resolve_pronoun(text: str, previous: str) -> str:
    """ "This shall …" names what the previous sentence is about: its object when it is active
    ("… shall provide evidence of X." gives "The evidence of X shall …"), its subject when it is
    passive ("X may be performed …" gives "X shall …")."""
    pronoun = PRONOUN.match(text)
    m = MODAL_PHRASE.search(previous)
    if not pronoun or not m:
        return text
    rest = previous[m.end() :].strip()
    if re.match(r"be\b", rest):
        noun = previous[: m.start()].strip().split(", ")[-1]
    elif len(words := rest.split(maxsplit=1)) == 2:
        noun = words[1]
    else:
        return text
    noun = re.sub(r"[\s.;:,]+$", "", noun)
    if not re.match(r"(?:the|a|an|such|its|their)\b", noun, re.I):
        noun = f"the {noun}"
    return f"{noun[0].upper()}{noun[1:]} {text[pronoun.end() :]}"


def obligations(spans: Sequence[Span], every: bool = False) -> list[tuple[str, str]]:
    """(quote, requirement text) for each obligation in a new paragraph's units.

    Items under a lead-in with a modal verb ("… shall be as follows:") are one row each. A lead-in
    without one ("… is not required when:") stays one row with its items. Other sentences count
    when they have a modal verb or a number with a unit (every sentence, with `every`); "X shall A,
    and may B" gives two rows.
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
            if every or MODAL.search(joined) or UNITS.search(joined):
                rows.append((f"{unit.lead} {joined}" if unit.lead else joined, joined))
        else:
            rows += _sentence_rows(unit, every)
        k += 1 + len(items)
    return rows


def added_changes(
    links: Sequence[Link],
    sections: set[str],
    regulation: str,
    to_version: str,
    consumed: frozenset[int] | set[int] = frozenset(),
    inclusive: bool = False,
) -> list[dict[str, Any]]:
    """Added changes in the given top-level sections, in document order.

    A new paragraph (some units new, none but lead-ins from the old version) gives one row per
    obligation. A new full sentence inside an old paragraph gives one row too, unless it is a list
    item (part of the list's requirement), a footnote, or already in the new text of a modified
    requirement (`consumed`, indexes of new units).

    `inclusive` (for recall) takes every section instead of only the cited `sections`, counts new
    list items inside old paragraphs (fused with their lead-in when it has a modal verb) and new
    sentences already in a modified requirement, and gives a compound obligation one row per verb
    (`split_obligation`). Only rows with a modal verb are kept: on the held-out pair the 60 rows
    without one matched no gold row.
    """
    claimed = {link.new.index for link in links if link.old and link.new}
    by_label: dict[str, list[Span]] = defaultdict(list)
    for unit in sorted((link.new for link in links if link.new), key=lambda s: s.index):
        by_label[unit.label].append(unit)
    known = verbs([u for spans in by_label.values() for u in spans]) if inclusive else set()
    changes: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    def add(label: str, page: int, text: str, reason: str) -> None:
        texts = [text]
        if inclusive:
            if not MODAL.search(text):
                return
            if changes:
                text = resolve_pronoun(text, changes[-1]["new_text"])
            texts = [
                part
                for clause in split_clauses(text) or [text]
                for part in split_obligation(clause, known) or [clause]
            ]
        for t in texts:
            if (label, t) not in seen:
                seen.add((label, t))
                changes.append(
                    {
                        "requirement_id": None,
                        "change": "added",
                        "new_text": fit(t),
                        "reason": reason,
                        "source": {"page": page, "paragraph": label},
                    }
                )

    for label, spans in by_label.items():
        in_scope = inclusive or top(label) in sections
        if not in_scope or all(s.index in claimed for s in spans):
            continue
        if not any(s.index in claimed and not s.text.endswith(":") for s in spans):
            for quoted, text in obligations(spans, every=inclusive):
                add(
                    label,
                    spans[0].page,
                    text,
                    f"Paragraph {label} of {regulation} is new in version {to_version}: "
                    f"'{quote(quoted, ADDED_QUOTE)}'.",
                )
            continue
        for k, unit in enumerate(spans):
            item = re.match(ITEM, unit.text)
            own = OWN_LEAD.match(unit.text) if inclusive else None
            if (
                unit.index in claimed
                or (unit.index in consumed and not (inclusive and not item))
                or (item and not inclusive)
                or re.match(r"\d", unit.text)
                or (unit.text.endswith(":") and not own)
            ):
                continue
            reason = (
                f"Paragraph {label} of {regulation} was amended in version {to_version}: "
                f"'{quote(unit.text, ADDED_QUOTE)}' was added."
            )
            if own:  # "X shall A and the following shall apply:" states A itself
                add(label, spans[0].page, own[1] + ".", reason)
                continue
            lead = _lead_in(spans[:k]) if item else None
            if item and ((lead and MODAL.search(lead)) or MODAL.search(unit.text)):
                add(label, spans[0].page, fuse(lead or "", unit.text), reason)
                continue
            for _, text in obligations([unit], every=inclusive):
                add(label, spans[0].page, text, reason)
    return changes


def _lead_in(before: Sequence[Span]) -> str | None:
    """The lead-in ("… as follows:") of a list whose earlier items are `before`, without its own
    item marker when the lead-in is an item itself ("(a) The system shall … the following:")."""
    for unit in reversed(before):
        if unit.text.endswith(":"):
            return re.sub(rf"^{ITEM}", "", unit.text).strip()
        if not re.match(ITEM, unit.text):
            return None
    return None
