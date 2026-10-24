"""Lane A: pool every model-written dev run, cluster rows per paragraph, keep what runs agree on.

    PYTHONPATH=. uv run python swing/a_votes.py pool        # writes ../out/experiments/A-pool.json
    PYTHONPATH=. uv run python swing/a_votes.py settings    # clustering settings against the gold

All offline: no model call. The local judge is eval.judge (token Jaccard, one to one).
"""

from __future__ import annotations

import argparse
import collections
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

from brain.paths import CASES
from eval import judge
from eval.score import paragraph_key

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out"
EXP = OUT / "experiments"
CORPUS = ROOT / "brain" / "data" / "corpus"
EXPECTED = CASES / "dev-rear-lamp" / "expected.json"
N_GOLD = 190

# name: (path, family, platform matched or None, model of the rewrite)
# Families group runs that share paragraph selection and rewrite model, so their rows are close
# copies of each other: Opus relevance + Sonnet rewrite is one family of six runs.
RUNS: dict[str, tuple[str, str, int | None]] = {
    "fable": ("rear-lamp-fable.json", "fable", 149),
    "opus": ("rear-lamp-opus.json", "opus", 143),
    "sonnet": ("rear-lamp-sonnet.json", "sonnet", 140),
    "kb-jev": ("rear-lamp-kb-jev.json", "kb-opus", 154),
    "kb-jev-filter-v4": ("rear-lamp-kb-jev-filter-v4.json", "kb-opus", 140),
    "kb-sol-rewrite": ("rear-lamp-kb-sol-rewrite.json", "kb-sol", 143),
    "main-cli": ("rear-lamp-main-cli.json", "opus-sonnet", 143),
    "main-a39acab": ("rear-lamp-main-a39acab.json", "opus-sonnet", None),
    "mix": ("rear-lamp-mix.json", "opus-sonnet", None),
    "mix-examples": ("rear-lamp-mix-examples.json", "opus-sonnet", None),
    "mix-noimage": ("rear-lamp-mix-noimage.json", "opus-sonnet", None),
    "mix-examples-cut": ("rear-lamp-mix-examples-cut.json", "opus-sonnet", 138),
    "mix-examples-cut-consolidated": (
        "rear-lamp-mix-examples-cut-consolidated.json",
        "opus-sonnet",
        None,
    ),
    "dev-upload": ("../brain/out/dev-upload.json", "gpt", 145),
    "qwen": ("rear-lamp-qwen-split-rewrite.json", "qwen", 133),
}
# The consolidated file is a filtered copy of mix-examples-cut: in the pool, never a voter.
VOTERS = [r for r in RUNS if r != "mix-examples-cut-consolidated"]
VOTERS_13 = [r for r in VOTERS if r != "main-a39acab"]  # the 13 of finding 2

_VALUE = re.compile(r"\d+(?:[.,]\d+)*")


def value_numbers(text: str) -> frozenset[str]:
    """Numbers that are values, not paragraph references: "5", "0.5", "1,000"; not "3.3.3.2"."""
    return frozenset(n for n in _VALUE.findall(text) if n.count(".") < 2)


@dataclass
class Row:
    run: str
    idx: int
    text: str
    regulation: str
    paragraph: str
    pkey: str
    page: int
    version: str
    quote: str
    confidence: float | None
    toks: frozenset[str] = field(default_factory=frozenset)
    nums: frozenset[str] = field(default_factory=frozenset)


def load_rows(runs: list[str] | None = None) -> list[Row]:
    rows: list[Row] = []
    for run in runs or list(RUNS):
        data = json.loads((OUT / RUNS[run][0]).read_text())
        for i, r in enumerate(data["requirements"]):
            s = r["source"]
            rows.append(
                Row(
                    run,
                    i,
                    r["text"],
                    s["regulation"],
                    str(s.get("paragraph") or ""),
                    paragraph_key(s.get("paragraph")) or "",
                    int(s.get("page") or 0),
                    s.get("version", ""),
                    r.get("quote") or "",
                    r.get("confidence"),
                    frozenset(judge.tokens(r["text"])),
                    value_numbers(r["text"]),
                )
            )
    return rows


def source_texts() -> dict[tuple[str, str], str]:
    """(regulation, paragraph key) -> paragraph text, for the four dev regulations."""
    out: dict[tuple[str, str], str] = {}
    for reg in ["UN R148", "UN R48", "UN R150", "UN R10", "UN R26"]:
        path = CORPUS / f"{'_'.join(reg.split())}_base.jsonl"
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            p = json.loads(line)
            key = paragraph_key(p["label"])
            if key and (reg, key) not in out:
                out[(reg, key)] = p["text"]
    return out


def word_share(text: str, source: str) -> float:
    """Fraction of the row's words (tokens, stop words dropped) that appear in the source."""
    t = judge.tokens(text)
    return len(t & judge.tokens(source)) / max(1, len(t))


def jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    return len(a & b) / max(1, len(a | b))


@dataclass
class Setting:
    threshold: float
    numbers: bool  # True: rows with different value numbers never cluster

    @property
    def name(self) -> str:
        return f"j{self.threshold:.2f}{'-num' if self.numbers else ''}"


def cluster_group(rows: list[Row], s: Setting) -> list[list[int]]:
    """Average-linkage clustering of one paragraph's rows; two rows of the same run never share
    a cluster, so a cluster's size is its vote count."""
    n = len(rows)
    sim = np.zeros((n, n))
    for a in range(n):
        for b in range(a + 1, n):
            if s.numbers and rows[a].nums != rows[b].nums:
                v = -1.0
            else:
                v = jaccard(rows[a].toks, rows[b].toks)
            sim[a, b] = sim[b, a] = v
    clusters: list[list[int]] = [[i] for i in range(n)]
    runs: list[set[str]] = [{r.run} for r in rows]
    while len(clusters) > 1:
        best, pair = s.threshold, None
        for a in range(len(clusters)):
            for b in range(a + 1, len(clusters)):
                if runs[a] & runs[b]:
                    continue
                sub = sim[np.ix_(clusters[a], clusters[b])]
                if s.numbers and (sub < 0).any():
                    continue
                v = float(sub.mean())
                if v >= best:
                    best, pair = v, (a, b)
        if pair is None:
            break
        a, b = pair
        clusters[a] = clusters[a] + clusters[b]
        runs[a] = runs[a] | runs[b]
        del clusters[b], runs[b]
    return clusters


@dataclass
class Cluster:
    regulation: str
    pkey: str
    members: list[Row]

    @property
    def runs(self) -> set[str]:
        return {m.run for m in self.members}

    def votes(self, voters: list[str] | None = None) -> int:
        return len(self.runs & set(voters or VOTERS))


def build(rows: list[Row], s: Setting) -> list[Cluster]:
    groups: dict[tuple[str, str], list[Row]] = collections.defaultdict(list)
    for r in rows:
        groups[(r.regulation, r.pkey)].append(r)
    out: list[Cluster] = []
    for (reg, key), grp in sorted(groups.items()):
        for c in cluster_group(grp, s):
            out.append(Cluster(reg, key, [grp[i] for i in c]))
    return out


# Representatives -------------------------------------------------------------------------------

REP_ORDER = {"fable": 0, "kb-jev": 1, "opus": 2}


def rep_medoid(c: Cluster, src: dict[tuple[str, str], str]) -> Row:
    if len(c.members) == 1:
        return c.members[0]
    return max(
        c.members,
        key=lambda m: sum(jaccard(m.toks, o.toks) for o in c.members if o is not m),
    )


def rep_prefer(order: list[str]):  # type: ignore[no-untyped-def]
    def pick(c: Cluster, src: dict[tuple[str, str], str]) -> Row:
        for run in order:
            for m in c.members:
                if m.run == run:
                    return m
        return rep_medoid(c, src)

    return pick


def rep_share(c: Cluster, src: dict[tuple[str, str], str]) -> Row:
    text = src.get((c.regulation, c.pkey), "")
    if not text:
        return rep_medoid(c, src)
    med = rep_medoid(c, src)
    return max(c.members, key=lambda m: (round(word_share(m.text, text), 2), m is med))


def rep_longest(c: Cluster, src: dict[tuple[str, str], str]) -> Row:
    return max(c.members, key=lambda m: len(m.toks))


REPS = {
    "medoid": rep_medoid,
    "fable": rep_prefer(["fable"]),
    "opus": rep_prefer(["opus"]),
    "kb-jev": rep_prefer(["kb-jev"]),
    "share": rep_share,
    "longest": rep_longest,
}


# Scoring ---------------------------------------------------------------------------------------


class Gold:
    """The dev gold with a cache of each text's similarity vector against it."""

    def __init__(self, path: Path = EXPECTED) -> None:
        self.rows = json.loads(path.read_text())["requirements"]
        self.by_reg: dict[str, list[int]] = collections.defaultdict(list)
        for j, r in enumerate(self.rows):
            self.by_reg[r["source"]["regulation"]].append(j)
        self._cache: dict[tuple[str, str], np.ndarray] = {}

    def vec(self, reg: str, text: str) -> np.ndarray:
        k = (reg, text)
        if k not in self._cache:
            self._cache[k] = np.array(
                [judge.similarity(text, self.rows[j]["text"]) for j in self.by_reg.get(reg, [])]
            )
        return self._cache[k]

    def match(self, picks: list[tuple[str, str]], threshold: float = 0.45) -> list[int]:
        """Indices into `picks` (regulation, text) that the one-to-one judge matches."""
        hit: list[int] = []
        by: dict[str, list[int]] = collections.defaultdict(list)
        for i, (reg, _) in enumerate(picks):
            by[reg].append(i)
        for reg, idx in by.items():
            if not self.by_reg.get(reg):
                continue
            m = np.stack([self.vec(reg, picks[i][1]) for i in idx])
            ok = m >= threshold
            if not ok.any():
                continue
            r, c = linear_sum_assignment(-np.where(ok, 1.0 + m, 0.0))
            hit.extend(idx[a] for a, b in zip(r, c, strict=True) if m[a, b] >= threshold)
        return hit

    def matched(self, picks: list[tuple[str, str]]) -> int:
        return len(self.match(picks))


