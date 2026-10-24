"""Run the brain on every labelled case (dev + synthetic) and log F2 per level.

    uv run python -m eval.suite [--no-llm] [--tag note]

Appends one row per case to eval/results.csv so changes can be compared over time.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

from brain.paths import CASES, PROJECT
from brain.pipeline import run

from .score import score
from .synth import cases as synthetic_cases

RESULTS = PROJECT / "eval" / "results.csv"


def labelled_cases() -> list[Path]:
    dev = [p for p in sorted(CASES.iterdir()) if (p / "expected.json").exists()]
    return dev + synthetic_cases()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--tag", default="")
    args = ap.parse_args(argv)
    rows = []
    for case in labelled_cases():
        image = case / "exploded_view.png"
        sub = run(
            (case / "spec.md").read_text(),
            image if image.exists() else None,
            case_id=case.name,
            use_llm=False if args.no_llm else None,
        )
        r = score(sub, json.loads((case / "expected.json").read_text()))
        row = {
            "time": time.strftime("%Y-%m-%d %H:%M"),
            "tag": args.tag,
            "case": case.name,
            "n": len(sub["requirements"]),
        }
        for level in ("regulation", "page", "requirement"):
            m = r[f"{level}_level"]
            row |= {
                f"{level}_p": round(m["precision"], 3),
                f"{level}_r": round(m["recall"], 3),
                f"{level}_f2": round(m["f2"], 3),
            }
        rows.append(row)
        print(
            f"{case.name:32s} n={row['n']:4d}  reg F2 {row['regulation_f2']:.3f}  "
            f"page F2 {row['page_f2']:.3f}  req F2 {row['requirement_f2']:.3f}"
        )
    new = not RESULTS.exists()
    with RESULTS.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        if new:
            writer.writeheader()
        writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
