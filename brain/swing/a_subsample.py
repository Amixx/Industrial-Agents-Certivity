"""Lane A, step 4: how many runs does the vote need, and how different must they be?

    PYTHONPATH=. uv run python swing/a_subsample.py [--draws 60]

Draws k of the 14 voting runs at random, many times, and votes over them with the clusters of the
full pool (members restricted to the drawn runs). Two cuts per draw: votes >= half of k (the
rule of the nominated file, 7 of 14) and the best cut on the gold (an optimistic ceiling).
Diversity of a draw is the mean pairwise distance between its runs: 1 - Jaccard of the sets of
clusters each run writes into.
"""

from __future__ import annotations

import argparse
import itertools
import math
import random
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import a_sweep as S  # noqa: E402
import a_votes as A  # noqa: E402


def restrict(c: A.Cluster, runs: set[str]) -> A.Cluster:
    return A.Cluster(c.regulation, c.pkey, [m for m in c.members if m.run in runs])


def evaluate(
    clusters: list[A.Cluster],
    runs: list[str],
    src: dict[tuple[str, str], str],
    gold: A.Gold,
    half: bool = True,
) -> dict[str, float]:
    rs = set(runs)
    sub = [restrict(c, rs) for c in clusters]
    sub = [c for c in sub if c.members]
    reps = [S.rep_share_claude(c, src) for c in sub]
    votes = [len(c.runs) for c in sub]
    out: dict[str, float] = {}
    best = (0.0, 0, 0, 0)
    for v in range(1, len(runs) + 1):
        idx = [i for i, n in enumerate(votes) if n >= v]
        m = gold.matched([(sub[i].regulation, reps[i].text) for i in idx])
        f = A.f2(m, len(idx))
        if f > best[0]:
            best = (f, v, len(idx), m)
        if v == math.ceil(len(runs) / 2):
            out.update(half_f2=f, half_rows=len(idx), half_matched=m)
    out.update(best_f2=best[0], best_v=best[1], best_rows=best[2], best_matched=best[3])
    return out


def distance(sets: dict[str, set[int]], a: str, b: str) -> float:
    return 1 - len(sets[a] & sets[b]) / max(1, len(sets[a] | sets[b]))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--draws", type=int, default=60)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args(argv)
    clusters, src, gold = S.setup()
    voters = list(A.VOTERS)
    sets: dict[str, set[int]] = {r: set() for r in voters}
    for k, c in enumerate(clusters):
        for r in c.runs & set(voters):
            sets[r].add(k)
    single = {r: evaluate(clusters, [r], src, gold)["half_f2"] for r in voters}
    print("single runs (local F2):", {r: round(f, 3) for r, f in single.items()})

    print("\npairwise distance between runs (1 - Jaccard of their cluster sets):")
    for r in voters:
        print(f"  {r:<18}" + " ".join(f"{distance(sets, r, o):.2f}" for o in voters))

    rng = random.Random(args.seed)
    print(
        "\nk  draws  half-rule F2 mean [min, max]  rows  | best-cut F2 mean  | best single in "
        "draw | corr(F2, diversity)"
    )
    for k in (2, 3, 4, 6, 8, 10, 12, 14):
        combos = list(itertools.combinations(voters, k))
        draws = combos if len(combos) <= args.draws else rng.sample(combos, args.draws)
        res, div, best_single = [], [], []
        for d in draws:
            res.append(evaluate(clusters, list(d), src, gold))
            div.append(
                statistics.mean(distance(sets, a, b) for a, b in itertools.combinations(d, 2))
            )
            best_single.append(max(single[r] for r in d))
        hf = [r["half_f2"] for r in res]
        bf = [r["best_f2"] for r in res]
        corr = statistics.correlation(div, hf) if len(set(div)) > 1 else float("nan")
        print(
            f"{k:<3}{len(draws):>5}  {statistics.mean(hf):.3f} [{min(hf):.3f}, {max(hf):.3f}]"
            f"  {statistics.mean(r['half_rows'] for r in res):>4.0f}  | {statistics.mean(bf):.3f}"
            f"            | {statistics.mean(best_single):.3f}               | {corr:+.2f}",
            flush=True,
        )

    print("\nnamed sets (half rule / best cut):")
    named = {
        "opus-sonnet family (6: main-cli, main-a39acab, mix x4)": [
            r for r in voters if A.RUNS[r][1] == "opus-sonnet"
        ],
        "one per family (7)": [
            "fable",
            "opus",
            "sonnet",
            "kb-jev",
            "kb-sol-rewrite",
            "main-cli",
            "dev-upload",
        ],
        "Claude models, all steps (3: fable, opus, sonnet)": ["fable", "opus", "sonnet"],
        "cheap Sunday-like (4: sonnet, main-cli, main-a39acab, mix)": [
            "sonnet",
            "main-cli",
            "main-a39acab",
            "mix",
        ],
        "cheap + diverse (4: sonnet, main-cli, dev-upload, qwen)": [
            "sonnet",
            "main-cli",
            "dev-upload",
            "qwen",
        ],
        "all 14": voters,
    }
    for name, runs in named.items():
        r = evaluate(clusters, runs, src, gold)
        dv = statistics.mean(distance(sets, a, b) for a, b in itertools.combinations(runs, 2))
        print(
            f"  {name:<58} half v>={math.ceil(len(runs) / 2)}: {r['half_rows']:.0f} rows "
            f"{r['half_matched']:.0f} matched {r['half_f2']:.3f} | best v>={r['best_v']:.0f}: "
            f"{r['best_rows']:.0f}/{r['best_matched']:.0f} {r['best_f2']:.3f} | diversity {dv:.2f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
