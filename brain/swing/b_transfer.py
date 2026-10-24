"""Lane B transfer check: paragraph recall and size against the blend cut on the bumper silver
labels (`data/bumper-labels`), with cached relevance only.

    B_CASE=data/synthetic/bumper-plain PYTHONPATH=. uv run python swing/b_transfer.py

Cache only by default; B_MODE=run makes the missing Opus calls (profile, regulations, relevance).
"""

from __future__ import annotations

import csv
import os
import sys

from brain import llm
from brain.paths import PROJECT
from swing import b_recall

CUTS = [0.5, 0.3, 0.25, 0.2, 0.175, 0.15, 0.1, 0.07, 0.05, 0.03]


def labels() -> dict[tuple[str, str], bool]:
    out = {}
    for name in ("labels-r42-r26.csv", "labels-r127-gtr9.csv"):
        with open(PROJECT / "data" / "bumper-labels" / name) as f:
            for r in csv.DictReader(f):
                out[(r["regulation"], r["paragraph"])] = r["cited"] == "y"
    return out


def main() -> int:
    os.environ["BRAIN_LLM"] = "anthropic"
    llm.complete_json = b_recall.guarded(os.environ.get("B_MODE", "rank"))
    b_recall._track_usage()
    rows, keep, _, _ = b_recall.scored_paragraphs()
    lab = labels()
    regs = sorted({p.regulation for p, *_ in rows})
    gold = {k for k, v in lab.items() if v and k[0] in regs and not k[1].startswith("(")}
    print(
        f"case {b_recall.CASE}; regulations {regs}; {len(rows)} candidates; "
        f"{len(gold)} silver-cited paragraphs in them; pipeline keeps {len(keep)}"
    )
    print(f"{'cut':>6s} {'paras':>6s} {'cited':>6s} {'recall':>7s} {'precision':>9s}")
    for cut in CUTS:
        sel = {(p.regulation, p.label) for p, b, *_ in rows if b >= cut}
        hit = len(sel & gold)
        print(
            f"{cut:6.3f} {len(sel):6d} {hit:6d} {hit / max(1, len(gold)):7.2f} "
            f"{hit / max(1, len(sel)):9.2f}"
        )
    sel = {(p.regulation, p.label) for p, *_ in rows if p.id in keep}
    hit = len(sel & gold)
    print(f"pipeline (0.20 + floor): {len(sel)} paragraphs, recall {hit / max(1, len(gold)):.2f}")
    print(dict(b_recall.stats), file=sys.stderr)
    b_recall.spend()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
