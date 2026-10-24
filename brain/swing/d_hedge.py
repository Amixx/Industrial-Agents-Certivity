"""Lane D: hedge granularity by submitting a fine and a coarse cut of the same paragraphs.

    uv run python swing/d_hedge.py FINE.json COARSE.json [--write PREFIX] [--only NAME ...]

FINE and COARSE are two rewrites of the same paragraph set. The script builds hedged variants
(the union, and selective hedges by relevance or by row-count disagreement), scores each with
the local lexical judge and prints one table. With --write it saves the named variants as
`out/rear-lamp-swing-D-<PREFIX>-<name>.json`.
"""

from __future__ import annotations

import argparse
import collections
import copy
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from brain.paths import CASES
from eval import judge
from eval.score import fbeta, paragraph_key

Row = dict[str, Any]
Key = tuple[str, str | None]
OUT = Path(__file__).resolve().parents[2] / "out"


def key(r: Row) -> Key:
    return r["source"]["regulation"], paragraph_key(r["source"].get("paragraph"))


def norm(text: str) -> str:
    return " ".join(text.lower().split()).rstrip(".")


def group(rows: list[Row]) -> dict[Key, list[Row]]:
    g: dict[Key, list[Row]] = collections.defaultdict(list)
    for r in rows:
        g[key(r)].append(r)
    return g


def merge(first: list[Row], second: list[Row], near: float = 1.0) -> list[Row]:
    """`first`, then the rows of `second` that are not a duplicate of a kept row. A duplicate is
    the same normalised text, or lexical similarity >= `near` when `near` < 1."""
    out = list(first)
    for r in second:
        if any(norm(r["text"]) == norm(o["text"]) for o in out):
            continue
        if near < 1.0 and any(judge.similarity(r["text"], o["text"]) >= near for o in out):
            continue
        out.append(r)
    return out


Policy = Callable[[Key, list[Row], list[Row]], list[Row]]


def build(fine: list[Row], coarse: list[Row], policy: Policy) -> list[Row]:
    gf, gc = group(fine), group(coarse)
    order = list(dict.fromkeys([*gf, *gc]))
    rows: list[Row] = []
    for k in order:
        rows.extend(policy(k, gf.get(k, []), gc.get(k, [])))
    out = []
    for i, r in enumerate(rows, 1):
        r = copy.deepcopy(r)
        r["id"] = f"R-{i:04d}"
        out.append(r)
    return out


def conf(rows: list[Row]) -> float:
    return max((r.get("confidence") or 0.0 for r in rows), default=0.0)


def policies() -> dict[str, Policy]:
    p: dict[str, Policy] = {
        "fine": lambda k, f, c: f,
        "coarse": lambda k, f, c: c,
        "union": lambda k, f, c: merge(f, c),
        "union-near08": lambda k, f, c: merge(f, c, 0.8),
        "union-near06": lambda k, f, c: merge(f, c, 0.6),
        # Hedge only where the cuts disagree on the row count; first file elsewhere.
        "diff-fine": lambda k, f, c: merge(f, c) if len(f) != len(c) else (f or c),
        "diff-coarse": lambda k, f, c: merge(f, c) if len(f) != len(c) else (c or f),
    }
    for t in (0.4, 0.5, 0.6):
        p[f"rel{t}-fine"] = lambda k, f, c, t=t: merge(f, c) if conf(f + c) >= t else (f or c)
        p[f"rel{t}-coarse"] = lambda k, f, c, t=t: merge(f, c) if conf(f + c) >= t else (c or f)
        p[f"rel{t}-or-diff"] = lambda k, f, c, t=t: (
            merge(f, c) if conf(f + c) >= t or len(f) != len(c) else (f or c)
        )
    # Keep the first file's paragraph set; on each of its paragraphs add the second file's rows
    # whose similarity to every row already kept is below `t`.
    for t in (0.35, 0.4, 0.45, 0.5, 0.6):
        p[f"first-near{t}"] = lambda k, f, c, t=t: merge(f, c, t) if f else []
    return p


def evaluate(rows: list[Row], exp: list[Row]) -> dict[str, Any]:
    pairs = judge.match(rows, exp)
    m = len(pairs)
    p, r = m / max(1, len(rows)), m / len(exp)
    return {"rows": len(rows), "matched": m, "f2": fbeta(p, r), "pairs": pairs}


def side_report(fine: list[Row], coarse: list[Row], union: list[Row], exp: list[Row]) -> str:
    """Which gold rows each cut matches alone, and how the union's matches split by source."""
    mf = {j for _, j, _ in judge.match(fine, exp)}
    mc = {j for _, j, _ in judge.match(coarse, exp)}
    mu = {j for _, j, _ in judge.match(union, exp)}
    return (
        f"gold matched: fine {len(mf)}, coarse {len(mc)}, both {len(mf & mc)}, "
        f"either {len(mf | mc)}, union file {len(mu)}"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("fine")
    ap.add_argument("coarse")
    ap.add_argument("--expected", default=str(CASES / "dev-rear-lamp" / "expected.json"))
    ap.add_argument("--write", help="file name prefix for saved variants")
    ap.add_argument("--only", nargs="*", default=[], help="variants to save")
    args = ap.parse_args(argv)
    fine_doc = json.loads(Path(args.fine).read_text())
    fine = fine_doc["requirements"]
    coarse = json.loads(Path(args.coarse).read_text())["requirements"]
    exp = json.loads(Path(args.expected).read_text())["requirements"]
    print(f"fine {args.fine} ({len(fine)} rows), coarse {args.coarse} ({len(coarse)} rows)")
    results = {}
    for name, pol in policies().items():
        rows = build(fine, coarse, pol)
        res = evaluate(rows, exp)
        results[name] = (rows, res)
        print(f"{name:<16}{res['rows']:>5} rows {res['matched']:>4} matched  F2 {res['f2']:.3f}")
    print(side_report(fine, coarse, results["union"][0], exp))
    if args.write:
        for name in args.only:
            rows, res = results[name]
            doc = dict(fine_doc, requirements=rows)
            path = OUT / f"rear-lamp-swing-D-{args.write}-{name}.json"
            path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
            path.with_suffix(".log").write_text(
                f"d_hedge.py {args.fine} {args.coarse} variant {name}: {res['rows']} rows, "
                f"{res['matched']} matched locally, F2 {res['f2']:.3f}; no model calls, $0\n"
            )
            print(f"wrote {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
