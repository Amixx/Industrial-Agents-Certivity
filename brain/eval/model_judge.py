"""Requirement-level matching with a model judge, next to the lexical proxy in eval.judge.

    uv run python -m eval.model_judge out/dev-llm.json [--expected ...] [--model claude-opus-5-5]
    uv run python -m eval.model_judge out/dev-llm.json --backend codex [--model gpt-6.1-sol]

For every expected requirement, the candidates are the top TOPK submitted requirements of the same
regulation by lexical similarity, plus those citing the same paragraph. A model, through
`claude -p` (brain.claude_cli) or `codex exec` (brain.codex_cli) on the logged-in subscription,
decides for each pair whether both state the same obligation; the yes pairs are matched one to
one. Verdicts are cached, so a rerun on the same file is free. A pair outside the candidates is
never judged, so the model recall is a lower bound.
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

from brain import claude_cli, codex_cli
from brain.paths import CASES

from . import judge
from .score import fbeta, paragraph_key

TOPK = 4
WORKERS = 5
# Codex carries a large agent prompt on every call, so it gets bigger batches.
BACKENDS = {
    "claude": (claude_cli.complete_json, claude_cli.DEFAULT_MODEL, 25),
    "codex": (codex_cli.complete_json, codex_cli.DEFAULT_MODEL, 100),
}

SYSTEM = """You judge whether two requirement statements state the same obligation: same scope
(what it applies to), same condition and same constraint. Wording, voice and sentence order may
differ. A statement that covers only part of the other, or adds or drops a condition or limit,
is not the same. Answer for every pair, in order."""

SCHEMA = {
    "type": "object",
    "properties": {"same": {"type": "array", "items": {"type": "boolean"}}},
    "required": ["same"],
    "additionalProperties": False,
}

Verdict = tuple[int, int, float, bool]  # submitted index, expected index, lexical sim, same


def candidates(
    sub: list[dict[str, Any]], exp: list[dict[str, Any]]
) -> list[tuple[int, int, float]]:
    pairs: list[tuple[int, int, float]] = []
    for j, e in enumerate(exp):
        reg, para = e["source"]["regulation"], paragraph_key(e["source"].get("paragraph", ""))
        same_reg = [i for i, s in enumerate(sub) if s["source"]["regulation"] == reg]
        sims = {i: judge.similarity(sub[i]["text"], e["text"]) for i in same_reg}
        top = sorted(same_reg, key=lambda i: -sims[i])[:TOPK]
        same_para = [
            i for i in same_reg if paragraph_key(sub[i]["source"].get("paragraph", "")) == para
        ]
        pairs.extend((i, j, sims[i]) for i in dict.fromkeys(top + same_para))
    return pairs


def verdicts(
    sub: list[dict[str, Any]], exp: list[dict[str, Any]], backend: str, model: str
) -> list[Verdict]:
    complete_json, _, size = BACKENDS[backend]
    pairs = candidates(sub, exp)
    batches = [pairs[k : k + size] for k in range(0, len(pairs), size)]

    def ask(batch: list[tuple[int, int, float]]) -> list[Verdict]:
        listing = "\n\n".join(
            f"Pair {n}:\nA: {exp[j]['text']}\nB: {sub[i]['text']}"
            for n, (i, j, _) in enumerate(batch)
        )
        prompt = f"{listing}\n\nReturn exactly {len(batch)} booleans."
        same = complete_json(SYSTEM, prompt, SCHEMA, model)["same"]
        for _ in range(2):
            if len(same) == len(batch):
                break
            prompt += f"\n\nThe previous answer had {len(same)} booleans; give one per pair."
            same = complete_json(SYSTEM, prompt, SCHEMA, model)["same"]
        if len(same) != len(batch):
            raise RuntimeError(f"judge returned {len(same)} verdicts for {len(batch)} pairs")
        return [(i, j, sim, bool(v)) for (i, j, sim), v in zip(batch, same, strict=True)]

    with ThreadPoolExecutor(WORKERS) as pool:
        return [v for out in pool.map(ask, batches) for v in out]


def match(n_sub: int, n_exp: int, judged: list[Verdict]) -> list[tuple[int, int]]:
    """One-to-one matches among the pairs judged the same, preferring higher lexical similarity."""
    m = np.zeros((n_sub, n_exp))
    for i, j, sim, same in judged:
        if same:
            m[i, j] = 1.0 + sim
    rows, cols = linear_sum_assignment(-m)
    return [(int(r), int(c)) for r, c in zip(rows, cols, strict=True) if m[r, c] > 0]


def level(n_matched: int, n_sub: int, n_exp: int) -> dict[str, float]:
    p = n_matched / n_sub if n_sub else 0.0
    r = n_matched / n_exp if n_exp else 0.0
    return {"matched": n_matched, "precision": p, "recall": r, "f2": fbeta(p, r)}


def compare(
    submission: dict[str, Any], expected: dict[str, Any], backend: str, model: str
) -> dict[str, Any]:
    sub, exp = submission["requirements"], expected["requirements"]
    judged = verdicts(sub, exp, backend, model)
    lexical = judge.match(sub, exp)
    model_matches = match(len(sub), len(exp), judged)
    lex_pairs = {(i, j) for i, j, _ in lexical}
    yes_pairs = {(i, j) for i, j, _, same in judged if same}
    return {
        "submitted": len(sub),
        "expected": len(exp),
        "pairs_judged": len(judged),
        "lexical": level(len(lexical), len(sub), len(exp)),
        "model": level(len(model_matches), len(sub), len(exp)),
        "lexical_match_judged_different": len(lex_pairs - yes_pairs),
        "model_match_below_lexical_threshold": sum(
            1 for i, j in model_matches if (i, j) not in lex_pairs
        ),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Model judge next to the lexical judge.")
    ap.add_argument("submissions", nargs="+")
    ap.add_argument("--expected", default=str(CASES / "dev-rear-lamp" / "expected.json"))
    ap.add_argument("--backend", choices=sorted(BACKENDS), default="claude")
    ap.add_argument("--model", help="default: the backend's default model")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    model = args.model or BACKENDS[args.backend][1]
    expected = json.loads(Path(args.expected).read_text())
    print(
        f"{'submission':<28}{'n':>5}  {'lexical P/R/F2':>20}  {'model P/R/F2':>20}"
        f"  {'lex-only':>8}  {'model-only':>10}"
    )
    for path in args.submissions:
        res = compare(json.loads(Path(path).read_text()), expected, args.backend, model)
        if args.json:
            print(json.dumps({"submission": path, "model": model, **res}, indent=1))
            continue
        lx, md = res["lexical"], res["model"]
        print(
            f"{Path(path).name[:27]:<28}{res['submitted']:>5}  "
            f"{lx['precision']:.3f}/{lx['recall']:.3f}/{lx['f2']:.3f}  "
            f"{md['precision']:.3f}/{md['recall']:.3f}/{md['f2']:.3f}  "
            f"{res['lexical_match_judged_different']:>8}  "
            f"{res['model_match_below_lexical_threshold']:>10}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
