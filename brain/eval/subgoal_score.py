"""Strict local scorer for the sub-goal against its gold.

    uv run python -m eval.subgoal_score out.json [--expected ../subgoal/dev/expected.json]

Modified and removed rows match the gold on requirement_id. Added rows match one to one within the
same source paragraph, by new_text similarity (at least 0.5). Flag recall is the share of gold rows
matched; change accuracy is the share of matched rows with the gold's change type. Exact reasons and
new_text similarity are reported too, with every mismatch.
"""

from __future__ import annotations

import argparse
import difflib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from brain.paths import ROOT

EXPECTED = ROOT / "subgoal" / "dev" / "expected.json"
MIN_ADDED_MATCH = 0.5

Change = dict[str, Any]


@dataclass
class Report:
    flag_recall: float
    change_accuracy: float
    added_recall: float
    reason_exact: float
    new_text_similarity: float
    extra: int
    mismatches: list[str] = field(default_factory=list)


def similarity(a: str | None, b: str | None) -> float:
    if not a or not b:
        return 1.0 if a == b else 0.0
    return difflib.SequenceMatcher(
        None, a.lower().split(), b.lower().split(), autojunk=False
    ).ratio()


def _paragraph(c: Change) -> str:
    return str((c.get("source") or {}).get("paragraph", ""))


def _pairs(
    submitted: list[Change], gold: list[Change]
) -> tuple[list[tuple[Change, Change]], list[Change]]:
    """One-to-one (submitted, gold) pairs, and the submitted rows left over."""
    pairs: list[tuple[Change, Change]] = []
    used: set[int] = set()
    by_id = {
        c["requirement_id"]: i
        for i, c in reversed(list(enumerate(submitted)))
        if c.get("requirement_id")
    }
    for g in gold:
        if g.get("requirement_id"):
            i = by_id.get(g["requirement_id"])
            if i is not None:
                pairs.append((submitted[i], g))
                used.add(i)
    candidates = [
        (similarity(s.get("new_text"), g.get("new_text")), i, j)
        for j, g in enumerate(gold)
        if not g.get("requirement_id")
        for i, s in enumerate(submitted)
        if not s.get("requirement_id") and _paragraph(s) == _paragraph(g)
    ]
    taken: set[int] = set()
    for sim, i, j in sorted(candidates, key=lambda t: (-t[0], t[1], t[2])):
        if sim < MIN_ADDED_MATCH or i in used or j in taken:
            continue
        pairs.append((submitted[i], gold[j]))
        used.add(i)
        taken.add(j)
    return pairs, [s for i, s in enumerate(submitted) if i not in used]


def _name(c: Change) -> str:
    return c.get("requirement_id") or f"added {_paragraph(c)}"


def score(submission: dict[str, Any], expected: dict[str, Any]) -> Report:
    submitted: list[Change] = submission["changes"]
    gold: list[Change] = expected["changes"]
    pairs, extra = _pairs(submitted, gold)
    matched = {id(g) for _, g in pairs}
    mismatches = [
        f"missed {_name(g)} ({g['change']}): {g['reason'][:120]}"
        for g in gold
        if id(g) not in matched
    ]
    same_type = reasons = 0
    sims: list[float] = []
    for s, g in pairs:
        name = _name(g)
        if s["change"] == g["change"]:
            same_type += 1
        else:
            mismatches.append(f"{name}: change {s['change']}, expected {g['change']}")
        if s.get("reason") == g["reason"]:
            reasons += 1
        else:
            mismatches.append(
                f"{name}: reason\n    got      {s.get('reason')}\n    expected {g['reason']}"
            )
        if g.get("source") != s.get("source"):
            mismatches.append(f"{name}: source {s.get('source')}, expected {g.get('source')}")
        if g.get("new_text"):
            sim = similarity(s.get("new_text"), g["new_text"])
            sims.append(sim)
            if sim < 1.0:
                mismatches.append(
                    f"{name}: new_text {sim:.2f}\n    got      {s.get('new_text')}"
                    f"\n    expected {g['new_text']}"
                )
    mismatches += [f"extra {_name(s)} ({s['change']}): {s.get('reason', '')[:120]}" for s in extra]
    gold_added = [g for g in gold if g["change"] == "added"]
    return Report(
        flag_recall=len(pairs) / len(gold) if gold else 1.0,
        change_accuracy=same_type / len(pairs) if pairs else 0.0,
        added_recall=(
            sum(1 for _, g in pairs if g["change"] == "added") / len(gold_added)
            if gold_added
            else 1.0
        ),
        reason_exact=reasons / len(gold) if gold else 1.0,
        new_text_similarity=sum(sims) / len(sims) if sims else 1.0,
        extra=len(extra),
        mismatches=mismatches,
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("submission", type=Path)
    ap.add_argument("--expected", type=Path, default=EXPECTED)
    args = ap.parse_args(argv)
    r = score(json.loads(args.submission.read_text()), json.loads(args.expected.read_text()))
    for line in r.mismatches:
        print(line)
    print(
        f"flag recall {r.flag_recall:.3f}  change accuracy {r.change_accuracy:.3f}  "
        f"added recall {r.added_recall:.3f}  exact reasons {r.reason_exact:.3f}  "
        f"new_text similarity {r.new_text_similarity:.3f}  extra {r.extra}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
