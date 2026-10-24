"""Spec (+ exploded view) -> main-goal submission JSON.

    uv run python -m brain.pipeline ../cases/dev-rear-lamp -o out/dev-rear-lamp.json
    uv run python -m brain.pipeline ../cases/heldout-front-bumper --team-id team-07 --no-llm

Steps: profile -> regulation selection -> graph -> decision model over paragraphs -> rewrite
-> verify. Extra fields (confidence, quote, rationale) are allowed by the format and feed the UI.
`run(spec, image)` is the entry point for the backend.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from . import features as F
from . import jev, llm, relevance
from .decide import MODEL_PATH, Model
from .graph import build
from .ingest import load_all
from .models import Paragraph, ProductProfile, RegulationChoice
from .paths import CORPUS
from .profile import build_profile
from .rewrite import rewrite
from .select_regs import choose
from .verify import clean, validate


def log(msg: str) -> None:
    print(f"[brain {time.strftime('%H:%M:%S')}] {msg}", file=sys.stderr)


def select_paragraphs(
    profile: ProductProfile,
    corpus: dict[str, list[Paragraph]],
    choices: list[RegulationChoice],
    threshold: float | None = None,
    use_llm: bool = False,
) -> tuple[list[tuple[Paragraph, float]], Any]:
    """Paragraphs to rewrite, with P(cited). With an LLM, its relevance score is blended in
    (paragraph F2 on dev 0.39 -> 0.73, see eval/relevance_check.py)."""
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
    probs: Any = model.predict(F.matrix(paragraphs, ctx)) if paragraphs else []
    if jev.enabled() and paragraphs:
        jev_p = jev.score(paragraphs, graph, profile)
        probs = [jev_p[p.id] for p in paragraphs]
    cut = model.threshold
    if use_llm and paragraphs:
        llm_p = relevance.score(paragraphs, graph, profile)
        probs = [
            relevance.blend(float(a), llm_p.get(p.id))
            for p, a in zip(paragraphs, probs, strict=True)
        ]
        scored = list(zip(paragraphs, map(float, probs), strict=True))
        keep = relevance.select(scored, threshold)
        return [(p, pr) for p, pr in scored if p.id in keep], graph
    cut = cut if threshold is None else threshold
    chosen = [(p, float(pr)) for p, pr in zip(paragraphs, probs, strict=True) if pr >= cut]
    return chosen, graph


def review(
    choices: list[RegulationChoice],
    include: Sequence[str] = (),
    exclude: Sequence[str] = (),
) -> list[RegulationChoice]:
    """The human review gate: force regulations in or out (Sunday hybrid mode)."""
    known = {c.regulation for c in choices}
    unknown = sorted((set(include) | set(exclude)) - known)
    if unknown:
        raise ValueError(f"unknown regulation ids {unknown}; use ids like 'UN R42', 'UN GTR 9'")
    if conflict := sorted(set(include) & set(exclude)):
        raise ValueError(f"regulations both included and excluded: {conflict}")
    out = []
    for c in choices:
        if c.regulation in include and not c.selected:
            c = c.model_copy(
                update={"selected": True, "rationale": c.rationale + "; added by review"}
            )
        elif c.regulation in exclude and c.selected:
            c = c.model_copy(
                update={"selected": False, "rationale": c.rationale + "; removed by review"}
            )
        out.append(c)
    return out


def run(
    spec: str,
    image: Path | None = None,
    *,
    case_id: str = "web",
    team_id: str = "team-00",
    use_llm: bool | None = None,
    threshold: float | None = None,
    include: Sequence[str] = (),
    exclude: Sequence[str] = (),
) -> dict[str, Any]:  # type: ignore[assignment]
    started, spent = time.monotonic(), llm.usage()
    if not any(CORPUS.glob("*_base.jsonl")):
        from .ingest import main as ingest_main

        ingest_main(["--role", "base"])
    corpus = load_all("base")
    use_llm = llm.available() if use_llm is None else use_llm
    profile = build_profile(spec, image, use_llm=use_llm)
    log(
        f"profile: {profile.product}; {len(profile.keywords)} terms; electronics="
        f"{profile.electronics}"
    )
    choices = review(choose(profile, corpus, use_llm=use_llm), include, exclude)
    log(
        "regulations: "
        + ", ".join(f"{c.regulation} {c.probability:.2f}" for c in choices if c.selected)
    )
    chosen, graph = select_paragraphs(profile, corpus, choices, threshold, use_llm)
    log(f"paragraphs selected: {len(chosen)}")
    confidence = {p.id: pr for p, pr in chosen}
    product = profile.model_dump_json(
        include={"product", "vehicle_categories", "functions", "parts"}
    )
    drafts = rewrite([p for p, _ in chosen], graph, product, use_llm=use_llm)
    kept, dropped = clean(drafts, graph.paragraphs)
    log(f"requirements: {len(kept)} kept, {len(dropped)} dropped")
    requirements = []
    for i, d in enumerate(kept, start=1):
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
                "confidence": round(confidence.get(p.id, 0.0), 3),
                "quote": d.quote[:1000],
            }
        )
        if d.atomic:
            requirements[-1]["atomic"] = d.atomic
    submission = {
        "team_id": team_id,
        "case_id": case_id,
        "requirements": requirements,
        # Every selected regulation, then the strongest rejected ones for the UI.
        "regulations": [c.model_dump() for c in choices if c.selected]
        + [c.model_dump() for c in choices if not c.selected][:10],
        "profile": profile.model_dump(),
        "run": {
            "wall_s": round(time.monotonic() - started, 1),
            "provider": llm.provider(),
            **llm.usage_since(spent),
        },
    }
    problems = validate(submission)
    if problems:
        raise ValueError("submission fails validate.py:\n" + "\n".join(problems[:20]))
    return submission


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run the brain on a case folder.")
    ap.add_argument("case", help="folder with spec.md and optionally exploded_view.png")
    ap.add_argument("-o", "--out")
    ap.add_argument("--team-id", default="team-00")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--threshold", type=float)
    ap.add_argument("--include", nargs="*", default=[], help="force regulations in, e.g. 'UN R42'")
    ap.add_argument("--exclude", nargs="*", default=[], help="force regulations out")
    args = ap.parse_args(argv)
    case = Path(args.case)
    image = case / "exploded_view.png"
    submission = run(
        (case / "spec.md").read_text(),
        image if image.exists() else None,
        case_id=case.name,
        team_id=args.team_id,
        use_llm=False if args.no_llm else None,
        threshold=args.threshold,
        include=args.include,
        exclude=args.exclude,
    )
    out = Path(args.out) if args.out else Path("out") / f"{case.name}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(submission, indent=1, ensure_ascii=False))
    r = submission["run"]
    log(
        f"wrote {out} ({len(submission['requirements'])} requirements); {r['wall_s']}s, "
        f"{r['calls']} LLM calls + {r['cache_hits']} cached, ${r['cost_usd']:.2f} "
        f"(${r['cold_cost_usd']:.2f} with a cold cache)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
