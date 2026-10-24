"""Lane F, steps 3 and 4: a logistic row selector, fitted leaving one regulation out.

    PYTHONPATH=. uv run python swing/f_fit.py [--set NAME] [--write VARIANT]

For each feature set: out-of-fold P(match) per cluster (fitted on the other three regulations),
AUC per regulation, the cut that maximises expected F2 (keep rows in order of P while
5 * sum(P) / (760 + rows) rises, which is the same as keeping rows above F2 / 5), and the local
judge's score of the rows kept. `--write VARIANT` saves the kept rows of `--set` as
../out/rear-lamp-swing-F-VARIANT.json.

Votes and the keep probability enter as log(votes) and logit(clip(p_keep, 0.02, 0.98)).
`logit_keep` is the Opus answer (`p_keep_strong`); `logit_keep_bulk` is Sonnet (`p_keep_bulk`).
"""

from __future__ import annotations

import argparse
import json
import math
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

from brain.paths import CASES
from eval import judge
from eval.score import fbeta
from swing.f_pool import OUT, POOL_PATH

N_GOLD = 190
VOTES = ["votes", "row_share", "para_votes", "para_rows", "vote_rank"]
TEXT = [
    "word_share",
    "log_tokens",
    "n_numbers",
    "cites_other",
    "shall_not",
    "may",
    "no_modal",
    "position",
    "depth",
    "annex",
]
# Log-scale sets. Raw votes and p_keep multiply; a linear model needs the logs.
# `logit_keep` is Opus, `logit_keep_bulk` is Sonnet.
_KEEP_SHARE = ["log_votes", "logit_keep", "word_share"]
_SONNET_SHARE = ["log_votes", "logit_keep_bulk", "word_share"]
SETS = {
    "votes only": ["votes"],
    "votes + relevance": ["votes", "llm_p"],
    "full": VOTES + ["llm_p", "p_keep_strong"] + TEXT,
    "full without keep": VOTES + ["llm_p"] + TEXT,
    "one run (no votes)": ["llm_p", "p_keep_strong"] + TEXT,
    "one run without keep": ["llm_p"] + TEXT,
    "votes alone (log)": ["log_votes"],
    "log votes + logit keep": ["log_votes", "logit_keep"],
    "log votes + logit keep + word share": _KEEP_SHARE,
    "keep + share + depth": _KEEP_SHARE + ["depth"],
    "keep + share + depth + rel": _KEEP_SHARE + ["depth", "llm_p"],
    "one run: keep + share + rel": ["logit_keep", "word_share", "llm_p"],
    "sonnet: log votes + logit keep": ["log_votes", "logit_keep_bulk"],
    "sonnet: keep + word share": _SONNET_SHARE,
    "sonnet: keep + share + depth": _SONNET_SHARE + ["depth"],
    "sonnet: keep + share + depth + rel": _SONNET_SHARE + ["depth", "llm_p"],
    "one run sonnet: keep + share + rel": ["logit_keep_bulk", "word_share", "llm_p"],
}


def _logit(p: float) -> float:
    p = min(0.98, max(0.02, p))
    return math.log(p / (1.0 - p))


def matrix(cs: list[dict[str, Any]], names: list[str]) -> np.ndarray:
    rows = []
    for c in cs:
        f = dict(c["f"])
        f["log_tokens"] = math.log1p(f["n_tokens"])
        f["log_votes"] = math.log(float(f["votes"]))
        f["logit_keep"] = _logit(float(f["p_keep_strong"]))
        f["logit_keep_bulk"] = _logit(float(f["p_keep_bulk"]))
        rows.append([float(f[n]) for n in names])
    return np.array(rows)


def oof(cs: list[dict[str, Any]], names: list[str]) -> tuple[np.ndarray, dict[str, Any]]:
    """Out-of-fold probabilities, one regulation held out at a time, and the all-data weights."""
    x, y = matrix(cs, names), np.array([c["y"] for c in cs])
    regs = np.array([c["regulation"] for c in cs])
    p = np.zeros(len(cs))
    for reg in sorted(set(regs)):
        tr = regs != reg
        sc = StandardScaler().fit(x[tr])
        m = LogisticRegression(C=1.0, max_iter=2000).fit(sc.transform(x[tr]), y[tr])
        p[~tr] = m.predict_proba(sc.transform(x[~tr]))[:, 1]
    sc = StandardScaler().fit(x)
    m = LogisticRegression(C=1.0, max_iter=2000).fit(sc.transform(x), y)
    return p, dict(zip(names, map(float, m.coef_[0]), strict=True))


def _auc(y_true: np.ndarray, scores: np.ndarray) -> str:
    """One regulation can have no assigned gold row (R26 in this pool); AUC is then undefined."""
    if len(set(y_true.tolist())) < 2:
        return "  n/a"
    return f"{roc_auc_score(y_true, scores):5.3f}"


