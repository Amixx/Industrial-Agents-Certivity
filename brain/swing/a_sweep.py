"""Lane A, steps 2 and 3: vote thresholds, weighted votes and representative text.

    PYTHONPATH=. uv run python swing/a_sweep.py weights      # A2: rankings of the clusters
    PYTHONPATH=. uv run python swing/a_sweep.py reps         # A3: which row stands for a cluster

Every ranking orders the 949 clusters of the pool; a file is a prefix of that order. Matched is
the local judge (eval.judge). "Platform est." scales each matched row by its source run's
platform / local ratio (table RATIO), the only calibration we have for writing style.
"""

from __future__ import annotations

import argparse
import collections
import statistics
import sys
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import a_votes as A  # noqa: E402

# Platform matched / local matched per run (out/README.md and a_votes' local scores, 24 Oct).
# Runs never uploaded take their family's uploaded mean: Opus relevance + Sonnet rewrite runs
# (main-cli 143/145, mix-examples-cut 138/145).
LOCAL = {
    "fable": 141,
    "opus": 139,
    "sonnet": 131,
    "kb-jev": 153,
    "kb-jev-filter-v4": 158,
    "kb-sol-rewrite": 150,
    "main-cli": 145,
    "mix-examples-cut": 145,
    "dev-upload": 138,
    "qwen": 137,
}
RATIO = {r: A.RUNS[r][2] / LOCAL[r] for r in LOCAL}  # type: ignore[operator]
_FAMILY_RATIO = (143 + 138) / (145 + 145)
for _r in A.RUNS:
    RATIO.setdefault(_r, _FAMILY_RATIO)

Rank = Callable[[A.Cluster], float]


def weights_uniform(voters: list[str]) -> dict[str, float]:
    return {r: 1.0 for r in voters}


def weights_family(voters: list[str]) -> dict[str, float]:
    fam = collections.Counter(A.RUNS[r][1] for r in voters)
    return {r: 1.0 / fam[A.RUNS[r][1]] for r in voters}


def weights_family_sqrt(voters: list[str]) -> dict[str, float]:
    fam = collections.Counter(A.RUNS[r][1] for r in voters)
    return {r: fam[A.RUNS[r][1]] ** -0.5 for r in voters}


def weights_platform(voters: list[str]) -> dict[str, float]:
    """Platform matched (family mean for runs never uploaded), relative to 125."""
    pm = {r: A.RUNS[r][2] or 140.5 for r in voters}
    return {r: max(0.0, (pm[r] - 125) / 20) for r in voters}


def mean_conf(c: A.Cluster) -> float:
    vals = [m.confidence for m in c.members if m.confidence is not None]
    return statistics.mean(vals) if vals else 0.0


def ranking(w: dict[str, float], tiebreak: str = "none") -> Rank:
    def score(c: A.Cluster) -> float:
        s = sum(w.get(r, 0.0) for r in c.runs)
        if tiebreak == "conf":
            s += 0.5 * mean_conf(c)  # inside one vote step (weights are >= 1 for uniform)
        elif tiebreak == "families":
            s += 0.01 * len({A.RUNS[r][1] for r in c.runs if r in w})
        return s

    return score


SIZES = (250, 300, 330, 360, 390, 420, 450, 500, 550)


def curve(
    clusters: list[A.Cluster],
    rank: Rank,
    rep: Callable[[A.Cluster, dict[tuple[str, str], str]], A.Row],
    src: dict[tuple[str, str], str],
    gold: A.Gold,
    sizes: tuple[int, ...] = SIZES,
) -> list[tuple[int, int, float, float]]:
    """(rows, local matched, local F2, platform estimate of matched) for each prefix size."""
    order = sorted(clusters, key=lambda c: -rank(c))
    reps = [rep(c, src) for c in order]
    out = []
    for n in sizes:
        picks = [(c.regulation, r.text) for c, r in zip(order[:n], reps[:n], strict=True)]
        hit = gold.match(picks)
        est = sum(RATIO[reps[i].run] for i in hit)
        out.append((n, len(hit), A.f2(len(hit), n), est))
    return out


def fmt(rows: list[tuple[int, int, float, float]]) -> str:
    return "  ".join(f"{n}:{m}/{f:.3f}/{e:.0f}" for n, m, f, e in rows)


def setup() -> tuple[list[A.Cluster], dict[tuple[str, str], str], A.Gold]:
    rows = A.load_rows()
    return A.build(rows, A.DEFAULT), A.source_texts(), A.Gold()


