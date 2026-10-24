"""Requirement-level matching with a model judge, calibrated against the platform's dev scores.

    uv run python -m eval.model_judge out/dev-llm.json [more.json ...] [--expected ...]

For every expected requirement, the candidates are the submitted requirements of the same
regulation that are among the TOPK most similar by token overlap, or cite the same paragraph, its
parent or a child. Sonnet 5.5, through `claude -p` (brain.claude_cli) on the logged-in
subscription, grades every pair 0-4 on its own, in shuffled batches that mix expected
requirements: grading a candidate next to other candidates for the same requirement makes the
grade depend on which other rows the file has. Pairs graded 3 or 4 are matched one to one.

On the 16 dev uploads the platform scored, the platform counts OFFSET more matches on average,
with a spread of 4.9 around that (Spearman 0.84). The platform itself varies by up to 7 matches
between two uploads of the same file, so treat differences under about 8 matches as a tie.
Grades are cached per pair, so rescoring a file, or a subset of its rows, is free.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

from brain import claude_cli
from brain.paths import CACHE, CASES

from . import judge
from .score import fbeta, paragraph_key

MODEL = "claude-sonnet-5-5"
TOPK = 8
BATCH = 40
WORKERS = 6
OFFSET = 4  # average shortfall against the platform's matched count on dev

SYSTEM = """You are the judge of a requirements-extraction benchmark. Each pair has an expected
requirement A, written by a regulatory expert from a UN vehicle regulation, and a submitted
requirement B. B counts as a match for A when it states the same engineering obligation: same
scope (what it applies to), same condition and same constraint. Wording, voice and sentence order
may differ. Judge each pair on its own.

Rate every pair:
4 = the same obligation, paraphrased.
3 = the same obligation with a small difference: a vaguer or more specific subject ("the lamp" vs
    "the stop lamp"), a dropped cross-reference or example, or extra detail that does not change
    what is required.
2 = partly the same: covers only part of A, or merges A with another obligation, or adds or drops
    a condition or limit.
