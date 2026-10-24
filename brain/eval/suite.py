"""Run the brain on every labelled case (dev + synthetic) and log F2 per level.

    uv run python -m eval.suite [--no-llm] [--tag note]
    uv run python -m eval.suite --model sonnet --tag sonnet   # Claude on both tiers (paid)

Appends one row per case to eval/results.csv so changes can be compared over time, with the
models that ran and the cost of the paid calls each case made.
"""

from __future__ import annotations

import argparse
import csv
import fnmatch
import json
import os
import time
from pathlib import Path

from brain import llm
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
    ap.add_argument(
        "--model",
        help="run Claude on both tiers: opus, sonnet, fable or a model id (sets BRAIN_LLM)",
    )
    args = ap.parse_args(argv)
    if args.model:
        os.environ["BRAIN_LLM"] = "anthropic"
        os.environ["BRAIN_MODEL"] = args.model
    paid = not args.no_llm and llm.available()
    models = f"{llm.model_for('strong')} / {llm.model_for('bulk')}" if paid else ""
    rows = []
    for case in labelled_cases():
        if not fnmatch.fnmatch(case.name, args.cases):
            continue
        before = llm.usage(), llm.usage(cached=True)
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
            "llm": llm.provider() if paid else "none",
            "models": models,
            # Spent by this run, and the full cost of the output including cache hits.
            "cost_usd": _case_cost(before[0], llm.usage()),
            "cost_full_usd": _case_cost(before[0], llm.usage(), before[1], llm.usage(cached=True)),
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
            f"page F2 {row['page_f2']:.3f}  req F2 {row['requirement_f2']:.3f}  "
            f"${row['cost_usd'] or 0:.2f} spent, ${row['cost_full_usd'] or 0:.2f} full",
            flush=True,
        )
    _append(rows)
    print(llm.usage_line())
    return 0


def _case_cost(*pairs: llm.Usage) -> float | str:
    """USD between each (before, after) pair of usage snapshots, summed."""
    total = 0.0
    for before, after in zip(pairs[::2], pairs[1::2], strict=True):
        delta = {
            model: {k: v - before.get(model, {}).get(k, 0) for k, v in counts.items()}
            for model, counts in after.items()
        }
        usd = llm.cost(delta)
        if usd is None:
            return ""
        total += usd
    return round(total, 3)


def _append(rows: list[dict[str, object]]) -> None:
    """Append rows; rewrite the file once if this run adds columns older rows lack."""
    fields = list(rows[0])
    old: list[dict[str, str]] = []
    rewrite = not RESULTS.exists()
    if not rewrite:
        with RESULTS.open(newline="") as f:
            reader = csv.DictReader(f)
            if list(reader.fieldnames or []) != fields:
                old, rewrite = list(reader), True
                fields = list(dict.fromkeys([*(reader.fieldnames or []), *fields]))
    mode = "w" if rewrite else "a"
    with RESULTS.open(mode, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, restval="")
        if mode == "w":
            writer.writeheader()
            writer.writerows(old)
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