def cmd_weights(args: argparse.Namespace) -> None:
    clusters, src, gold = setup()
    print("rows:local matched/local F2/platform est. matched; representative = medoid")
    for vname, voters in (("14 voters", A.VOTERS), ("13 voters", A.VOTERS_13)):
        for wname, wf in (
            ("uniform", weights_uniform),
            ("family", weights_family),
            ("family-sqrt", weights_family_sqrt),
            ("platform", weights_platform),
        ):
            for tb in ("none", "conf", "families"):
                if wname != "uniform" and tb != "none":
                    continue
                res = curve(clusters, ranking(wf(voters), tb), A.rep_medoid, src, gold)
                print(f"{vname} {wname:<12}{tb:<9} {fmt(res)}", flush=True)
    # Plain vote cuts with their exact sizes.
    print("\nexact vote cuts, 14 voters, medoid:")
    for v in range(2, 13):
        keep = [c for c in clusters if c.votes() >= v]
        picks = [(c.regulation, A.rep_medoid(c, src).text) for c in keep]
        reps = [A.rep_medoid(c, src) for c in keep]
        hit = gold.match(picks)
        est = sum(RATIO[reps[i].run] for i in hit)
        print(
            f"  votes >= {v:>2}: {len(keep)} rows, {len(hit)} matched, "
            f"F2 {A.f2(len(hit), len(keep)):.3f}, "
            f"platform est. {est:.0f} ({A.f2(round(est), len(keep)):.3f})"
        )


def cmd_reps(args: argparse.Namespace) -> None:
    clusters, src, gold = setup()
    rank = ranking(weights_uniform(A.VOTERS), "conf")
    style = sorted(RATIO, key=lambda r: -RATIO[r])
    reps = dict(A.REPS)
    reps["style"] = A.rep_prefer(style)
    reps["fable>kbjev>opus"] = A.rep_prefer(["fable", "kb-jev", "opus", "sonnet", "dev-upload"])
    print("ranking: uniform votes, confidence tiebreak. rows:local/F2/platform est.")
    for name, rep in reps.items():
        res = curve(clusters, rank, rep, src, gold, (300, 330, 360, 390, 420, 450))
        order = sorted(clusters, key=lambda c: -rank(c))[:390]
        runs = collections.Counter(rep(c, src).run for c in order).most_common(4)
        share = statistics.median(
            A.word_share(rep(c, src).text, src.get((c.regulation, c.pkey), "")) for c in order
        )
        print(f"{name:<17} {fmt(res)}  | top-390 share {share:.2f} from {runs}", flush=True)


# Writers that keep a subject and condition: the runs whose style lost on the platform
# (minimal edit, qwen, the OpenAI mini rewrite, Sol) never represent a cluster when another
# member can.
TERSE = {"kb-jev-filter-v4", "qwen", "dev-upload", "kb-sol-rewrite"}


def rep_share_claude(c: A.Cluster, src: dict[tuple[str, str], str]) -> A.Row:
    """The member with the highest word share against the source paragraph, among the runs not in
    TERSE; ties go to the medoid of those members."""
    ms = [m for m in c.members if m.run not in TERSE] or c.members
    med = A.rep_medoid(A.Cluster(c.regulation, c.pkey, ms), src)
    text = src.get((c.regulation, c.pkey), "")
    if not text:
        return med
    return max(ms, key=lambda m: (round(A.word_share(m.text, text), 2), m is med))


def cmd_write(args: argparse.Namespace) -> None:
    import json

    clusters, src, gold = setup()
    keep = [c for c in clusters if c.votes() >= args.votes]
    reps = [rep_share_claude(c, src) for c in keep]
    files: dict[str, dict] = {}
    reqs = []
    for k, r in enumerate(reps, 1):
        if r.run not in files:
            files[r.run] = json.loads((A.OUT / A.RUNS[r.run][0]).read_text())
        rec = dict(files[r.run]["requirements"][r.idx])
        rec = {key: rec[key] for key in ("text", "source", "confidence", "quote") if key in rec}
        reqs.append({"id": f"R-{k:04d}", **rec})
    base = json.loads((A.OUT / "rear-lamp-fable.json").read_text())
    doc = {
        "team_id": "team-06",
        "case_id": "dev-rear-lamp",
        "requirements": reqs,
        "regulations": base["regulations"],
        "profile": base["profile"],
    }
    out = Path(args.out)
    out.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    hit = gold.match([(c.regulation, r.text) for c, r in zip(keep, reps, strict=True)])
    est = sum(RATIO[reps[i].run] for i in hit)
    runs = collections.Counter(r.run for r in reps).most_common()
    lines = [
        f"lane A vote file: {len(A.VOTERS)} voters, clusters at {A.DEFAULT.name}, "
        f"votes >= {args.votes}, representative share-claude (TERSE = {sorted(TERSE)})",
        f"rows {len(reqs)}, local matched {len(hit)}, local F2 {A.f2(len(hit), len(reqs)):.3f}",
        f"platform estimate (per-run platform/local ratio): {est:.1f} matched, "
        f"F2 {A.f2(round(est), len(reqs)):.3f}",
        f"representatives by run: {runs}",
        "spend: $0 (no model call)",
    ]
    out.with_suffix(".log").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("weights")
    sub.add_parser("reps")
    w = sub.add_parser("write")
    w.add_argument("--votes", type=int, required=True)
    w.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    {"weights": cmd_weights, "reps": cmd_reps, "write": cmd_write}[args.cmd](args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