def best_cut(p: np.ndarray) -> tuple[np.ndarray, float, float]:
    """Indices kept, expected matched and expected F2 at the size that maximises 5 m / (760 + n)."""
    order = np.argsort(-p)
    cum = np.cumsum(p[order])
    n = np.arange(1, len(p) + 1)
    f2 = 5 * cum / (4 * N_GOLD + n)
    k = int(np.argmax(f2)) + 1
    return order[:k], float(cum[k - 1]), float(f2[k - 1])


def local(cs: list[dict[str, Any]], keep: np.ndarray) -> tuple[int, float]:
    gold = json.loads((CASES / "dev-rear-lamp" / "expected.json").read_text())["requirements"]
    sub = [{"text": cs[i]["text"], "source": {"regulation": cs[i]["regulation"]}} for i in keep]
    m = len(judge.match(sub, gold))
    return m, fbeta(m / max(1, len(sub)), m / N_GOLD)


def _contrast(
    cs: list[dict[str, Any]],
    results: dict[str, tuple[np.ndarray, dict[str, float]]],
    left: str,
    right: str,
) -> None:
    """How the two cuts differ, so a word-share gain can be read against finding 4."""
    a = set(int(i) for i in best_cut(results[left][0])[0])
    b = set(int(i) for i in best_cut(results[right][0])[0])

    def stats(idxs: set[int]) -> str:
        if not idxs:
            return "none"
        labelled = sum(cs[i]["y"] for i in idxs)
        share = sum(cs[i]["f"]["word_share"] for i in idxs) / len(idxs)
        return f"{len(idxs)} rows, {labelled} labelled, mean word share {share:.2f}"

    print(f"\n{right} only: {stats(b - a)}")
    print(f"{left} only: {stats(a - b)}")


def submission(cs: list[dict[str, Any]], keep: np.ndarray, p: np.ndarray) -> dict[str, Any]:
    base = json.loads((OUT / "rear-lamp-main-a39acab.json").read_text())
    order = sorted(keep, key=lambda i: (cs[i]["regulation"], cs[i]["pkey"]))
    reqs = [
        {
            "id": f"R-{n:04d}",
            "text": cs[i]["text"],
            "source": {
                "regulation": cs[i]["regulation"],
                "version": cs[i]["version"],
                "page": cs[i]["page"],
                "paragraph": cs[i]["paragraph"],
            },
            "confidence": round(float(p[i]), 3),
            "quote": cs[i]["quote"][:1000],
        }
        for n, i in enumerate(order, start=1)
    ]
    return {
        "team_id": "team-06",
        "case_id": "dev-rear-lamp",
        "requirements": reqs,
        "regulations": base["regulations"],
        "profile": base["profile"],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", help="save --set's kept rows as rear-lamp-swing-F-NAME.json")
    ap.add_argument("--set", default="full", choices=list(SETS))
    args = ap.parse_args(argv)
    cs = json.loads(POOL_PATH.read_text())["clusters"]
    y = np.array([c["y"] for c in cs])
    regs = np.array([c["regulation"] for c in cs])
    print(f"{len(cs)} clusters, {int(y.sum())} labelled matches")
    width = max(len(name) for name in SETS)
    reg_names = sorted(set(regs))
    head = f"{'features':{width}s} {'AUC':>5s} " + " ".join(f"{r[3:]:>5s}" for r in reg_names)
    print(head + "   rows  exp.m  exp.F2  local m  local F2")
    results = {}
    for name, names in SETS.items():
        p, w = oof(cs, names)
        results[name] = (p, w)
        aucs = [_auc(y[regs == r], p[regs == r]) for r in reg_names]
        keep, em, ef = best_cut(p)
        m, lf = local(cs, keep)
        print(
            f"{name:{width}s} {roc_auc_score(y, p):5.3f} "
            + " ".join(aucs)
            + f"  {len(keep):5d}  {em:5.1f}  {ef:6.3f}  {m:7d}  {lf:8.3f}"
        )
    print("\nweights (standardised, fitted on all four regulations):")
    for name, (_, w) in results.items():
        order = sorted(w.items(), key=lambda kv: -abs(kv[1]))
        parts = ", ".join(f"{k} {v:+.2f}" for k, v in order)
        print(f"  {name}: {parts}")
    _contrast(
        cs,
        results,
        "log votes + logit keep",
        "log votes + logit keep + word share",
    )
    _contrast(
        cs,
        results,
        "log votes + logit keep",
        "sonnet: log votes + logit keep",
    )
    if args.write:
        p = results[args.set][0]
        keep, em, ef = best_cut(p)
        path = OUT / f"rear-lamp-swing-F-{args.write}.json"
        path.write_text(json.dumps(submission(cs, keep, p), indent=1, ensure_ascii=False))
        print(f"\nwrote {path.name}: {len(keep)} rows, expected {em:.1f} matched, F2 {ef:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
