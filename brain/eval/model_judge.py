"""Requirement-level matching with a model judge, calibrated against the platform's dev scores.

    uv run python -m eval.model_judge out/dev-llm.json [more.json ...] [--expected ...]

For every expected requirement, the candidates are the submitted requirements of the same
regulation that are among the TOPK most similar by token overlap, or cite the same paragraph, its
parent or a child. Two passes through `claude -p` (brain.claude_cli) on the logged-in subscription:

1. Grade: one call per expected requirement rates all its candidates 0-4.
2. Check: every pair graded 2 is asked again on its own, as yes or no, in shuffled batches.
   Grading a candidate next to closer ones makes the first pass too strict on these.

A pair matches when it is graded 3 or 4, or graded 2 and checked yes; the matches are one to one.
On the 15 dev uploads the platform scored, this ranks the files in the platform's order (Spearman
0.96) and counts OFFSET more matches than the platform on average, with a spread of 2.5 around
that. The platform itself varies by several matches between two uploads of the same file.
Verdicts are cached per pair, so rescoring a file, or a subset of its rows, is free.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import threading
from collections.abc import Callable
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
GRADE_CHUNK = 80
CHECK_BATCH = 30
WORKERS = 6
OFFSET = 4  # average surplus over the platform's matched count on dev

GRADE_SYSTEM = """You are the judge of a requirements-extraction benchmark. An expert wrote
requirement A from a UN vehicle regulation. A system extracted candidate requirements. A candidate
counts as a match for A when it states the same engineering obligation: same scope (what it
applies to), same condition and same constraint. Wording, voice and sentence order may differ.

Rate every candidate:
4 = the same obligation, paraphrased.
3 = the same obligation with a small difference: a vaguer or more specific subject ("the lamp" vs
    "the stop lamp"), a dropped cross-reference or example, or extra detail that does not change
    what is required.
2 = partly the same: covers only part of A, or merges A with another obligation, or adds or drops
    a condition or limit.
1 = same topic, different obligation.
0 = unrelated."""

GRADE_SCHEMA = {
    "type": "object",
    "properties": {
        "scores": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"n": {"type": "integer"}, "score": {"type": "integer"}},
                "required": ["n", "score"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["scores"],
    "additionalProperties": False,
}

CHECK_SYSTEM = """Each pair has an expected requirement A, written by a regulatory expert, and a
submitted requirement B. B matches A when it states the same engineering obligation (same scope,
condition and constraint). Judge the obligation, not the wording: a different name for the same
subject ("the rear lamp" for "lighting and light-signalling devices"), extra numbers or test
details copied from the same paragraph, or a dropped cross-reference still match. B does not
match when it requires something different, applies to something else, or states a different
condition or limit.
Answer for every pair, in order."""

CHECK_SCHEMA = {
    "type": "object",
    "properties": {"same": {"type": "array", "items": {"type": "boolean"}}},
    "required": ["same"],
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
    """Grades and checks per pair, cached in one JSON file per model."""

    def __init__(self, model: str = MODEL) -> None:
        self.model = model
        self.path = CACHE / "model_judge" / f"{model}.json"
        data = json.loads(self.path.read_text()) if self.path.exists() else {}
        self.grade: dict[str, int] = data.get("grade", {})
        self.check: dict[str, bool] = data.get("check", {})
        self._lock = threading.Lock()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"grade": self.grade, "check": self.check}))

    def _run(self, jobs: list[Any], ask: Callable[[Any], None]) -> None:
        with ThreadPoolExecutor(WORKERS) as pool:
            list(pool.map(ask, jobs))
        self.save()

    def fill(self, pairs: list[tuple[str, str]]) -> None:
        """Grade, then check, every (expected text, submitted text) pair not yet cached."""
        todo: dict[str, dict[str, None]] = {}
        for e, s in pairs:
            if pair_key(e, s) not in self.grade:
                todo.setdefault(e, {})[s] = None
        jobs = [
            (e, texts[k : k + GRADE_CHUNK])
            for e, d in todo.items()
            for texts in [list(d)]
            for k in range(0, len(texts), GRADE_CHUNK)
        ]

        def grade(job: tuple[str, list[str]]) -> None:
            e, texts = job
            listing = "\n".join(f"{n}. {t}" for n, t in enumerate(texts, 1))
            prompt = f"A: {e}\n\nCandidates:\n{listing}\n\nRate all {len(texts)} candidates."
            got: dict[int, int] = {}
            for attempt in range(3):
                out = claude_cli.complete_json(
                    GRADE_SYSTEM, prompt + " " * attempt, GRADE_SCHEMA, self.model
                )
                got = {d["n"]: d["score"] for d in out["scores"]}
                if all(n in got for n in range(1, len(texts) + 1)):
                    break
            else:
                raise RuntimeError(f"judge graded {len(got)} of {len(texts)} candidates")
            with self._lock:
                for n, t in enumerate(texts, 1):
                    self.grade[pair_key(e, t)] = got[n]

        self._run(jobs, grade)

        borderline = [
            (e, s)
            for e, s in dict.fromkeys(pairs)
            if self.grade[pair_key(e, s)] == 2 and pair_key(e, s) not in self.check
        ]
        random.Random(0).shuffle(borderline)
        batches = [borderline[k : k + CHECK_BATCH] for k in range(0, len(borderline), CHECK_BATCH)]

        def check(batch: list[tuple[str, str]]) -> None:
            listing = "\n\n".join(f"Pair {n}:\nA: {e}\nB: {s}" for n, (e, s) in enumerate(batch, 1))
            prompt = f"{listing}\n\nReturn exactly {len(batch)} booleans."
            same: list[bool] = []
            for attempt in range(3):
                same = claude_cli.complete_json(
                    CHECK_SYSTEM, prompt + " " * attempt, CHECK_SCHEMA, self.model
                )["same"]
                if len(same) == len(batch):
                    break
            else:
                raise RuntimeError(f"judge returned {len(same)} verdicts for {len(batch)} pairs")
            with self._lock:
                for (e, s), v in zip(batch, same, strict=True):
                    self.check[pair_key(e, s)] = bool(v)

        self._run(batches, check)

    def same(self, expected_text: str, submitted_text: str) -> tuple[bool, int]:
        k = pair_key(expected_text, submitted_text)
        g = self.grade[k]
        return g >= 3 or (g == 2 and self.check[k]), g


def match(sub: list[dict[str, Any]], exp: list[dict[str, Any]], verdicts: Verdicts) -> list[Pair]:
    """One-to-one matches, judging any pair not yet cached first."""
    pairs = candidates(sub, exp)
    verdicts.fill([(exp[j]["text"], sub[i]["text"]) for i, j in pairs])
    m = np.zeros((len(sub), len(exp)))
    for i, j in pairs:
        ok, g = verdicts.same(exp[j]["text"], sub[i]["text"])
        if ok:
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
        "platform_estimate": level(max(0, n - OFFSET), len(sub), len(exp)),
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
