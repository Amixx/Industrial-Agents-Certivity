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
# 0.917), blend AUC 0.981. Weight 0.7 with cut-off 0.20 gives paragraph F2 0.75 at recall 0.94;
# F2 stays 0.73-0.76 between cut-offs 0.20 and 0.30. Tuned on the one dev case.
WEIGHT = 0.7
THRESHOLD = 0.20
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
    batch: int = 25,
    workers: int = 12,
    tier: llm.Tier | None = None,
) -> dict[str, float]:
    tier = tier or ("bulk" if os.environ.get("BRAIN_RELEVANCE_TIER") == "bulk" else "strong")
    product = profile.model_dump_json(
        include={"product", "vehicle_categories", "functions", "parts", "electronics"}
    )
    chunks = [paragraphs[i : i + batch] for i in range(0, len(paragraphs), batch)]

    def safe(chunk: list[Paragraph]) -> dict[str, float]:
        try:
            return _batch(chunk, graph, product, tier)
        except Exception as e:  # missing ids fall back to the decision model alone (`blend`)
            print(f"[relevance] batch failed ({e!r:.200}); model score only", file=sys.stderr)
            return {}

    with ThreadPoolExecutor(workers) as pool:
        out: dict[str, float] = {}
        for part in pool.map(safe, chunks):
            out |= part
    return out


def blend(model_p: float, llm_p: float | None, weight: float = WEIGHT) -> float:
    """Geometric blend of the decision model's and the LLM's probabilities."""
    if llm_p is None:
        return model_p
    return float(model_p ** (1 - weight) * max(llm_p, 1e-3) ** weight)


def floor(scores: list[tuple[Paragraph, float]], cut: float) -> set[str]:
    """Ids above `cut`, plus each regulation's top FLOOR share."""
    chosen = {p.id for p, s in scores if s >= cut}
    by_reg: dict[str, list[tuple[Paragraph, float]]] = {}
    for p, s in scores:
        by_reg.setdefault(p.regulation, []).append((p, s))
    for items in by_reg.values():
        k = max(FLOOR_MIN, int(FLOOR * len(items)))
        chosen.update(p.id for p, _ in sorted(items, key=lambda x: -x[1])[:k])
    return chosen