def f2(matched: int, rows: int) -> float:
    return 5 * matched / (4 * N_GOLD + rows)


# Pool file -------------------------------------------------------------------------------------


def pool_records(clusters: list[Cluster], src: dict[tuple[str, str], str]) -> list[dict[str, Any]]:
    recs = []
    for k, c in enumerate(clusters):
        text = src.get((c.regulation, c.pkey), "")
        paras = collections.Counter(m.paragraph for m in c.members)
        pages = collections.Counter(m.page for m in c.members)
        recs.append(
            {
                "cluster": k,
                "regulation": c.regulation,
                "paragraph": paras.most_common(1)[0][0],
                "paragraph_key": c.pkey,
                "page": pages.most_common(1)[0][0],
                "votes": c.votes(VOTERS),
                "votes_13": c.votes(VOTERS_13),
                "families": len({RUNS[r][1] for r in c.runs & set(VOTERS)}),
                "medoid": rep_medoid(c, src).text,
                "members": [
                    {
                        "file": "out/" + RUNS[m.run][0]
                        if not RUNS[m.run][0].startswith("..")
                        else RUNS[m.run][0][3:],
                        "run": m.run,
                        "id_index": m.idx,
                        "text": m.text,
                        "page": m.page,
                        "paragraph": m.paragraph,
                        "confidence": m.confidence,
                        "word_share": round(word_share(m.text, text), 3) if text else None,
                    }
                    for m in c.members
                ],
            }
        )
    return recs


DEFAULT = Setting(0.5, False)


def cmd_pool(args: argparse.Namespace) -> None:
    s = Setting(args.threshold, args.numbers)
    rows = load_rows()
    src = source_texts()
    clusters = build(rows, s)
    recs = pool_records(clusters, src)
    gold = Gold()
    # Which clusters' medoid the local judge matches when every cluster is submitted at once
    # (an upper bound on what any vote cut can reach with medoid text).
    picks = [(c.regulation, rep_medoid(c, src).text) for c in clusters]
    for i in gold.match(picks):
        recs[i]["medoid_matched_in_full_pool"] = True
    doc = {
        "about": (
            "Lane A pool (brain/docs/todo/07-big-swings.md). One record per cluster of rows from "
            "the same (regulation, paragraph). Rows cluster by average-linkage token Jaccard "
            f"(eval.judge.tokens) at {s.threshold}"
            + (", rows with different value numbers never cluster" if s.numbers else "")
            + "; two rows of one run never share a cluster. votes = distinct voting runs "
            f"({len(VOTERS)}: every run but the consolidated file); votes_13 = the 13 of finding 2 "
            "(also without main-a39acab). families = distinct run families among the voters."
        ),
        "setting": s.name,
        "runs": {
            r: {"file": RUNS[r][0], "family": RUNS[r][1], "platform_matched": RUNS[r][2]}
            for r in RUNS
        },
        "voters": VOTERS,
        "clusters": recs,
    }
    path = Path(args.out)
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    hist = collections.Counter(r["votes"] for r in recs)
    print(f"{len(rows)} rows, {len(recs)} clusters -> {path}")
    print("votes histogram:", sorted(hist.items()))
    print("clusters whose medoid matches in the full pool:", len(gold.match(picks)))


def cmd_settings(args: argparse.Namespace) -> None:
    rows = load_rows()
    src = source_texts()
    gold = Gold()
    for s in [Setting(t, n) for t in (0.5, 0.6, 0.7) for n in (False, True)]:
        clusters = build(rows, s)
        line = [f"{s.name:<10} clusters {len(clusters):>5}"]
        for n in (3, 4, 5, 6, 8, 10):
            keep = [c for c in clusters if c.votes(VOTERS_13) >= n]
            picks = [(c.regulation, rep_medoid(c, src).text) for c in keep]
            m = gold.matched(picks)
            line.append(f"v{n}: {len(keep)}/{m}/{f2(m, len(keep)):.3f}")
        print("  ".join(line), flush=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pool")
    p.add_argument("--threshold", type=float, default=DEFAULT.threshold)
    p.add_argument("--numbers", action="store_true")
    p.add_argument("--out", default=str(EXP / "A-pool.json"))
    sub.add_parser("settings")
    args = ap.parse_args(argv)
    {"pool": cmd_pool, "settings": cmd_settings}[args.cmd](args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
