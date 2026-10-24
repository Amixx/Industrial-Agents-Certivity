"""Lane C of task 07: small files of the rows we are surest of, and why their misses miss.

    BRAIN_LLM= PYTHONPATH=. uv run python swing/c_precision.py pool     # C1: vote pool
    BRAIN_LLM= PYTHONPATH=. uv run python swing/c_precision.py build    # C1, C2: files, buckets
    BRAIN_LLM= PYTHONPATH=. uv run python swing/c_precision.py misses <file>   # C4: read misses

No model calls. The pool is 13 model-written dev files (finding 2 of the task); rows are
clustered per (regulation, paragraph) by the local judge's similarity, and a cluster's vote is
the number of distinct runs with a member in it.
"""

from __future__ import annotations

import collections
import csv
import json
import sys
from pathlib import Path
from typing import Any

from eval import judge
from eval.score import fbeta, paragraph_key

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out"
EXP = ROOT / "cases" / "dev-rear-lamp" / "expected.json"
POOL_PATH = OUT / "experiments" / "C-pool.json"

# Representative preference: Fable first (best platform F2), then by platform matched.
RUNS = {
    "fable": OUT / "rear-lamp-fable.json",
    "kb-jev": OUT / "rear-lamp-kb-jev.json",
    "opus": OUT / "rear-lamp-opus.json",
    "dev-upload": ROOT / "brain" / "out" / "dev-upload.json",
    "main-cli": OUT / "rear-lamp-main-cli.json",
    "kb-sol-rewrite": OUT / "rear-lamp-kb-sol-rewrite.json",
    "sonnet": OUT / "rear-lamp-sonnet.json",
    "kb-jev-filter-v4": OUT / "rear-lamp-kb-jev-filter-v4.json",
    "mix-examples-cut": OUT / "rear-lamp-mix-examples-cut.json",
    "mix-examples": OUT / "rear-lamp-mix-examples.json",
    "mix": OUT / "rear-lamp-mix.json",
    "mix-noimage": OUT / "rear-lamp-mix-noimage.json",
    "qwen-split-rewrite": OUT / "rear-lamp-qwen-split-rewrite.json",
}
SIM = 0.6


def key(r: dict[str, Any]) -> tuple[str, str | None]:
    return r["source"]["regulation"], paragraph_key(r["source"].get("paragraph"))


def load(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text())["requirements"]


def build_pool(sim: float = SIM) -> list[dict[str, Any]]:
    """Leader clustering per paragraph, runs in preference order; a row joins the most similar
    cluster at `sim` or more that has no member from its own run yet."""
    by_par: dict[tuple, list[dict[str, Any]]] = collections.defaultdict(list)
    for run, path in RUNS.items():
        for r in load(path):
            k = key(r)
            best, best_s = None, sim
            for c in by_par[k]:
                if run in c["runs"]:
                    continue
                s = max(judge.similarity(r["text"], m["text"]) for m in c["members"])
                if s >= best_s:
                    best, best_s = c, s
            member = {
                "run": run,
                "text": r["text"],
                "confidence": r.get("confidence"),
                "source": r["source"],
            }
            if best is None:
                by_par[k].append(
                    {
                        "regulation": k[0],
                        "paragraph": k[1],
                        "page": r["source"].get("page"),
                        "runs": [run],
                        "members": [member],
                    }
                )
            else:
                best["runs"].append(run)
                best["members"].append(member)
    pool = [c for cs in by_par.values() for c in cs]
    for c in pool:
        c["votes"] = len(c["runs"])
    return pool


def as_row(m: dict[str, Any], i: int) -> dict[str, Any]:
    row = {"id": f"R-{i:04d}", "text": m["text"], "source": m["source"]}
    if m.get("confidence") is not None:
        row["confidence"] = m["confidence"]
    return row


def submission(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "team_id": "team-06",
        "case_id": "dev-rear-lamp",
        "requirements": [
            {**{k: v for k, v in r.items() if k != "votes"}, "id": f"R-{i:04d}"}
            for i, r in enumerate(rows, 1)
        ],
    }


