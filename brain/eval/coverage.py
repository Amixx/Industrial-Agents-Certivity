"""An assessment against the expert's answer, by the local judge, for the web app's coverage page.

    uv run python -m eval.coverage < assessment.json > coverage.json

Reads {"requirements": [...], "below_cut": [...]} on stdin, as the backend stores an assessment;
`below_cut` holds the scores of paragraphs the run cut, when it kept them. Writes the local
judge's totals, every expert row it leaves unmatched with the reason from `errors.breakdown`,
and every submitted row it leaves unmatched.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from brain.paths import CASES

from .errors import _key, breakdown
from .score import fbeta, paragraph_key


def _row(r: dict[str, Any]) -> dict[str, Any]:
    return {"id": r["id"], "text": r["text"], "source": r["source"]}


def coverage(
    sub: list[dict[str, Any]],
    exp: list[dict[str, Any]],
    below_cut: Sequence[dict[str, Any]] = (),
) -> dict[str, Any]:
    found = breakdown(sub, exp)
    cut: dict[tuple[str, str | None], dict[str, Any]] = {}
    for c in sorted(below_cut, key=lambda c: c["score"]):
        cut[c["regulation"], paragraph_key(c["paragraph"])] = c
    missed = []
    for m in found["missed"]:
        r = exp[m["index"]]
        row = {**_row(r), "reason": m["reason"]}
        if m["reason"] == "below_cut" and (hit := cut.get(_key(r))):
            row |= {"score": hit["score"], "cut": hit["cut"], "stage": hit["stage"]}
        if m["nearest"]:
            near = sub[m["nearest"]["index"]]
            row["nearest"] = {**_row(near), "similarity": round(m["nearest"]["similarity"], 3)}
            if (j := m["nearest"]["paired_with"]) is not None:
                row["nearest"]["paired_with"] = exp[j]["id"]
        missed.append(row)
    m = len(found["pairs"])
    p, r = m / max(1, len(sub)), m / max(1, len(exp))
    return {
        "local": {
            "expected": len(exp),
            "submitted": len(sub),
            "matched": m,
            "precision": round(p, 3),
            "recall": round(r, 3),
            "f2": round(fbeta(p, r), 3),
        },
        "missed": missed,
        "extra": [
            {**_row(sub[e["index"]]), "on_expert_paragraph": e["on_gold_paragraph"]}
            for e in found["extra"]
        ],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--expected", default=str(CASES / "dev-rear-lamp" / "expected.json"))
    args = ap.parse_args(argv)
    exp = json.loads(Path(args.expected).read_text())["requirements"]
    assessment = json.load(sys.stdin)
    out = coverage(assessment["requirements"], exp, assessment.get("below_cut") or [])
    json.dump(out, sys.stdout, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
