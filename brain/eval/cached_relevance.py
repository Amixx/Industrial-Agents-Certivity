"""Score the LLM relevance answers already in the cache against the dev gold, mid-run.

    uv run python -m eval.cached_relevance --since "2026-10-24 19:00"

The cache does not record which model answered, so `--since` picks the answers written after a
run started. Compares AUC with the decision model (out of fold) on the same paragraphs, per
regulation, and shows what each LLM cut-off would keep.
"""

from __future__ import annotations

import argparse
import json
import time

import numpy as np
from sklearn.metrics import roc_auc_score

from brain.decide import cross_validate, dataset
from brain.ingest import load_all
from brain.paths import CACHE, CASES


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--since", required=True, help="local time, 'YYYY-MM-DD HH:MM'")
    args = ap.parse_args(argv)
    since = time.mktime(time.strptime(args.since, "%Y-%m-%d %H:%M"))
    llm: dict[str, float] = {}
    for f in (CACHE / "llm").glob("*.json"):
        if f.stat().st_mtime >= since:
            for r in json.loads(f.read_text()).get("paragraphs", []):
                llm[r["id"]] = float(r["p_cited"])
    ds = dataset(CASES / "dev-rear-lamp", load_all("base"))
    oof = cross_validate(ds)
    idx = [i for i, p in enumerate(ds.paragraphs) if p.id in llm]
    if not idx:
        print("no cached relevance answers for dev paragraphs since then")
        return 1
    y = ds.y[idx]
    q = np.array([llm[ds.paragraphs[i].id] for i in idx])
    m = oof[idx]
    regs = np.array([ds.paragraphs[i].regulation for i in idx])
    print(f"{len(idx)} paragraphs scored, {int(y.sum())} in gold")
    print(f"{'':10s} {'n':>5s} {'gold':>5s} {'AUC llm':>8s} {'AUC model':>10s}")
    for reg in ["all", *sorted(set(regs))]:
        s = np.ones(len(idx), bool) if reg == "all" else regs == reg
        if 0 < y[s].sum() < s.sum():
            auc_q, auc_m = roc_auc_score(y[s], q[s]), roc_auc_score(y[s], m[s])
            print(f"{reg:10s} {s.sum():5d} {int(y[s].sum()):5d} {auc_q:8.3f} {auc_m:10.3f}")
    for t in (0.1, 0.2, 0.3, 0.5):
        k = q >= t
        tp = int((k & (y == 1)).sum())
        print(
            f"llm p >= {t}: keeps {int(k.sum())}, recall {tp / y.sum():.2f}, "
            f"precision {tp / max(1, int(k.sum())):.2f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
