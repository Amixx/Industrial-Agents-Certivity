"""Scoring: F2 at the regulation, page and requirement levels.

    uv run python -m eval.score out.json [--expected ../cases/dev-rear-lamp/expected.json]

Regulation and page levels reuse Certivity's tools/score_local.py. The requirement level uses the
lexical proxy in eval.judge, so treat it as a relative signal between our own runs.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

from brain.paths import CASES, TOOLS

from . import judge

_spec = importlib.util.spec_from_file_location("score_local", TOOLS / "score_local.py")
assert _spec and _spec.loader
score_local = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(score_local)

paragraph_key = score_local._paragraph_key


def fbeta(precision: float, recall: float, beta: float = 2.0) -> float:
    b2 = beta * beta
    denominator = b2 * precision + recall
    return 0.0 if denominator == 0 else (1 + b2) * precision * recall / denominator


def score(
    submission: dict[str, Any], expected: dict[str, Any], threshold: float = 0.45
) -> dict[str, Any]:
    """score_local.score() plus a requirement level, with F2 on every level."""
    result: dict[str, Any] = score_local.score(submission, expected)
    sub, exp = submission["requirements"], expected["requirements"]
    matches = judge.match(sub, exp, threshold)
    result["requirement_level"] = score_local._prf(len(matches), len(sub), len(exp))
    for level in result.values():
        level["f2"] = fbeta(level["precision"], level["recall"])
    return result


def table(result: dict[str, Any]) -> str:
    lines = [f"{'level':<13}{'P':>7}{'R':>7}{'F2':>7}   cited/expected/matched"]
    for name, level in result.items():
        lines.append(
            f"{name.split('_')[0]:<13}{level['precision']:>7.3f}{level['recall']:>7.3f}"
            f"{level['f2']:>7.3f}   {level['n_submitted']}/{level['n_expected']}/"
            f"{level['n_matched']}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="F2 at three levels against an expected file.")
    ap.add_argument("submission")
    ap.add_argument("--expected", default=str(CASES / "dev-rear-lamp" / "expected.json"))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    result = score(
        json.loads(Path(args.submission).read_text()), json.loads(Path(args.expected).read_text())
    )
    print(json.dumps(result, indent=2) if args.json else table(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
