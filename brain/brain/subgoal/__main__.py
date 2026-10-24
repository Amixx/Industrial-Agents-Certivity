"""The sub-goal command: two regulation PDFs and the old requirements in, a submission out.

    uv run python -m brain.subgoal --old-pdf ../subgoal/dev/old.pdf --new-pdf ../subgoal/dev/new.pdf
        --requirements-old ../subgoal/dev/requirements_old.json --case-id subgoal-dev --out out.json

Exits 1 when the file fails tools/validate.py.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from brain.subgoal import run, validate


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--old-pdf", type=Path, required=True)
    ap.add_argument("--new-pdf", type=Path, required=True)
    ap.add_argument("--requirements-old", type=Path, required=True)
    ap.add_argument("--case-id", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--team-id", default="team-06")
    ap.add_argument("--to-version", help="version label of the new PDF, if it is not in the index")
    args = ap.parse_args(argv)
    start = time.monotonic()
    requirements = json.loads(args.requirements_old.read_text())
    submission = run(
        args.old_pdf, args.new_pdf, requirements, args.case_id, args.team_id, args.to_version
    )
    problems = validate(submission, requirements)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(submission, indent=2, ensure_ascii=False) + "\n")
    counts = {
        k: sum(c["change"] == k for c in submission["changes"])
        for k in ("modified", "removed", "added")
    }
    print(
        f"{len(requirements)} old requirements, {len(submission['changes'])} changes {counts}, "
        f"{time.monotonic() - start:.1f} s -> {args.out}",
        file=sys.stderr,
    )
    for problem in problems:
        print(f"invalid: {problem}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