def rep(c: dict[str, Any], prefer: tuple[str, ...] = ()) -> dict[str, Any]:
    for run in prefer:
        for m in c["members"]:
            if m["run"] == run:
                return m
    return c["members"][0]


def buckets(rows: list[dict[str, Any]], exp: list[dict[str, Any]]) -> dict[str, Any]:
    """Matched count and the three kinds of unmatched row."""
    pairs = judge.match(rows, exp)
    hit = {i for i, _, _ in pairs}
    gold = collections.Counter(key(r) for r in exp)
    ours = collections.Counter(key(r) for r in rows)
    out = {"rows": len(rows), "matched": len(pairs), "not_cited": 0, "excess": 0, "wording": 0}
    for i, r in enumerate(rows):
        if i in hit:
            continue
        k = key(r)
        if k not in gold:
            out["not_cited"] += 1
        elif ours[k] > gold[k]:
            out["excess"] += 1
        else:
            out["wording"] += 1
    p, rec = out["matched"] / max(1, len(rows)), out["matched"] / len(exp)
    out["precision"], out["f2"] = round(p, 3), round(fbeta(p, rec), 3)
    out["gold_paragraph_rows"] = sum(1 for r in rows if key(r) in gold)
    return out


def silver() -> dict[tuple[str, str], bool]:
    """Silver bumper labels; a mark on a heading covers the paragraphs below it."""
    marks: dict[tuple[str, str], bool] = {}
    for name in ("labels-r42-r26.csv", "labels-r127-gtr9.csv"):
        with (ROOT / "brain" / "data" / "bumper-labels" / name).open() as f:
            for r in csv.DictReader(f):
                if r["cited"] in ("y", "n"):
                    marks[(r["regulation"], r["paragraph"].strip().rstrip("."))] = r["cited"] == "y"
    return marks


def silver_cited(marks: dict[tuple[str, str], bool], reg: str, par: str) -> bool | None:
    parts = par.strip().rstrip(".").split(".")
    for n in range(len(parts), 0, -1):
        k = (reg, ".".join(parts[:n]))
        if k in marks:
            return marks[k]
    return marks.get((reg, "(whole regulation)"))


