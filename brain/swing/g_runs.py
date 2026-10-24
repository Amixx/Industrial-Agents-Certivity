"""Lane G: can a vote over several cheap runs work on an unseen bumper on Sunday?

    # one run of the pipeline, with its model, prompts and paragraph order, timed and priced
    PYTHONPATH=. uv run python swing/g_runs.py run data/synthetic/bumper-plain --name haiku-a \
        --rel-model claude-haiku-5-5 --rw-model claude-haiku-5-5 --rel-prompt base --seed 0
    # paragraph votes (and row clusters) over several runs
    PYTHONPATH=. uv run python swing/g_runs.py vote bumper-plain haiku-a haiku-b ... --min 2
    # paragraph precision and recall against the silver bumper labels
    PYTHONPATH=. uv run python swing/g_runs.py labels bumper-plain haiku-a vote-...

Every run writes `../out/experiments/G-<case>-<name>.json` (the submission), `.log` (stderr) and
`-scores.json` (relevance and blended score of every candidate paragraph, timings, spend).
Prompts and models are patched at runtime; no shared file is edited.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import re
import sys
import threading
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "out" / "experiments"
LABELS = ROOT / "brain" / "data" / "bumper-labels"
BUMPER_REGS = ["UN R42", "UN R26", "UN R127", "UN GTR 9"]

# $ per million tokens: input, output, cache read
PRICE = {
    "claude-sonnet-5-5": (2, 10, 0.2),
    "claude-opus-5-5": (4, 20, 0.2),
    "claude-fable-5-1": (10, 50, 0.25),
    "claude-haiku-5-5": (0.1, 0.5, 0.01),
}

# Variant prompts. Same criteria as brain.relevance._SYSTEM, reworded and reordered, so a second
# run sees a different prompt without a different calibration target. No dev gold text.
REL_ALT = """You review UN Regulations for one automotive component and decide which paragraphs
belong in its requirement list. A requirement list names what the component must meet, and what
the vehicle must meet because of this component. Experts cite few paragraphs of each regulation.
Give each paragraph the probability that such an expert list cites it.

An expert tends to leave out:
- scope, definitions and administration (approval application, marking forms, communication,
  extensions, discontinued production, transitional provisions, technical services);
- paragraphs on devices, functions or vehicle categories this product does not have;
- descriptions of the test rig or laboratory equipment that set no limit for the component;
- sampling rules and tolerances for conformity-of-production inspectors.

An expert tends to keep:
- provisions every device or vehicle under the regulation must meet;
- what the component must achieve in construction, performance, size, position, strength,
  durability, markings, or behaviour in a named test, for the parts and functions it has;
- vehicle requirements that depend on this component (installation, position, visibility, state
  after an impact or test) where the regulation approves the vehicle;
- limit values and pass criteria for the component, also in annexes;
- for electromagnetic compatibility, the requirements on electrical/electronic sub-assemblies."""

RW_VERBATIM = """You turn paragraphs of UN Regulations into engineering requirements for a product.
Each requirement is the regulation's own sentence, with as few words changed as possible:
- Copy the sentence that states the obligation word for word: numbers, units, tolerances,
  references, passive voice and the modal verb ("shall", "shall not", "may ... only if").
- If the sentence has no explicit subject, or uses a pronoun, put the subject in front, taken
  from the heading path ("The front fog lamp shall ...").
- If the paragraph completes its parent's clause (parent_text ends with ":" or "the following"),
  put the parent's condition in front ("After each impact test made in accordance with ...,").
- Keep the condition the sentence already has ("When tested in accordance with ...").
- Split only where the source itself lists separate items (lettered or numbered items, table rows
  with their own values, optional or alternative cases); each item becomes its own requirement,
  with the shared condition and subject repeated.
