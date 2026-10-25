"""LLM paragraph relevance: P(an expert lists a requirement from this paragraph for this product).

The decision model ranks paragraphs from generic features; this asks a model to read each
candidate with its heading path and the product profile. The pipeline blends the two scores
(see `blend`), so the run still works, deterministically, without an LLM.
"""

from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

from . import llm
from .graph import Graph
from .models import Paragraph, ProductProfile

# Dev, strong tier, domain-neutral prompt (eval/relevance_check.py): LLM AUC 0.975 (bulk tier
# 0.917), blend AUC 0.981; weight 0.7 with cut-off 0.20 gives paragraph F2 0.75 at recall 0.94.
# The decision model is fitted on the lamp and transfers poorly: on silver labels for a plain
# front bumper (data/bumper-labels) its AUC is 0.65 against 0.98 for the LLM, and paragraph
# recall there is 0.63 at weight 0.7 against 0.91 at 0.85. A higher weight floods the lamp's
# large regulations instead (estimated dev requirement F2 0.61 at 0.7, 0.54 at 0.85).
WEIGHT = 0.7
# Each regulation keeps the paragraphs whose blended score reaches RELATIVE times its best one,
# never below MIN_CUT. One absolute cut-off does not transfer: the lamp's large regulations have
# many paragraphs between 0.2 and 0.3, while on a front bumper the decision model pulls the
# impact-test paragraphs under 0.2, and GPT scores lower overall than Opus. Against absolute
# 0.20: dev lamp (Opus) estimated requirement F2 0.61 against 0.62; plain bumper paragraph F2 on
# the silver labels in data/bumper-labels 0.72 instead of 0.64 (Opus), 0.78 instead of 0.71 (GPT).
RELATIVE = 0.3
# The section stage makes the final cut; retain the Jev blend's recall at relative 0.20 here.
RELATIVE_JEV = 0.20
MIN_CUT = 0.10
# Keep at least the top FLOOR share (min FLOOR_MIN) of every selected regulation: no effect on
# dev, but a product unlike the lamp (low decision-model scores) still gets its core regulation.
FLOOR = 0.06
FLOOR_MIN = 5

_SYSTEM = """You are a type-approval engineer preparing the requirement list for one automotive
component. The list cites UN Regulation paragraphs that the component itself must fulfil, or that
the vehicle must fulfil because of the component. An expert list is selective: most paragraphs
of an applicable regulation are not cited. For each paragraph, estimate the probability that the
expert list cites it.

Usually cited:
- requirements on the component's construction, performance, dimensions, position, strength,
  durability, behaviour in a specified test, or markings, for the functions and parts the
  product actually has;
- vehicle-level requirements that the component determines (installation, position,
  visibility, behaviour after an impact or test), when the regulation approves the vehicle;
- general provisions that apply to every device or vehicle the regulation covers;
- limits the component must meet when tested (values, criteria), including in annexes;
- for electromagnetic compatibility, the requirements on electrical/electronic sub-assemblies.

Rarely cited:
- definitions, scope, administrative procedure (application, approval forms, communication,
  extension, production definitively discontinued, transitional provisions, names of services);
- paragraphs about devices, functions or vehicle categories the product does not have;
- laboratory set-up and test-equipment details that state no limit for the component;
- conformity-of-production sampling and tolerances for inspectors."""

_SCHEMA = {
    "type": "object",
    "properties": {
        "paragraphs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "p_cited": {
                        "type": "number",
                        "description": "probability (0-1) that the expert list cites it",
                    },
                },
                "required": ["id", "p_cited"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["paragraphs"],
    "additionalProperties": False,
}


def _heading_path(p: Paragraph, graph: Graph) -> str:
    names = []
    for pid in p.path:
        q = graph.paragraphs.get(pid)
        if q is not None:
            names.append(f"{q.label} {q.heading or q.text[:60]}")
    return " > ".join(names)


def _parent_text(p: Paragraph, graph: Graph) -> str:
    parent = graph.paragraphs.get(p.parent) if p.parent else None
    return parent.text[:300] if parent is not None else ""


