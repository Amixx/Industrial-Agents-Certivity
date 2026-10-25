"""Where a dev submission loses requirement-level points, by the local judge.

    uv run python -m eval.errors ../out/rear-lamp-fable.json [more.json ...]

For each file: rows inside and outside gold paragraphs (rows outside match nothing), gold rows
missed on paragraphs the file cites (wording or granularity) and on paragraphs it never cites
(selection), how its row count per gold paragraph compares with the gold, and the score if every
row outside gold paragraphs were dropped (the ceiling for paragraph selection).
"""

from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path
from typing import Any

from brain.paths import CASES

from . import judge
from .score import fbeta, paragraph_key

# The gold sometimes names the table in the paragraph ("5.1.4.4.1. Table 3"); its paragraph is
# the one before the table.
_TABLE = re.compile(r"\s+table\s+\S+$")


def _key(r: dict[str, Any]) -> tuple[str, str | None]:
    key = paragraph_key(r["source"].get("paragraph"))
    return r["source"]["regulation"], _TABLE.sub("", key) if key else key


def reason(
    key: tuple[str, str | None], gold: collections.Counter[Any], ours: collections.Counter[Any]
) -> str:
    """Why a gold row on paragraph `key` went unmatched: the file never cites the paragraph
    (`below_cut`), cites it with fewer rows than the gold (`split_finer`), or with as many rows
    that the judge did not pair (`worded_differently`)."""
    if not ours[key]:
        return "below_cut"
    return "split_finer" if ours[key] < gold[key] else "worded_differently"


def breakdown(sub: list[dict[str, Any]], exp: list[dict[str, Any]]) -> dict[str, Any]:
    """The judge's pairs, each unmatched gold row with its reason and the file's most similar row
    on the same paragraph (index, similarity and the gold row the judge paired it with, or
    None), and each unmatched row of the file with whether its paragraph is among the gold's."""
    gold = collections.Counter(_key(r) for r in exp)
    ours = collections.Counter(_key(r) for r in sub)
    pairs = judge.match(sub, exp)
    paired = {i: j for i, j, _ in pairs}
    matched_exp = set(paired.values())
    by_key: dict[tuple[str, str | None], list[int]] = collections.defaultdict(list)
    for i, r in enumerate(sub):
        by_key[_key(r)].append(i)
    missed = []
    for j, r in enumerate(exp):
        if j in matched_exp:
            continue
        near = max(
            ((judge.similarity(sub[i]["text"], r["text"]), i) for i in by_key[_key(r)]),
            default=None,
        )
        missed.append(
            {
                "index": j,
                "reason": reason(_key(r), gold, ours),
                "nearest": None
                if near is None
                else {"index": near[1], "similarity": near[0], "paired_with": paired.get(near[1])},
            }
        )
    extra = [
        {"index": i, "on_gold_paragraph": _key(r) in gold}
        for i, r in enumerate(sub)
        if i not in paired
    ]
    return {"pairs": pairs, "missed": missed, "extra": extra}


def report(sub: list[dict[str, Any]], exp: list[dict[str, Any]]) -> list[str]:
    gold = collections.Counter(_key(r) for r in exp)
    ours = collections.Counter(_key(r) for r in sub)
    found = breakdown(sub, exp)
    pairs = found["pairs"]
    matched_sub = {i for i, _, _ in pairs}
    inside = [i for i, r in enumerate(sub) if _key(r) in gold]
    hit_inside = len(matched_sub & set(inside))
    missed = found["missed"]
    on_cited = sum(1 for m in missed if m["reason"] != "below_cut")
    fewer = sum(1 for k, n in gold.items() if 0 < ours[k] < n)
    equal = sum(1 for k, n in gold.items() if ours[k] == n)
    more = sum(1 for k, n in gold.items() if ours[k] > n)
    m = len(pairs)
    p, r = m / max(1, len(sub)), m / len(exp)
    p2, r2 = hit_inside / max(1, len(inside)), hit_inside / len(exp)
    return [
        f"rows {len(sub)}: in gold paragraphs {len(inside)} (matched {hit_inside}), "
        f"outside {len(sub) - len(inside)} (matched {m - hit_inside})",
        f"gold rows missed: {on_cited} on cited paragraphs, {len(missed) - on_cited} on "
        "paragraphs never cited",
        f"gold paragraphs where we have fewer / equal / more rows than gold: {fewer} / {equal} "
        f"/ {more}",
        f"local judge: matched {m}, P {p:.3f} R {r:.3f} F2 {fbeta(p, r):.3f}",
        f"rows outside gold paragraphs dropped: P {p2:.3f} R {r2:.3f} F2 {fbeta(p2, r2):.3f}",
    ]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("submissions", nargs="+")
    ap.add_argument("--expected", default=str(CASES / "dev-rear-lamp" / "expected.json"))
    args = ap.parse_args(argv)
    exp = json.loads(Path(args.expected).read_text())["requirements"]
    for path in args.submissions:
        print(f"== {path}")
        for line in report(json.loads(Path(path).read_text())["requirements"], exp):
            print("   " + line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