def transfer() -> int:
    """Paragraph precision against the silver bumper labels, by relevance confidence and by
    agreement between the two bumper runs in brain/out/."""
    marks = silver()
    llm = load(ROOT / "brain" / "out" / "bumper-plain-llm.json")
    other = {key(r) for r in load(ROOT / "brain" / "out" / "bumper-plain.json")}
    rows = []
    for r in llm:
        c = silver_cited(marks, r["source"]["regulation"], r["source"]["paragraph"])
        if c is not None:
            rows.append((r.get("confidence") or 0, c, key(r) in other))
    rows.sort(key=lambda t: -t[0])
    print(
        f"bumper-plain-llm: {len(llm)} rows, {len(rows)} labelled, "
        f"{sum(c for _, c, _ in rows)} on silver-cited paragraphs"
    )
    third = max(1, len(rows) // 3)
    for name, part in (
        ("top third", rows[:third]),
        ("middle third", rows[third : 2 * third]),
        ("bottom third", rows[2 * third :]),
    ):
        print(
            f"  {name:<13} conf {part[-1][0]:.2f} to {part[0][0]:.2f}: "
            f"{sum(c for _, c, _ in part)}/{len(part)} on cited paragraphs"
        )
    for flag in (True, False):
        part = [t for t in rows if t[2] == flag]
        print(f"  also in bumper-plain.json = {flag}: {sum(c for _, c, _ in part)}/{len(part)}")
    return 0


def main(argv: list[str]) -> int:
    exp = load(EXP)
    cmd = argv[0] if argv else "build"
    if cmd == "pool":
        pool = build_pool()
        POOL_PATH.write_text(json.dumps(pool, indent=1, ensure_ascii=False))
        votes = collections.Counter(c["votes"] for c in pool)
        print(f"{len(pool)} clusters; by votes: {sorted(votes.items())}")
        return 0
    if cmd == "build":
        pool = json.loads(POOL_PATH.read_text())
        fable_kb = ("fable", "kb-jev")

        def conf(c: dict[str, Any], run: str) -> float:
            return max((m["confidence"] or 0 for m in c["members"] if m["run"] == run), default=0.0)

        def kb_conf(c: dict[str, Any]) -> float:
            return conf(c, "kb-jev")

        def sure(c: dict[str, Any], t: float = 0.6) -> bool:
            return conf(c, "fable") >= t or conf(c, "kb-jev") >= t

        kb_rows = load(RUNS["kb-jev"])
        kb_sorted = sorted(kb_rows, key=lambda r: -(r.get("confidence") or 0))
        fable_rows = load(RUNS["fable"])
        conf06 = [r for r in kb_rows if (r.get("confidence") or 0) >= 0.6]
        seen = {(key(r), r["text"]) for r in conf06}
        conf06 += [
            r
            for r in fable_rows
            if (r.get("confidence") or 0) >= 0.6 and (key(r), r["text"]) not in seen
        ]
        variants: dict[str, list[dict[str, Any]]] = {}
        for n in (10, 11, 12, 13):
            cs = [c for c in pool if c["votes"] >= n]
            variants[f"votes{n}"] = [{**rep(c, fable_kb), "votes": c["votes"]} for c in cs]
            variants[f"votes{n}-kbjev"] = [
                {**rep(c, ("kb-jev", "fable")), "votes": c["votes"]} for c in cs
            ]
        variants["conf06"] = conf06
        for n in (120, 150, 180):
            variants[f"kbjev-top{n}"] = kb_sorted[:n]
        for n, t in ((8, 0.6), (10, 0.6), (10, 0.5), (8, 0.5), (6, 0.5)):
            cs = [c for c in pool if c["votes"] >= n and (sure(c, t))]
            variants[f"both-v{n}-c{int(t * 10):02d}"] = [
                {**rep(c, fable_kb), "votes": c["votes"]} for c in cs
            ]
        cs = [c for c in pool if c["votes"] >= 10]
        cs.sort(key=kb_conf, reverse=True)
        variants["votes10-kbtop150"] = [{**rep(c, fable_kb), "votes": c["votes"]} for c in cs[:150]]
        print(
            f"{'variant':<22}{'rows':>5}{'match':>6}{'P':>7}{'F2':>7}"
            f"{'notcit':>7}{'excess':>7}{'wording':>8}{'in-gold':>8}"
        )
        results = {}
        for name, rows in variants.items():
            rows = [{k: v for k, v in r.items() if k != "run"} for r in rows]
            b = buckets(rows, exp)
            results[name] = b
            print(
                f"{name:<22}{b['rows']:>5}{b['matched']:>6}{b['precision']:>7.3f}"
                f"{b['f2']:>7.3f}{b['not_cited']:>7}{b['excess']:>7}{b['wording']:>8}"
                f"{b['gold_paragraph_rows']:>8}"
            )
            if name in argv[1:]:
                path = OUT / f"rear-lamp-swing-C-{name}.json"
                path.write_text(json.dumps(submission(rows), indent=2, ensure_ascii=False))
                print(f"  wrote {path.relative_to(ROOT)}")
        (OUT / "experiments" / "C-buckets.json").write_text(json.dumps(results, indent=1))
        return 0
    if cmd == "transfer":
        return transfer()
    if cmd == "misses":
        rows = load(Path(argv[1]))
        pairs = judge.match(rows, exp)
        hit = {i for i, _, _ in pairs}
        gold_by_key = collections.defaultdict(list)
        for j, g in enumerate(exp):
            gold_by_key[key(g)].append(j)
        matched_exp = {j for _, j, _ in pairs}
        for i, r in enumerate(rows):
            if i in hit:
                continue
            k = key(r)
            print(f"\n## {k[0]} {k[1]} (p{r['source'].get('page')}) votes={r.get('votes')}")
            print(f"OURS: {r['text']}")
            for j in gold_by_key.get(k, []):
                tag = "matched" if j in matched_exp else "free"
                sim = judge.similarity(r["text"], exp[j]["text"])
                print(f"GOLD [{tag} {sim:.2f}]: {exp[j]['text']}")
        return 0
    raise SystemExit(f"unknown command {cmd}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