def _batch(chunk: list[Paragraph], graph: Graph, product: str, tier: llm.Tier) -> dict[str, float]:
    listing = "\n".join(
        json.dumps(
            {
                "id": p.id,
                "label": f"{p.regulation} {p.label}",
                "heading_path": _heading_path(p, graph),
                "parent_text": _parent_text(p, graph),
                "text": p.text[:2500],
            },
            ensure_ascii=False,
        )
        for p in chunk
    )
    prompt = (
        f"Product profile:\n{product}\n\nParagraphs (JSON lines):\n{listing}\n\n"
        "Return p_cited for every paragraph id."
    )
    data = llm.complete_json(_SYSTEM, prompt, _SCHEMA, tier=tier, effort="low")
    ids = {p.id for p in chunk}
    return {
        d["id"]: min(1.0, max(0.0, float(d["p_cited"])))
        for d in data["paragraphs"]
        if d["id"] in ids
    }


def score(
    paragraphs: list[Paragraph],
    graph: Graph,
    profile: ProductProfile,
    batch: int | None = None,
    workers: int | None = None,
    tier: llm.Tier | None = None,
) -> dict[str, float]:
    tier = tier or ("bulk" if os.environ.get("BRAIN_RELEVANCE_TIER") == "bulk" else "strong")
    product = profile.model_dump_json(
        include={"product", "vehicle_categories", "functions", "parts", "electronics"}
    )
    size, n_workers = llm.batching(25, 8, 12)
    batch, workers = batch or size, workers or n_workers

    def safe(chunk: list[Paragraph]) -> dict[str, float]:
        try:
            return _batch(chunk, graph, product, tier)
        except Exception as e:
            print(f"[relevance] batch failed ({e!r:.200})", file=sys.stderr)
            return {}

    out: dict[str, float] = {}
    todo = paragraphs
    # A failed batch or a skipped id gets one more pass; anything still unscored stops the run,
    # because the decision model alone would quietly drop paragraphs on a product unlike the lamp.
    for _ in range(2):
        chunks = [todo[i : i + batch] for i in range(0, len(todo), batch)]
        with ThreadPoolExecutor(workers) as pool:
            for part in pool.map(safe, chunks):
                out |= part
        todo = [p for p in todo if p.id not in out]
        if not todo:
            return out
        print(f"[relevance] {len(todo)} paragraphs unscored, retrying", file=sys.stderr)
    regs = sorted({p.regulation for p in todo})
    raise RuntimeError(f"relevance: {len(todo)} paragraphs unscored after a retry, in {regs}")


def blend(model_p: float, llm_p: float | None, weight: float = WEIGHT) -> float:
    """Geometric blend of the decision model's and the LLM's probabilities."""
    if llm_p is None:
        return model_p
    return float(model_p ** (1 - weight) * max(llm_p, 1e-3) ** weight)


def bars(
    scores: list[tuple[Paragraph, float]], cut: float | None = None, relative: float = RELATIVE
) -> dict[str, float]:
    """Each regulation's cut-off in `select`: `relative` times its best score (at least MIN_CUT),
    or `cut` when one is given."""
    best: dict[str, float] = {}
    for p, s in scores:
        best[p.regulation] = max(s, best.get(p.regulation, s))
    return {r: cut if cut is not None else max(MIN_CUT, relative * b) for r, b in best.items()}


def select(
    scores: list[tuple[Paragraph, float]], cut: float | None = None, relative: float = RELATIVE
) -> set[str]:
    """Ids to keep: per regulation, scores at its cut-off from `bars`, plus its top FLOOR share."""
    by_reg: dict[str, list[tuple[Paragraph, float]]] = {}
    for p, s in scores:
        by_reg.setdefault(p.regulation, []).append((p, s))
    bar = bars(scores, cut, relative)
    chosen: set[str] = set()
    for reg, items in by_reg.items():
        ranked = sorted(items, key=lambda x: -x[1])
        chosen.update(p.id for p, s in ranked if s >= bar[reg])
        chosen.update(p.id for p, _ in ranked[: max(FLOOR_MIN, int(FLOOR * len(items)))])
    return chosen
