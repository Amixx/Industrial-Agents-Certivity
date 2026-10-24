"""Lane B: rank every candidate paragraph by relevance, rewrite all of them down to a low score.

    PYTHONPATH=. uv run python swing/b_recall.py rank                       # B1, cache only
    PYTHONPATH=. uv run python swing/b_recall.py plan --cut 0.03            # B2 dry run
    PYTHONPATH=. uv run python swing/b_recall.py run --cut 0.03 --approved \
        -o ../out/rear-lamp-swing-B-full.json                               # B2, paid

The selection is `brain.pipeline.select_paragraphs` without the cut: every paragraph keeps its
blended score (decision model and Opus relevance, `relevance.blend`). The paragraphs the pipeline
itself selects (cut 0.20 plus the floor) are rewritten first, in the pipeline's order and batches,
so those calls come from the cache; the rest follow in score order in new batches of 12.
`rank` and `plan` refuse any call that is not cached.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from brain import features as F
from brain import llm, relevance, rewrite
from brain.decide import MODEL_PATH, Model
from brain.graph import build
from brain.ingest import load_all
from brain.paths import CASES
from brain.profile import build_profile
from brain.select_regs import choose
from brain.verify import clean, validate

CASE = Path(os.environ.get("B_CASE", CASES / "dev-rear-lamp"))
SCORES = Path(__file__).resolve().parents[2] / "out" / "experiments" / "B-scores.json"
PRICE = {"claude-sonnet-5-5": (2, 10), "claude-opus-5-5": (4, 20)}

lock = threading.Lock()
stats: dict[str, Any] = defaultdict(int)
usage: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0, 0])  # calls, in, out, cache read
_orig = llm.complete_json


def _track_usage() -> None:
    """Count real API tokens per model, as swing/run_costed.py does."""
    import anthropic.resources.beta.messages as M

    orig = M.Messages.create

    def create(self: Any, **kw: Any) -> Any:
        r = orig(self, **kw)
        u = r.usage
        with lock:
            a = usage[kw["model"]]
            a[0] += 1
            a[1] += u.input_tokens + (u.cache_creation_input_tokens or 0)
            a[2] += u.output_tokens
            a[3] += u.cache_read_input_tokens or 0
        return r

    M.Messages.create = create  # type: ignore[method-assign]


def spend() -> float:
    total = 0.0
    for m, (c, i, o, cr) in usage.items():
        pin, pout = PRICE.get(m, (0, 0))
        cost = (i * pin + o * pout + cr * pin * 0.1) / 1e6
        total += cost
        print(
            f"[cost] {m}: {c} calls, {i:,} in / {o:,} out / {cr:,} cache read; ${cost:.2f}",
            file=sys.stderr,
        )
    print(f"[cost] total new spend ${total:.2f}", file=sys.stderr)
    return total


def guarded(mode: str):  # type: ignore[no-untyped-def]
    """complete_json that counts cache hits; in `rank`/`plan` mode a miss never calls the API:
    a strong-tier miss stops the run, a bulk-tier (rewrite) miss is counted and answered empty,
    so the rewrite falls back to its deterministic path."""

    def cj(system: str, content: Any, schema: Any, *, tier: str = "bulk", **kw: Any) -> Any:
        payload = {
            "provider": llm.provider(),
            "model": llm.model_for(tier),  # type: ignore[arg-type]
            "system": system,
            "content": content,
            "schema": schema,
            "effort": kw.get("effort", "medium"),
        }
        hit = llm._cache_path(payload).exists()
        with lock:
            stats[f"{tier} hit" if hit else f"{tier} miss"] += 1
            if not hit:
                stats[f"{tier} miss chars"] += len(system) + len(str(content))
        if not hit and mode != "run":
            if tier == "strong":
                raise RuntimeError("uncached strong-tier call in a cache-only mode")
            return {"paragraphs": []}
        return _orig(system, content, schema, tier=tier, **kw)  # type: ignore[arg-type]

    return cj


def scored_paragraphs() -> tuple[list[tuple[Any, float, float | None, float]], set[str], Any, str]:
    """Every candidate paragraph with (blend, llm, model) scores, the ids the pipeline selects,
    the graph and the product string, exactly as brain.pipeline.run computes them."""
    spec = (CASE / "spec.md").read_text()
    image = CASE / "exploded_view.png"
    corpus = load_all("base")
    profile = build_profile(spec, image if image.exists() else None, use_llm=True)
    choices = choose(profile, corpus, use_llm=True)
    regs = [c.regulation for c in choices if c.selected]
    sub = {r: corpus[r] for r in regs}
    graph = build(sub, set(corpus))
    ctx = F.build_context(profile, sub, graph, {c.regulation: c.probability for c in choices})
    paragraphs = [
        p
        for r in regs
        for p in sub[r]
        if p.number and p.label != "preamble" and not p.label.startswith("Rationale")
    ]
    model = Model.load(MODEL_PATH)
    probs = model.predict(F.matrix(paragraphs, ctx))
    llm_p = relevance.score(paragraphs, graph, profile)
    rows = [
        (p, relevance.blend(float(a), llm_p.get(p.id)), llm_p.get(p.id), float(a))
        for p, a in zip(paragraphs, probs, strict=True)
    ]
    keep = relevance.floor([(p, b) for p, b, _, _ in rows], relevance.THRESHOLD)
    return rows, keep, graph, profile.product


def gold_labels() -> dict[tuple[str, str], int]:
    exp = json.loads((CASE / "expected.json").read_text())["requirements"]
    out: dict[tuple[str, str], int] = defaultdict(int)
    for r in exp:
        out[(r["source"]["regulation"], r["source"]["paragraph"])] += 1
    return out


BUCKETS = [1.0, 0.5, 0.3, 0.2, 0.15, 0.1, 0.07, 0.05, 0.03, 0.02, 0.01, 0.0]


def rank(rows: list[tuple[Any, float, float | None, float]], keep: set[str]) -> None:
    gold = gold_labels()
    rows = sorted(rows, key=lambda r: -r[1])
    SCORES.write_text(
        json.dumps(
            [
                {
                    "id": p.id,
                    "regulation": p.regulation,
                    "paragraph": p.label,
                    "page": p.page,
                    "blend": round(b, 4),
                    "llm": lp,
                    "model": round(m, 4),
                    "pipeline_selects": p.id in keep,
                    "gold_rows": gold.get((p.regulation, p.label), 0),
                }
                for p, b, lp, m in rows
            ],
            indent=0,
        )
    )
    print(f"{len(rows)} candidate paragraphs; pipeline selects {len(keep)}; wrote {SCORES}")
    print(
        f"{'blend in':>14s} {'paras':>6s} {'cum':>6s} {'gold p':>7s} {'cum gp':>7s} "
        f"{'gold rows':>9s} {'cum gr':>7s}"
    )
    cum = cum_gp = cum_gr = 0
    for hi, lo in zip(BUCKETS, BUCKETS[1:], strict=False):
        b = [r for r in rows if lo <= r[1] < hi or (hi == 1.0 and r[1] >= lo)]
        gp = sum(1 for p, *_ in b if gold.get((p.regulation, p.label)))
        gr = sum(gold.get((p.regulation, p.label), 0) for p, *_ in b)
        cum, cum_gp, cum_gr = cum + len(b), cum_gp + gp, cum_gr + gr
        print(f"[{lo:.2f}, {hi:.2f}) {len(b):6d} {cum:6d} {gp:7d} {cum_gp:7d} {gr:9d} {cum_gr:7d}")
    corpus_labels = {(p.regulation, p.label) for p, *_ in rows}
    missing = sum(n for k, n in gold.items() if k not in corpus_labels)
    print(f"gold rows on labels that are not candidates: {missing}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mode", choices=["rank", "plan", "run"])
    ap.add_argument("--cut", type=float, default=0.03)
    ap.add_argument("-o", "--out")
    ap.add_argument("--team-id", default="team-06")
    ap.add_argument("--approved", action="store_true", help="the paid run was approved")
    args = ap.parse_args(argv)
    if args.mode == "run" and not args.approved:
        ap.error("run makes paid calls; pass --approved after the plan's estimate was approved")
    os.environ["BRAIN_LLM"] = "anthropic"
    _track_usage()
    llm.complete_json = guarded(args.mode)
    rewrite.llm.complete_json = llm.complete_json  # same module object; explicit for clarity

    rows, keep, graph, product = scored_paragraphs()
    if args.mode == "rank":
        rank(rows, keep)
        print(dict(stats), file=sys.stderr)
        return 0

    by_id = {p.id: (p, b) for p, b, _, _ in rows}
    core = [p for p, *_ in rows if p.id in keep]  # pipeline order: its batches are cached
    tail = sorted(
        (r for r in rows if r[0].id not in keep and r[1] >= args.cut), key=lambda r: -r[1]
    )
    tail_p = [p for p, *_ in tail]
    print(
        f"core {len(core)} paragraphs (pipeline selection), tail {len(tail_p)} at blend >= "
        f"{args.cut}",
        file=sys.stderr,
    )
    t0 = time.time()
    drafts = rewrite.with_llm(core, graph, product) + rewrite.with_llm(tail_p, graph, product)
    kept, dropped = clean(drafts, graph.paragraphs)
    secs = time.time() - t0
    miss = stats.get("bulk miss", 0)
    chars = stats.get("bulk miss chars", 0)
    # About 3.5 characters per token; output was 0.5 to 1 times the paragraph input on the lamp.
    tok_in = chars / 3.5
    tok_out = 0.8 * (tok_in - miss * 2500)
    pin, pout = PRICE[llm.model_for("bulk")]
    est = (tok_in * pin + tok_out * pout) / 1e6
    print(
        f"rewrite batches: {stats.get('bulk hit', 0)} cached, {miss} new "
        f"(~{tok_in / 1e3:.0f}k in, ~{tok_out / 1e3:.0f}k out, ~${est:.2f} at list price); "
        f"drafts {len(drafts)}, kept {len(kept)}, dropped {len(dropped)}, {secs:.0f}s",
        file=sys.stderr,
    )
    spend()
    if args.mode == "plan":
        return 0
    reqs = []
    for i, d in enumerate(kept, 1):
        p = d.paragraph
        reqs.append(
            {
                "id": f"R-{i:04d}",
                "text": d.text,
                "source": {
                    "regulation": p.regulation,
                    "version": p.version,
                    "page": p.page,
                    "paragraph": p.label,
                },
                "confidence": round(by_id[p.id][1], 4),
                "quote": d.quote[:1000],
            }
        )
    sub = {"team_id": args.team_id, "case_id": CASE.name, "requirements": reqs}
    problems = validate(sub)
    if problems:
        raise SystemExit("validate.py: " + "; ".join(problems[:10]))
    out = Path(args.out or f"../out/rear-lamp-swing-B-full-{args.cut}.json")
    out.write_text(json.dumps(sub, indent=1, ensure_ascii=False))
    print(f"wrote {out} ({len(reqs)} rows)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
