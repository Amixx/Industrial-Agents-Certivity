"""Lane H runs 2 and 3. Paid. Refuses to start without --approved.

    PYTHONPATH=. uv run python swing/h_run.py sonnet --approved
    PYTHONPATH=. uv run python swing/h_run.py haiku --approved --already 3.36

Profile and regulation review stay on the cached Opus answers. Relevance uses the named
model. The blend weight is 0.85. The rewrite is main's Sonnet prompt. Stops before the
rewrite if the spend so far, plus about $0.0032 per selected paragraph, would pass
--max-dollars (default $6, the planned cap) together with --already.
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
from swing.h_dry import blend, selected

ROOT = Path(__file__).resolve().parents[2]
CASE = CASES / "dev-rear-lamp"
PRICE = {
    "claude-opus-5-5": (4.0, 20.0, 0.2),
    "claude-sonnet-5-5": (2.0, 10.0, 0.2),
    "claude-haiku-5-5": (0.1, 0.5, 0.01),
}
REWRITE_PER_PARAGRAPH = 0.854436 / 267
NAMES = {
    "sonnet": ("claude-sonnet-5-5", "rear-lamp-swing-H-sonnet-w85"),
    "haiku": ("claude-haiku-5-5", "rear-lamp-swing-H-haiku-rel"),
}

usage: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0, 0])
hits: dict[str, int] = defaultdict(int)
lock = threading.Lock()


def log(msg: str) -> None:
    print(f"[h {time.strftime('%H:%M:%S')}] {msg}", file=sys.stderr, flush=True)


def spend() -> float:
    total = 0.0
    for model, (calls, inp, out, cache_read) in usage.items():
        pi, po, pc = PRICE.get(model, (0.0, 0.0, 0.0))
        cost = (inp * pi + out * po + cache_read * pc) / 1e6
        total += cost
        log(
            f"{model}: {calls} new calls, {inp:,} in / {out:,} out / "
            f"{cache_read:,} cache read; ${cost:.3f}"
        )
    for model, n in hits.items():
        log(f"{model}: {n} cache hits")
    log(f"new spend ${total:.3f}")
    return total


def install_meter() -> None:
    import anthropic.resources.beta.messages as M

    orig_create = M.Messages.create

    def create(self: Any, **kw: Any) -> Any:
        if str(kw.get("model", "")).startswith("claude-haiku"):
            kw.pop("fallbacks", None)
            kw["betas"] = [b for b in kw.get("betas", []) if "fallback" not in b]
        response = orig_create(self, **kw)
        u = response.usage
        with lock:
            row = usage[kw["model"]]
            row[0] += 1
            row[1] += u.input_tokens + (u.cache_creation_input_tokens or 0)
            row[2] += u.output_tokens
            row[3] += u.cache_read_input_tokens or 0
        return response

    M.Messages.create = create  # type: ignore[method-assign]
    orig_cj = llm.complete_json

    def cj(system: str, content: Any, schema: Any, *, tier: str = "bulk", **kw: Any) -> Any:
        model = llm.model_for(tier)  # type: ignore[arg-type]
        payload = {
            "provider": llm.provider(),
            "model": model,
            "system": system,
            "content": content,
            "schema": schema,
            "effort": kw.get("effort", "medium"),
        }
        if llm._cache_path(payload).exists():
            with lock:
                hits[model] += 1
        return orig_cj(system, content, schema, tier=tier, **kw)  # type: ignore[arg-type]

    llm.complete_json = cj  # type: ignore[assignment]


def candidates(
    profile: Any, corpus: dict[str, list[Any]], choices: list[Any]
) -> tuple[Any, list[Any], list[float]]:
    regs = [c.regulation for c in choices if c.selected]
    sub = {r: corpus[r] for r in regs}
    graph = build(sub, set(corpus))
    paragraphs = [
        p
        for r in regs
        for p in sub[r]
        if p.number and p.label != "preamble" and not p.label.startswith("Rationale")
    ]
    ctx = F.build_context(profile, sub, graph, {c.regulation: c.probability for c in choices})
    model_p = [float(x) for x in Model.load(MODEL_PATH).predict(F.matrix(paragraphs, ctx))]
    return graph, paragraphs, model_p


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("which", choices=sorted(NAMES))
    ap.add_argument("--approved", action="store_true")
    ap.add_argument("--already", type=float, default=0.0, help="dollars already spent by this lane")
    ap.add_argument("--max-dollars", type=float, default=6.0)
    args = ap.parse_args(argv)
    if not args.approved:
        ap.error("this makes paid calls; pass --approved after the dry-run estimate was accepted")
    os.environ["BRAIN_LLM"] = "anthropic"
    os.environ["BRAIN_MODEL_STRONG"] = "claude-opus-5-5"
    os.environ["BRAIN_MODEL_BULK"] = "claude-sonnet-5-5"
    install_meter()

    rel_model, stem = NAMES[args.which]
    spec = (CASE / "spec.md").read_text()
    image = CASE / "exploded_view.png"
    t0 = time.time()
    profile = build_profile(spec, image if image.exists() else None, use_llm=True)
    corpus = load_all("base")
    choices = choose(profile, corpus, use_llm=True)
    graph, paragraphs, model_p = candidates(profile, corpus, choices)
    log(f"{len(paragraphs)} candidates; relevance model {rel_model}; blend weight 0.85")

    os.environ["BRAIN_MODEL_STRONG"] = rel_model
    llm_p = relevance.score(paragraphs, graph, profile)
    os.environ["BRAIN_MODEL_STRONG"] = "claude-opus-5-5"
    if len(llm_p) < len(paragraphs):
        log(f"relevance scored {len(llm_p)} of {len(paragraphs)}")
    kept = selected(paragraphs, model_p, llm_p, 0.85)
    scored = {
        p.id: blend(m, llm_p.get(p.id), 0.85) for p, m in zip(paragraphs, model_p, strict=True)
    }
    so_far = spend()
    rewrite_est = REWRITE_PER_PARAGRAPH * len(kept)
    log(
        f"selected {len(kept)} paragraphs; rewrite estimate ${rewrite_est:.2f}; "
        f"lane total if it lands ${args.already + so_far + rewrite_est:.2f}"
    )
    if args.already + so_far + rewrite_est > args.max_dollars:
        log("stopping before the rewrite: the estimate passes the cap")
        return 2

    drafts = rewrite.with_llm(kept, graph, profile.product)
    kept_d, dropped = clean(drafts, graph.paragraphs)
    log(f"requirements: {len(kept_d)} kept, {len(dropped)} dropped")
    requirements = []
    for i, d in enumerate(kept_d, start=1):
        p = d.paragraph
        requirements.append(
            {
                "id": f"R-{i:04d}",
                "text": d.text,
                "source": {
                    "regulation": p.regulation,
                    "version": p.version,
                    "page": p.page,
                    "paragraph": p.label,
                },
                "confidence": round(scored.get(p.id, 0.0), 3),
                "quote": d.quote[:1000],
            }
        )
    submission = {
        "team_id": "team-06",
        "case_id": CASE.name,
        "requirements": requirements,
        "regulations": [c.model_dump() for c in choices if c.selected]
        + [c.model_dump() for c in choices if not c.selected][:10],
        "profile": profile.model_dump(),
    }
    problems = validate(submission)
    out = ROOT / "out" / f"{stem}.json"
    out.write_text(json.dumps(submission, indent=1, ensure_ascii=False) + "\n")
    total = spend()
    wall = time.time() - t0
    lines = [
        f"lane H {args.which}: relevance {rel_model}, blend 0.85, Sonnet rewrite, main's prompt",
        f"paragraphs selected {len(kept)}, rows {len(requirements)}, dropped {len(dropped)}",
        f"wall {wall:.0f}s, new spend ${total:.3f}, already ${args.already:.3f}, "
        f"lane ${args.already + total:.3f}",
        f"wrote {out}",
    ]
    if problems:
        lines.append("validate: " + "; ".join(problems[:8]))
    (out.with_suffix(".log")).write_text("\n".join(lines) + "\n")
    log(f"wrote {out} in {wall:.0f}s")
    if problems:
        log("validate failed: " + "; ".join(problems[:5]))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