1 = same topic, different obligation.
0 = unrelated."""

SCHEMA = {
    "type": "object",
    "properties": {"scores": {"type": "array", "items": {"type": "integer"}}},
    "required": ["scores"],
    "additionalProperties": False,
}

Pair = tuple[int, int]  # submitted index, expected index


def pair_key(expected_text: str, submitted_text: str) -> str:
    return hashlib.sha1(f"{expected_text}\0{submitted_text}".encode()).hexdigest()


def _related(a: str, b: str) -> bool:
    return a == b or a.startswith(b + ".") or b.startswith(a + ".")


def candidates(sub: list[dict[str, Any]], exp: list[dict[str, Any]]) -> list[Pair]:
    pairs: list[Pair] = []
    for j, e in enumerate(exp):
        reg, para = e["source"]["regulation"], paragraph_key(e["source"].get("paragraph", ""))
        same_reg = [i for i, s in enumerate(sub) if s["source"]["regulation"] == reg]
        top = sorted(same_reg, key=lambda i: -judge.similarity(sub[i]["text"], e["text"]))[:TOPK]
        near = [
            i
            for i in same_reg
            if _related(paragraph_key(sub[i]["source"].get("paragraph", "")), para)
        ]
        pairs.extend((i, j) for i in dict.fromkeys(top + near))
    return pairs


class Verdicts:
    """Grades per pair, cached in one JSON file per model."""

    def __init__(self, model: str = MODEL) -> None:
        self.model = model
        self.path = CACHE / "model_judge" / f"{model}.json"
        self.grade: dict[str, int] = json.loads(self.path.read_text()) if self.path.exists() else {}
        self._lock = threading.Lock()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.grade))

    def fill(self, pairs: list[tuple[str, str]]) -> None:
        """Grade every (expected text, submitted text) pair not yet cached."""
        todo = [p for p in dict.fromkeys(pairs) if pair_key(*p) not in self.grade]
        random.Random(0).shuffle(todo)
        batches = [todo[k : k + BATCH] for k in range(0, len(todo), BATCH)]

        def ask(batch: list[tuple[str, str]]) -> None:
            listing = "\n\n".join(f"Pair {n}:\nA: {e}\nB: {s}" for n, (e, s) in enumerate(batch, 1))
            prompt = f"{listing}\n\nReturn exactly {len(batch)} scores, one per pair, in order."
            scores: list[int] = []
            for attempt in range(3):
                scores = claude_cli.complete_json(
                    SYSTEM, prompt + " " * attempt, SCHEMA, self.model
                )["scores"]
                if len(scores) == len(batch):
                    break
            else:
                raise RuntimeError(f"judge returned {len(scores)} scores for {len(batch)} pairs")
            with self._lock:
                for p, g in zip(batch, scores, strict=True):
                    self.grade[pair_key(*p)] = int(g)

        with ThreadPoolExecutor(WORKERS) as pool:
            list(pool.map(ask, batches))
        self.save()


def match(sub: list[dict[str, Any]], exp: list[dict[str, Any]], verdicts: Verdicts) -> list[Pair]:
    """One-to-one matches among pairs graded 3 or 4, grading any pair not yet cached first."""
    pairs = candidates(sub, exp)
    verdicts.fill([(exp[j]["text"], sub[i]["text"]) for i, j in pairs])
    m = np.zeros((len(sub), len(exp)))
    for i, j in pairs:
        g = verdicts.grade[pair_key(exp[j]["text"], sub[i]["text"])]
        if g >= 3:
            m[i, j] = 1.0 + g / 10
    rows, cols = linear_sum_assignment(-m)
    return [(int(r), int(c)) for r, c in zip(rows, cols, strict=True) if m[r, c] > 0]


def level(n_matched: float, n_sub: int, n_exp: int) -> dict[str, float]:
    p = n_matched / n_sub if n_sub else 0.0
    r = n_matched / n_exp if n_exp else 0.0
    return {"matched": n_matched, "precision": p, "recall": r, "f2": fbeta(p, r)}


def compare(
    submission: dict[str, Any], expected: dict[str, Any], verdicts: Verdicts
) -> dict[str, Any]:
    sub, exp = submission["requirements"], expected["requirements"]
    n = len(match(sub, exp, verdicts))
    return {
        "submitted": len(sub),
        "expected": len(exp),
        "lexical": level(len(judge.match(sub, exp)), len(sub), len(exp)),
        "model": level(n, len(sub), len(exp)),
        "platform_estimate": level(min(len(exp), n + OFFSET), len(sub), len(exp)),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Calibrated model judge next to the lexical judge.")
    ap.add_argument("submissions", nargs="+")
    ap.add_argument("--expected", default=str(CASES / "dev-rear-lamp" / "expected.json"))
    ap.add_argument("--model", default=MODEL, help="the calibration holds for the default only")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    expected = json.loads(Path(args.expected).read_text())
    verdicts = Verdicts(args.model)
    if not args.json:
        print(
            f"{'submission':<34}{'n':>5}  {'lexical m/F2':>12}  {'model m/F2':>12}"
            f"  {'platform est. m/F2':>18}"
        )
    for path in args.submissions:
        res = compare(json.loads(Path(path).read_text()), expected, verdicts)
        if args.json:
            print(json.dumps({"submission": path, "model": args.model, **res}, indent=1))
            continue
        lx, md, pe = res["lexical"], res["model"], res["platform_estimate"]
        print(
            f"{Path(path).name[:33]:<34}{res['submitted']:>5}  "
            f"{lx['matched']:>5.0f} {lx['f2']:.3f}  {md['matched']:>5.0f} {md['f2']:.3f}  "
            f"{pe['matched']:>11.0f} {pe['f2']:.3f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
