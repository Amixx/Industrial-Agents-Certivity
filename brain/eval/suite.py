"""Run the brain on every labelled case (dev + synthetic) and log F2 per level.

    uv run python -m eval.suite [--no-llm] [--tag note]

Appends one row per case to eval/results.csv so changes can be compared over time.
"""

from __future__ import annotations

import argparse
import csv
import fnmatch
import json
import time
from pathlib import Path

from brain.paths import CASES, PROJECT, ROOT
from brain.pipeline import run

from .score import score
from .synth import cases as synthetic_cases

RESULTS = PROJECT / "eval" / "results.csv"
TIER_A = ROOT / "synthetic" / "cases"  # synthetic/README.md


def labelled_cases() -> list[Path]:
    dev = [p for p in sorted(CASES.iterdir()) if (p / "expected.json").exists()]
    tier_a = sorted(p for p in TIER_A.glob("*") if (p / "expected.json").exists())
    return dev + synthetic_cases() + tier_a


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--tag", default="")
    ap.add_argument("--cases", default="*", help="glob on case names, e.g. 'synth-a*'")
    ap.add_argument("--include", nargs="*", default=[], help="force regulations in, every case")
    ap.add_argument("--exclude", nargs="*", default=[], help="force regulations out, every case")
    args = ap.parse_args(argv)
    rows = []
    for case in labelled_cases():
        if not fnmatch.fnmatch(case.name, args.cases):
            continue
        image = case / "exploded_view.png"
        sub = run(
            (case / "spec.md").read_text(),
            image if image.exists() else None,
            case_id=case.name,
            use_llm=False if args.no_llm else None,
            include=args.include,
            exclude=args.exclude,
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
        stats = sub["run"]
        row |= {
            "wall_s": stats["wall_s"],
            "llm": stats["provider"],
            "llm_calls": stats["calls"],
            "cache_hits": stats["cache_hits"],
            "input_tokens": stats["input_tokens"],
            "output_tokens": stats["output_tokens"],
            "cost_usd": round(stats["cost_usd"], 4),
            "cold_cost_usd": round(stats["cold_cost_usd"], 4),
            "unpriced_calls": stats["unpriced_calls"],
        }
        rows.append(row)
        print(
            f"{case.name:32s} n={row['n']:4d}  reg F2 {row['regulation_f2']:.3f}  "
            f"page F2 {row['page_f2']:.3f}  req F2 {row['requirement_f2']:.3f}"
        )
    append(rows)
    return 0


def append(rows: list[dict[str, object]]) -> None:
    """Add rows to RESULTS; older rows get empty cells for columns added since."""
    old: list[dict[str, str]] = []
    fields = list(rows[0])
    if RESULTS.exists():
        with RESULTS.open(newline="") as f:
            reader = csv.DictReader(f)
            old = list(reader)
            fields = list(reader.fieldnames or []) + [
                k for k in rows[0] if k not in (reader.fieldnames or [])
            ]
    with RESULTS.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(old)
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
