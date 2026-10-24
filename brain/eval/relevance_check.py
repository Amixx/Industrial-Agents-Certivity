"""Does the LLM relevance score add to the decision model? Paragraph-level check on dev.

    uv run --extra llm python -m eval.relevance_check

Scores every candidate paragraph of the gold regulations with the LLM, then compares AUC and the
best paragraph-level F2 for the decision model (leave-one-regulation-out), the LLM alone, and
geometric blends.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import roc_auc_score

from brain.decide import cross_validate, dataset, f2_at
from brain.graph import build
from brain.ingest import load_all
from brain.paths import CASES
from brain.profile import build_profile
from brain.relevance import blend, score


def best_f2(p: np.ndarray, y: np.ndarray) -> tuple[float, float, float, float, int]:
    best = max((f2_at(p, y, t)[2], t) for t in np.arange(0.01, 0.95, 0.01))
    prec, rec, f2 = f2_at(p, y, best[1])
    return f2, prec, rec, float(best[1]), int((p >= best[1]).sum())


def main() -> int:
    case = CASES / "dev-rear-lamp"
    corpus = load_all("base")
    ds = dataset(case, corpus)
    keep = np.array([bool(p.number) for p in ds.paragraphs])
    paragraphs = [p for p, k in zip(ds.paragraphs, keep, strict=True) if k]
    y = ds.y[keep]
    oof = cross_validate(ds)[keep]
    profile = build_profile((case / "spec.md").read_text(), case / "exploded_view.png")
    regs = sorted({p.regulation for p in paragraphs})
    graph = build({r: corpus[r] for r in regs}, set(corpus))
    llm_p = score(paragraphs, graph, profile)
    lp = np.array([llm_p.get(p.id, 0.0) for p in paragraphs])
    print(f"{len(y)} paragraphs, {y.sum()} gold, {len(llm_p)} scored by the LLM")
    rows = [("decision model", oof), ("llm", lp)]
    for w in (0.3, 0.5, 0.7):
        rows.append(
            (f"blend w={w}", np.array([blend(a, b, w) for a, b in zip(oof, lp, strict=True)]))
        )
    for name, p in rows:
        f2, prec, rec, t, n = best_f2(p, y)
        print(
            f"{name:16s} AUC {roc_auc_score(y, p):.3f}  best F2 {f2:.3f} "
            f"(P {prec:.3f} R {rec:.3f} at {t:.2f}, n={n})"
        )
    for w in (0.5, 0.7, 0.85, 1.0):
        b = np.array([blend(a, c, w) for a, c in zip(oof, lp, strict=True)])
        sweep = []
        for t in (0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.5):
            prec, rec, f2 = f2_at(b, y, t)
            sweep.append(f"{t:.2f}:{f2:.2f}/R{rec:.2f}/n{(b >= t).sum()}")
        print(f"  sweep w={w}  " + "  ".join(sweep))
    for reg in regs:
        m = np.array([p.regulation == reg for p in paragraphs])
        print(
            f"  {reg:8s} gold {y[m].sum():3d}/{m.sum():4d}  AUC model "
            f"{roc_auc_score(y[m], oof[m]):.3f}  llm {roc_auc_score(y[m], lp[m]):.3f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
