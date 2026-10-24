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
from pathlib import Path
from typing import Any

from brain.paths import CASES

from . import judge
from .score import fbeta, paragraph_key


def _key(r: dict[str, Any]) -> tuple[str, str | None]:
    return r["source"]["regulation"], paragraph_key(r["source"].get("paragraph"))


def report(sub: list[dict[str, Any]], exp: list[dict[str, Any]]) -> list[str]:
    gold = collections.Counter(_key(r) for r in exp)
    ours = collections.Counter(_key(r) for r in sub)
    pairs = judge.match(sub, exp)
    matched_sub = {i for i, _, _ in pairs}
    matched_exp = {j for _, j, _ in pairs}
    inside = [i for i, r in enumerate(sub) if _key(r) in gold]
    hit_inside = len(matched_sub & set(inside))
    missed = [j for j in range(len(exp)) if j not in matched_exp]
    on_cited = sum(1 for j in missed if _key(exp[j]) in ours)
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
