"""Lane B, steps 3 and 5: union the full rewrite with lane A's pool, then measure the tail.

    BRAIN_LLM= PYTHONPATH=. uv run python swing/b_tail.py union ../out/rear-lamp-swing-B-full.json \
        -o ../out/rear-lamp-swing-B-union.json
    BRAIN_LLM= PYTHONPATH=. uv run python swing/b_tail.py curve ../out/rear-lamp-swing-B-union.json
    BRAIN_LLM= PYTHONPATH=. uv run python swing/b_tail.py cut ../out/rear-lamp-swing-B-union.json \
        0.2 -o ../out/rear-lamp-swing-B-cut020.json

`union` adds one row (the cluster medoid) for every pool cluster that no row of the full file
covers: same regulation and paragraph, token Jaccard 0.5 or more with any cluster member (lane
A's clustering rule). Every row gets its paragraph's blend score as `confidence` (from
`out/experiments/B-scores.json`; 0 for a label that is not a candidate). Clusters outside the
pipeline's four regulations are skipped. `curve` scores nested cuts by that score with the
local judge, each cut matched on its own, so the one-to-one assignment is redone per file.
No model call.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from brain.paths import CASES
from brain.verify import base_versions, validate
from eval import judge
from eval.score import fbeta, paragraph_key

ROOT = Path(__file__).resolve().parents[2]
POOL = ROOT / "out" / "experiments" / "A-pool.json"
SCORES = ROOT / "out" / "experiments" / "B-scores.json"
EXPECTED = CASES / "dev-rear-lamp" / "expected.json"
CUTS = [0.5, 0.4, 0.3, 0.25, 0.2, 0.175, 0.15, 0.125, 0.1, 0.085, 0.07, 0.06, 0.05, 0.04, 0.03, 0.0]


def key(reg: str, par: str) -> tuple[str, str]:
    return reg, paragraph_key(par)


def blend_scores() -> dict[tuple[str, str], float]:
    return {
        key(s["regulation"], s["paragraph"]): s["blend"] for s in json.loads(SCORES.read_text())
    }


def union(full: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    rows = list(full["requirements"])
    scores = blend_scores()
    versions = base_versions()
    by_par: dict[tuple[str, str], list[str]] = {}
    for r in rows:
        by_par.setdefault(key(r["source"]["regulation"], r["source"]["paragraph"]), []).append(
            r["text"]
        )
    added = 0
    selected = {reg for reg, _ in scores}  # the pipeline's regulations; dev-upload also cites R26
    for c in json.loads(POOL.read_text())["clusters"]:
        if c["regulation"] not in selected:
            continue
        k = key(c["regulation"], c["paragraph"])
        ours = by_par.get(k, [])
        covered = any(
            judge.similarity(t, m["text"]) >= 0.5 or judge.similarity(m["text"], t) >= 0.5
            for t in ours
            for m in c["members"]
        )
        if covered:
            continue
        rows.append(
            {
                "text": c["medoid"],
                "source": {
                    "regulation": c["regulation"],
                    "version": versions[c["regulation"]],
                    "page": c["page"],
                    "paragraph": c["members"][0]["paragraph"],
                },
                "confidence": scores.get(k, 0.0),
                "quote": "",
                "pool_votes": c["votes"],
            }
        )
        added += 1
    for r in rows:
        k = key(r["source"]["regulation"], r["source"]["paragraph"])
        r["confidence"] = scores.get(k, r.get("confidence", 0.0))
    return rows, added


def submission(rows: list[dict[str, Any]], team: str = "team-06") -> dict[str, Any]:
    reqs = [
        {**{k: v for k, v in r.items() if k != "pool_votes"}, "id": f"R-{i:04d}"}
        for i, r in enumerate(rows, 1)
    ]
    return {"team_id": team, "case_id": "dev-rear-lamp", "requirements": reqs}


def matched(rows: list[dict[str, Any]], exp: list[dict[str, Any]]) -> int:
    return len(judge.match(rows, exp))


def curve(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    exp = json.loads(EXPECTED.read_text())["requirements"]
    out = []
    prev_rows = prev_m = 0
    for cut in sorted(CUTS, reverse=True):
        sub = [r for r in rows if r["confidence"] >= cut]
        m = matched(sub, exp)
        n = len(sub)
        p, rc = m / max(1, n), m / len(exp)
        d_rows, d_m = n - prev_rows, m - prev_m
        out.append(
            {
                "cut": cut,
                "rows": n,
                "matched": m,
                "f2": round(fbeta(p, rc), 4),
                "bucket_rows": d_rows,
                "bucket_matched": d_m,
                "bucket_p": round(d_m / d_rows, 3) if d_rows else None,
            }
        )
        prev_rows, prev_m = n, m
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mode", choices=["union", "curve", "cut"])
    ap.add_argument("file")
    ap.add_argument("cut", nargs="?", type=float)
    ap.add_argument("-o", "--out")
    args = ap.parse_args(argv)
    data = json.loads(Path(args.file).read_text())
    if args.mode == "union":
        rows, added = union(data)
        sub = submission(rows, data["team_id"])
        problems = validate(sub)
        if problems:
            raise SystemExit("validate.py: " + "; ".join(problems[:10]))
        Path(args.out).write_text(json.dumps(sub, indent=1, ensure_ascii=False))
        print(
            f"{len(data['requirements'])} rows + {added} pool rows = {len(rows)}; wrote {args.out}"
        )
        return 0
    rows = data["requirements"]
    if args.mode == "curve":
        print(
            f"{'cut':>6s} {'rows':>5s} {'match':>6s} {'F2':>6s} {'+rows':>6s} {'+match':>7s} "
            f"{'P(match)':>8s}"
        )
        for c in curve(rows):
            bp = "" if c["bucket_p"] is None else f"{c['bucket_p']:.3f}"
            print(
                f"{c['cut']:6.3f} {c['rows']:5d} {c['matched']:6d} {c['f2']:6.3f} "
                f"{c['bucket_rows']:6d} {c['bucket_matched']:7d} {bp:>8s}"
            )
        return 0
    sub = submission([r for r in rows if r["confidence"] >= args.cut], data["team_id"])
    problems = validate(sub)
    if problems:
        raise SystemExit("validate.py: " + "; ".join(problems[:10]))
    Path(args.out).write_text(json.dumps(sub, indent=1, ensure_ascii=False))
    print(f"cut {args.cut}: {len(sub['requirements'])} rows; wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