- Fold "However, ..." exceptions into the same requirement as "..., except that ...".
- Ignore footnote text and footnote markers glued to words.
- Skip pure definitions, permissions with no constraint, and text that is not an obligation.
Return an empty list for a paragraph with no obligation."""

usage: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0, 0])  # calls, in, out, cache read
hits: dict[str, int] = defaultdict(int)
timings: dict[str, float] = {}
captured: dict[str, Any] = {}
lock = threading.Lock()


def log(msg: str) -> None:
    print(f"[g {time.strftime('%H:%M:%S')}] {msg}", file=sys.stderr, flush=True)


def spend() -> tuple[float, list[str]]:
    total, lines = 0.0, []
    for m, (c, i, o, cr) in usage.items():
        pi, po, pc = PRICE.get(m, (0, 0, 0))
        cost = (i * pi + o * po + cr * pc) / 1e6
        total += cost
        lines.append(f"{m}: {c} calls, {i:,} in / {o:,} out / {cr:,} cache read; ${cost:.3f}")
    lines += [f"{m}: {h} cache hits" for m, h in hits.items()]
    return total, lines


def timed(name: str, fn: Any) -> Any:
    def wrap(*a: Any, **kw: Any) -> Any:
        t = time.time()
        try:
            return fn(*a, **kw)
        finally:
            timings[name] = timings.get(name, 0.0) + time.time() - t
            log(f"{name} took {timings[name]:.0f} s")

    return wrap


def patch(args: argparse.Namespace) -> None:
    """Models, prompts, paragraph order, cost and time logging, all at runtime."""
    import anthropic.resources.beta.messages as M

    from brain import llm, pipeline, relevance, rewrite

    os.environ["BRAIN_LLM"] = "anthropic"
    os.environ["BRAIN_MODEL_STRONG"] = args.rel_model
    os.environ["BRAIN_MODEL_BULK"] = args.rw_model

    orig_create = M.Messages.create

    def create(self: Any, **kw: Any) -> Any:
        if kw["model"].startswith("claude-haiku"):  # no server-side fallback for Haiku
            kw.pop("fallbacks", None)
            kw["betas"] = [b for b in kw.get("betas", []) if "fallback" not in b]
        r = orig_create(self, **kw)
        u = r.usage
        with lock:
            a = usage[kw["model"]]
            a[0] += 1
            a[1] += u.input_tokens + (u.cache_creation_input_tokens or 0)
            a[2] += u.output_tokens
            a[3] += u.cache_read_input_tokens or 0
        return r

    M.Messages.create = create  # type: ignore[method-assign]

    orig_cj = llm.complete_json

    def cj(system: str, content: Any, schema: Any, *, tier: Any = "bulk", **kw: Any) -> Any:
        payload = {
            "provider": llm.provider(),
            "model": llm.model_for(tier),
            "system": system,
            "content": content,
            "schema": schema,
            "effort": kw.get("effort", "medium"),
        }
        if llm._cache_path(payload).exists():
            with lock:
                hits[llm.model_for(tier)] += 1
        return orig_cj(system, content, schema, tier=tier, **kw)

    llm.complete_json = cj  # type: ignore[assignment]

    if args.rel_prompt == "alt":
        relevance._SYSTEM = REL_ALT
    if args.rw_prompt == "verbatim":
        rewrite._SYSTEM = RW_VERBATIM
    if getattr(args, "weight", None) is not None:
        # blend() binds its default at import, so assigning relevance.WEIGHT does nothing.
        orig_blend = relevance.blend

        def blend(model_p: float, llm_p: float | None, weight: float | None = None) -> float:
            return orig_blend(model_p, llm_p, args.weight if weight is None else weight)

        relevance.blend = blend  # type: ignore[method-assign]
        relevance.WEIGHT = args.weight

    orig_score = relevance.score

    def score(paragraphs: list[Any], graph: Any, profile: Any, **kw: Any) -> dict[str, float]:
        order = list(paragraphs)
        if args.seed:  # a different order gives every batch different neighbours
            random.Random(args.seed).shuffle(order)
        out = orig_score(order, graph, profile, batch=args.rel_batch, **kw)
        captured["llm"] = out
        return out

    relevance.score = timed("relevance", score)  # type: ignore[assignment]

    orig_select = pipeline.select_paragraphs

    def select(profile: Any, corpus: Any, choices: Any, threshold: Any = None, use_llm=False):  # type: ignore[no-untyped-def]
        chosen, graph = orig_select(profile, corpus, choices, threshold, use_llm)
        captured["chosen"] = {p.id: pr for p, pr in chosen}
        # The decision model's own probability, as select_paragraphs computes it, so votes and
        # score averages can be re-blended offline.
        regs = [c.regulation for c in choices if c.selected]
        sub = {r: corpus[r] for r in regs}
        g = pipeline.build(sub, set(corpus))
        ctx = pipeline.F.build_context(
            profile, sub, g, {c.regulation: c.probability for c in choices}
        )
        cands = [
            p
            for r in regs
            for p in sub[r]
            if p.number and p.label != "preamble" and not p.label.startswith("Rationale")
        ]
        probs = pipeline.Model.load(pipeline.MODEL_PATH).predict(pipeline.F.matrix(cands, ctx))
        captured["model"] = {p.id: float(pr) for p, pr in zip(cands, probs, strict=True)}
        captured["labels"] = {
            p.id: (p.regulation, p.label)
            for r in [c.regulation for c in choices if c.selected]
            for p in corpus[r]
            if p.number
        }
        return chosen, graph

    pipeline.select_paragraphs = select  # type: ignore[assignment]

    if args.only:  # the reviewed regulation list, as on Sunday after the 08:30 review
        orig_review = pipeline.review

        def review(choices: Any, include: Any = (), exclude: Any = ()) -> Any:
            out = orig_review(choices, include, exclude)
            return [c.model_copy(update={"selected": c.regulation in args.only}) for c in out]

        pipeline.review = review  # type: ignore[assignment]
    pipeline.build_profile = timed("profile", pipeline.build_profile)  # type: ignore[assignment]
    pipeline.choose = timed("regulations", pipeline.choose)  # type: ignore[assignment]
    pipeline.rewrite = timed("rewrite", pipeline.rewrite)  # type: ignore[assignment]


def cmd_run(args: argparse.Namespace) -> int:
    patch(args)
    from brain import pipeline

    case = Path(args.case)
    out = EXP / f"G-{case.name}-{args.name}.json"
    t0 = time.time()
    argv = [str(case), "-o", str(out), "--team-id", "team-06"]
    if args.include:
        argv += ["--include", *args.include]
    if args.exclude:
        argv += ["--exclude", *args.exclude]
    if args.threshold is not None:
        argv += ["--threshold", str(args.threshold)]
    code = pipeline.main(argv)
    wall = time.time() - t0
    total, lines = spend()
    for line in lines:
        log(line)
    log(f"wall clock {wall:.0f} s, new spend ${total:.3f}")
    labels = captured.get("labels", {})
    llm_p = captured.get("llm", {})
    chosen = captured.get("chosen", {})
    record = {
        "case": case.name,
        "name": args.name,
        "rel_model": args.rel_model,
        "rw_model": args.rw_model,
        "rel_prompt": args.rel_prompt,
        "rw_prompt": args.rw_prompt,
        "seed": args.seed,
        "rel_batch": args.rel_batch,
        "wall_s": round(wall, 1),
        "timings_s": {k: round(v, 1) for k, v in timings.items()},
        "spend_usd": round(total, 4),
        "usage": {m: v for m, v in usage.items()},
        "cache_hits": dict(hits),
        "paragraphs": [
            {
                "id": pid,
                "regulation": reg,
                "paragraph": lab,
                "llm": llm_p.get(pid),
                "model": captured.get("model", {}).get(pid),
                "selected": pid in chosen,
                "blend": chosen.get(pid),
            }
            for pid, (reg, lab) in labels.items()
        ],
    }
    (EXP / f"G-{case.name}-{args.name}-scores.json").write_text(json.dumps(record, indent=1))
    return code


# ---------- votes ----------

_TOKEN = re.compile(r"[a-z0-9]+(?:[.,]\d+)*")
_STOP = frozenset(
    "the a an of to and or in on at by for be is are shall with as that this which "
    "it its from than any all each".split()
)


def toks(text: str) -> frozenset[str]:
    return frozenset(t for t in _TOKEN.findall(text.lower()) if t not in _STOP)


def jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    return len(a & b) / max(1, len(a | b))


def cluster(rows: list[tuple[str, dict[str, Any]]], threshold: float) -> list[list[int]]:
    """Average-linkage clusters of one paragraph's rows; two rows of one run never share one."""
    n = len(rows)
    tk = [toks(r["text"]) for _, r in rows]
    sim = np.zeros((n, n))
    for a in range(n):
        for b in range(a + 1, n):
            sim[a, b] = sim[b, a] = jaccard(tk[a], tk[b])
    clusters = [[i] for i in range(n)]
    runs = [{rows[i][0]} for i in range(n)]
    while True:
        best, pair = threshold, None
        for a in range(len(clusters)):
            for b in range(a + 1, len(clusters)):
                if runs[a] & runs[b]:
                    continue
                v = float(sim[np.ix_(clusters[a], clusters[b])].mean())
                if v >= best:
                    best, pair = v, (a, b)
        if pair is None:
            return clusters
        a, b = pair
        clusters[a] += clusters[b]
        runs[a] |= runs[b]
        del clusters[b], runs[b]


