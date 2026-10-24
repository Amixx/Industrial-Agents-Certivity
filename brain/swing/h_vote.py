"""Vote the three lane H runs. No model call.

Clusters rows the way lane A built votes7 (token Jaccard 0.5, two rows of one run never
share a cluster). Keeps a cluster at 2 of 3 and at 3 of 3. The representative is run 2's
row when that run is in the cluster, otherwise the medoid.

    PYTHONPATH=. uv run python swing/h_vote.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import swing.a_votes as A
from eval.score import paragraph_key

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out"
RUNS = {
    "run1": OUT / "rear-lamp-main-a39acab.json",
    "run2": OUT / "rear-lamp-swing-H-sonnet-w85.json",
    "run3": OUT / "rear-lamp-swing-H-haiku-rel.json",
}
ORDER = ["run2", "run1", "run3"]


def load() -> list[A.Row]:
    rows: list[A.Row] = []
    for run, path in RUNS.items():
        data = json.loads(path.read_text())
        for i, r in enumerate(data["requirements"]):
            s = r["source"]
            rows.append(
                A.Row(
                    run,
                    i,
                    r["text"],
                    s["regulation"],
                    str(s.get("paragraph") or ""),
                    paragraph_key(s.get("paragraph")) or "",
                    int(s.get("page") or 0),
                    s.get("version", ""),
                    r.get("quote") or "",
                    r.get("confidence"),
                    frozenset(A.judge.tokens(r["text"])),
                    A.value_numbers(r["text"]),
                )
            )
    return rows


def representative(c: A.Cluster) -> A.Row:
    for run in ORDER:
        for m in c.members:
            if m.run == run:
                return m
    return A.rep_medoid(c, {})


def write(min_votes: int, clusters: list[A.Cluster]) -> Path:
    keep = [c for c in clusters if len(c.runs) >= min_votes]
    files = {run: json.loads(path.read_text()) for run, path in RUNS.items()}
    reqs = []
    for k, c in enumerate(keep, start=1):
        r = representative(c)
        rec = dict(files[r.run]["requirements"][r.idx])
        rec = {key: rec[key] for key in ("text", "source", "confidence", "quote") if key in rec}
        reqs.append({"id": f"R-{k:04d}", **rec})
    base = files["run2"]
    doc = {
        "team_id": "team-06",
        "case_id": "dev-rear-lamp",
        "requirements": reqs,
        "regulations": base.get("regulations", []),
        "profile": base.get("profile", {}),
        "vote": {
            "runs": list(RUNS),
            "min": min_votes,
            "of": len(RUNS),
            "representative": "run2, else run1, else run3",
            "cluster": "jaccard 0.5, same as lane A votes7",
        },
    }
    path = OUT / f"rear-lamp-swing-H-vote{min_votes}.json"
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    by = defaultdict(int)
    for c in keep:
        by[representative(c).run] += 1
    lines = [
        f"lane H vote >= {min_votes} of {len(RUNS)}, jaccard 0.5, representative run 2",
        f"clusters kept {len(keep)}, rows {len(reqs)}",
        f"representatives by run: {dict(by)}",
        "historical 14 files are not in this vote",
        "spend: $0 (no model call)",
    ]
    path.with_suffix(".log").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return path


def main() -> int:
    missing = [str(p) for p in RUNS.values() if not p.exists()]
    if missing:
        print("missing: " + ", ".join(missing))
        return 1
    clusters = A.build(load(), A.Setting(0.5, False))
    for n in (2, 3):
        write(n, clusters)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
