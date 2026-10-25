"""Decision model: P(paragraph contributes a gold requirement), fitted on labelled cases.

    uv run python -m brain.decide            # fit on the dev case, report leave-one-regulation-out
                                             # CV, save brain/data/decision_model.json

Logistic regression on generic features (brain.features); TabPFN is used instead when installed
(`uv sync --extra tabpfn`) and BRAIN_DECIDER=tabpfn. The F2-optimal rule includes a paragraph when
P > F2*/(1+4) for the F2* we expect; `threshold` defaults to the value tuned in CV.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import features as F
from .graph import build
from .ingest import load_all
from .models import Paragraph
from .paths import CASES, DATA
from .profile import parse_spec
from .select_regs import choose

MODEL_PATH = DATA / "decision_model.json"


def paragraph_key(label: str) -> str:
    text = str(label or "").casefold()
    text = re.sub(r"\s*table.*$", "", text)
    text = re.sub(r"[,;:()\[\]]", " ", text)
    text = re.sub(r"(?<![0-9a-z])\.|\.(?![0-9a-z])", " ", text)
    return " ".join(text.split())


@dataclass
class Dataset:
    paragraphs: list[Paragraph]
    X: np.ndarray
    y: np.ndarray


def gold_keys(expected: dict) -> set[tuple[str, str]]:
    return {
        (r["source"]["regulation"], paragraph_key(r["source"].get("paragraph", "")))
        for r in expected["requirements"]
    }


def candidates(corpus: dict[str, list[Paragraph]], regulations: list[str]) -> list[Paragraph]:
    return [p for reg in regulations for p in corpus[reg] if p.label != "preamble"]


def dataset(
    case: Path,
    corpus: dict[str, list[Paragraph]] | None = None,
    regulations: list[str] | None = None,
) -> Dataset:
    corpus = corpus or load_all("base")
    expected = json.loads((case / "expected.json").read_text())
    profile = parse_spec((case / "spec.md").read_text())
    choices = choose(profile, corpus, use_llm=False)
    reg_prob = {c.regulation: c.probability for c in choices}
    regs = regulations or sorted({r["source"]["regulation"] for r in expected["requirements"]})
    graph = build({r: corpus[r] for r in regs}, set(corpus))
    ctx = F.build_context(profile, {r: corpus[r] for r in regs}, graph, reg_prob)
    ps = candidates(corpus, regs)
    keys = gold_keys(expected)
    y = np.array([(p.regulation, paragraph_key(p.label)) in keys for p in ps], dtype=int)
    return Dataset(ps, F.matrix(ps, ctx), y)


class Model:
    def __init__(self, coef: np.ndarray, intercept: float, threshold: float) -> None:
        self.coef, self.intercept, self.threshold = coef, intercept, threshold

    def predict(self, X: np.ndarray) -> np.ndarray:
        z = X @ self.coef + self.intercept
        out: np.ndarray = 1 / (1 + np.exp(-z))
        return out

    def save(self, path: Path = MODEL_PATH) -> None:
        path.write_text(
            json.dumps(
                {
                    "features": F.FEATURES,
                    "coef": self.coef.tolist(),
                    "intercept": self.intercept,
                    "threshold": self.threshold,
                },
                indent=1,
            )
        )

    @classmethod
    def load(cls, path: Path = MODEL_PATH) -> Model:
        d = json.loads(path.read_text())
        if d["features"] != F.FEATURES:
            raise ValueError("decision model was fitted on other features; rerun brain.decide")
        return cls(np.array(d["coef"]), float(d["intercept"]), float(d["threshold"]))


def fit(X: np.ndarray, y: np.ndarray, threshold: float = 0.15) -> Model:
    from sklearn.linear_model import LogisticRegression

    lr = LogisticRegression(C=0.01, class_weight="balanced", max_iter=3000)
    lr.fit(X, y)
    # class_weight="balanced" inflates P; recalibrate the intercept to the base rate.
    model = Model(lr.coef_[0], float(lr.intercept_[0]), threshold)
    for _ in range(50):
        gap = model.predict(X).mean() - y.mean()
        if abs(gap) < 1e-4:
            break
        model.intercept -= gap * 4
    return model


def predict_tabpfn(X_train: np.ndarray, y_train: np.ndarray, X: np.ndarray) -> np.ndarray:
    from tabpfn import TabPFNClassifier  # optional dependency

    clf = TabPFNClassifier()
    clf.fit(X_train, y_train)
    proba: np.ndarray = clf.predict_proba(X)[:, 1]
    return proba


def f2_at(p: np.ndarray, y: np.ndarray, threshold: float) -> tuple[float, float, float]:
    chosen = p >= threshold
    tp = int((chosen & (y == 1)).sum())
    precision = tp / max(1, int(chosen.sum()))
    recall = tp / max(1, int(y.sum()))
    f2 = 0.0 if tp == 0 else 5 * precision * recall / (4 * precision + recall)
    return precision, recall, f2


def cross_validate(ds: Dataset) -> np.ndarray:
    """Leave-one-regulation-out out-of-fold probabilities."""
    regs = np.array([p.regulation for p in ds.paragraphs])
    oof = np.zeros(len(ds.y))
    for reg in sorted(set(regs)):
        test = regs == reg
        if os.environ.get("BRAIN_DECIDER") == "tabpfn":
            oof[test] = predict_tabpfn(ds.X[~test], ds.y[~test], ds.X[test])
        else:
            oof[test] = fit(ds.X[~test], ds.y[~test]).predict(ds.X[test])
    return oof


def main() -> int:
    from sklearn.metrics import roc_auc_score

    ds = dataset(CASES / "dev-rear-lamp")
    print(f"{len(ds.y)} candidate paragraphs, {ds.y.sum()} gold")
    oof = cross_validate(ds)
    print(f"leave-one-regulation-out AUC {roc_auc_score(ds.y, oof):.3f}")
    best = max((f2_at(oof, ds.y, t)[2], t) for t in np.arange(0.02, 0.6, 0.01))
    for t in (0.05, 0.1, 0.15, 0.2, 0.3, best[1]):
        prec, rec, f2 = f2_at(oof, ds.y, t)
        print(f"  threshold {t:.2f}: P {prec:.3f} R {rec:.3f} F2 {f2:.3f} n={(oof >= t).sum()}")
    model = fit(ds.X, ds.y, threshold=round(float(best[1]), 2))
    model.save()
    print("saved", MODEL_PATH, "threshold", model.threshold)
    for name, c in sorted(zip(F.FEATURES, model.coef, strict=True), key=lambda x: -abs(x[1])):
        print(f"  {name:16s} {c:+.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