def load(case: str, name: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((EXP / f"G-{case}-{name}.json").read_text())
    return data


def key(r: dict[str, Any]) -> tuple[str, str]:
    return r["source"]["regulation"], str(r["source"]["paragraph"])


def cmd_vote(args: argparse.Namespace) -> int:
    subs = {n: load(args.case, n) for n in args.runs}
    by_par: dict[tuple[str, str], list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    for n, s in subs.items():
        for r in s["requirements"]:
            by_par[key(r)].append((n, r))
    anchor = args.anchor or args.runs[0]
    kept: list[dict[str, Any]] = []
    n_par = 0
    for k in sorted(by_par):
        rows = by_par[k]
        votes = len({n for n, _ in rows})
        if votes < args.min:
            continue
        n_par += 1
        if args.rows == "anchor":  # paragraph vote; rows from the anchor run, else the most voted
            own = [r for n, r in rows if n == anchor]
            if not own:
                counts: dict[str, int] = defaultdict(int)
                for n, _ in rows:
                    counts[n] += 1
                best = max(counts, key=lambda n: (counts[n], -args.runs.index(n)))
                own = [r for n, r in rows if n == best]
            kept += own
        else:  # row clusters: keep a cluster written by at least --min-rows runs
            for c in cluster(rows, args.sim):
                if len(c) >= args.min_rows:
                    members = [rows[i][1] for i in c]
                    pick = max(members, key=lambda r: len(r.get("quote") or "") > 0)
                    rep = next((rows[i][1] for i in c if rows[i][0] == anchor), pick)
                    kept.append(rep)
    first = next(iter(subs.values()))
    out = {
        "team_id": first["team_id"],
        "case_id": first["case_id"],
        "requirements": [{**r, "id": f"R-{i:04d}"} for i, r in enumerate(kept, start=1)],
        "regulations": first.get("regulations", []),
        "profile": first.get("profile", {}),
        "vote": {"runs": args.runs, "min": args.min, "rows": args.rows, "anchor": anchor},
    }
    name = args.out or f"vote{args.min}-{args.rows}-{len(args.runs)}"
    (EXP / f"G-{args.case}-{name}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    n = len(args.runs)
    log(f"{name}: {n_par} paragraphs with >= {args.min} of {n} votes, {len(kept)} rows")
    return 0


# ---------- silver labels ----------


def silver() -> dict[tuple[str, str], bool]:
    out = {}
    for name in ("labels-r42-r26.csv", "labels-r127-gtr9.csv"):
        with (LABELS / name).open() as f:
            for r in csv.DictReader(f):
                if r["cited"] in ("y", "n") and r["paragraph"] != "(whole regulation)":
                    out[(r["regulation"], r["paragraph"])] = r["cited"] == "y"
    return out


def para_stats(sub: dict[str, Any], gold: dict[tuple[str, str], bool], regs: list[str]) -> str:
    cited = {k for k, v in gold.items() if v and k[0] in regs}
    rows = [r for r in sub["requirements"] if r["source"]["regulation"] in regs]
    pars = {key(r) for r in rows}
    labelled = {p for p in pars if p in gold}
    tp = len(labelled & cited)
    prec = tp / max(1, len(labelled))
    rec = tp / max(1, len(cited))
    f2 = 5 * prec * rec / max(1e-9, 4 * prec + rec)
    on_cited = sum(1 for r in rows if key(r) in cited)
    return (
        f"{len(pars):4d} par ({len(pars) - len(labelled)} unlabelled), {len(rows):4d} rows "
        f"({on_cited} on cited) | P {prec:.2f} R {rec:.2f} ({tp}/{len(cited)}) F2 {f2:.3f}"
    )


def cmd_labels(args: argparse.Namespace) -> int:
    gold = silver()
    for name in args.runs:
        sub = load(args.case, name)
        print(f"{name:28s} 4 regs  {para_stats(sub, gold, BUMPER_REGS)}")
        print(f"{'':28s} no GTR9 {para_stats(sub, gold, BUMPER_REGS[:3])}")
        sc = EXP / f"G-{args.case}-{name}-scores.json"
        if sc.exists():
            rec = json.loads(sc.read_text())
            ys, ps = [], []
            for p in rec["paragraphs"]:
                k = (p["regulation"], p["paragraph"])
                if k in gold and p["llm"] is not None:
                    ys.append(gold[k])
                    ps.append(p["llm"])
            if ys and any(ys) and not all(ys):
                from sklearn.metrics import roc_auc_score

                print(
                    f"{'':28s} LLM AUC {roc_auc_score(ys, ps):.3f} on {len(ys)} labelled; "
                    f"wall {rec['wall_s']:.0f} s {rec['timings_s']}; ${rec['spend_usd']:.3f}"
                )
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("case")
    r.add_argument("--name", required=True)
    r.add_argument("--rel-model", default="claude-haiku-5-5")
    r.add_argument("--rw-model", default="claude-haiku-5-5")
    r.add_argument("--rel-prompt", choices=["base", "alt"], default="base")
    r.add_argument("--rw-prompt", choices=["base", "verbatim"], default="base")
    r.add_argument("--seed", type=int, default=0)
    r.add_argument("--rel-batch", type=int, default=None)
    r.add_argument("--threshold", type=float, default=None)
    r.add_argument("--weight", type=float, default=None, help="LLM blend weight; default 0.7")
    r.add_argument("--include", nargs="*", default=[])
    r.add_argument("--exclude", nargs="*", default=[])
    r.add_argument("--only", nargs="*", default=[], help="exactly these regulations")
    v = sub.add_parser("vote")
    v.add_argument("case")
    v.add_argument("runs", nargs="+")
    v.add_argument("--min", type=int, default=2, help="paragraph votes to keep a paragraph")
    v.add_argument("--rows", choices=["anchor", "cluster"], default="anchor")
    v.add_argument("--min-rows", type=int, default=2, help="cluster votes to keep a row")
    v.add_argument("--sim", type=float, default=0.6)
    v.add_argument("--anchor")
    v.add_argument("--out")
    lab = sub.add_parser("labels")
    lab.add_argument("case")
    lab.add_argument("runs", nargs="+")
    args = ap.parse_args(argv)
    return {"run": cmd_run, "vote": cmd_vote, "labels": cmd_labels}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
