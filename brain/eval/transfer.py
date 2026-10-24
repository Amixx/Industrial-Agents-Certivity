"""Does the decision model transfer? Fitted on the dev lamp, scored on the silver bumper labels.

    uv run python -m eval.transfer

Prints the leave-one-regulation-out AUC on dev, then AUC, best F2 and F2 at the saved cut-off on
the labelled bumper paragraphs (data/bumper-labels/, plain bumper spec), per regulation too. Run
it before and after any change to brain/features.py: a change has to help dev without hurting
the bumper. No LLM calls.
"""

from __future__ import annotations

import csv
import json

import numpy as np
from sklearn.metrics import roc_auc_score

from brain import features as F
from brain.decide import MODEL_PATH, cross_validate, dataset, f2_at, fit
from brain.graph import build
from brain.ingest import load_all
from brain.paths import CASES, DATA
from brain.profile import parse_spec
from brain.select_regs import choose

LABELS = DATA / "bumper-labels"
SPEC = DATA / "synthetic" / "bumper-plain" / "spec.md"
REGS = ["UN R42", "UN R26", "UN R127", "UN GTR 9"]


def labels() -> dict[tuple[str, str], bool]:
    out = {}
    for name in ("labels-r42-r26.csv", "labels-r127-gtr9.csv"):
        with (LABELS / name).open() as f:
            for r in csv.DictReader(f):
                if r["cited"] in ("y", "n"):
                    out[(r["regulation"], r["paragraph"])] = r["cited"] == "y"
    return out


def main() -> int:
    corpus = load_all("base")
    ds = dataset(CASES / "dev-rear-lamp", corpus)
    numbered = np.array([bool(p.number) for p in ds.paragraphs])
    oof = cross_validate(ds)
    print(f"dev leave-one-regulation-out AUC {roc_auc_score(ds.y[numbered], oof[numbered]):.3f}")
    model = fit(ds.X, ds.y, threshold=json.loads(MODEL_PATH.read_text())["threshold"])

    gold = labels()
    profile = parse_spec(SPEC.read_text())
    sub = {r: corpus[r] for r in REGS}
    graph = build(sub, set(corpus))
    reg_prob = {c.regulation: c.probability for c in choose(profile, corpus, use_llm=False)}
    ctx = F.build_context(profile, sub, graph, reg_prob)
    ps = [p for r in REGS for p in sub[r] if p.number and (p.regulation, p.label) in gold]
    y = np.array([gold[(p.regulation, p.label)] for p in ps], dtype=int)
    prob = model.predict(F.matrix(ps, ctx))
    best = max(f2_at(prob, y, t)[2] for t in np.arange(0.01, 0.9, 0.005))
    precision, recall, f2 = f2_at(prob, y, model.threshold)
    print(
        f"bumper: {len(y)} labelled paragraphs, {y.sum()} cited; AUC {roc_auc_score(y, prob):.3f};"
        f" best F2 {best:.3f}; at cut-off {model.threshold}: P {precision:.2f} R {recall:.2f} "
        f"F2 {f2:.3f}, {(prob >= model.threshold).sum()} selected"
    )
    for reg in REGS:
        m = np.array([p.regulation == reg for p in ps])
        print(
            f"   {reg:9s} cited {y[m].sum():2d} of {m.sum():3d}, AUC "
            f"{roc_auc_score(y[m], prob[m]):.3f}, selected {(prob[m] >= model.threshold).sum()}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
