"""LLM path: drop written requirements an expert list would leave out.

Paragraph relevance decides which paragraphs are rewritten; inside a relevant paragraph some
requirements still concern categories the product lacks, the applicant's paperwork or test set-up.
The strong model scores each requirement; rows under THRESHOLD go. Offline on saved runs, 0.40
dropped 19 to 69 rows per lamp submission and lost at most one match: requirement F2 dev 0.643 ->
0.685, synth-a03 (held out) 0.566 -> 0.598. At 0.50 matched rows start to go.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor

from . import llm
from .rewrite import Draft

THRESHOLD = 0.40
BATCH = 30

_SYSTEM = """You are a type-approval engineer reviewing a draft requirement list for one
automotive component. Each draft requirement was rewritten from a UN Regulation paragraph that is
already known to be relevant to the product. An expert's final list keeps the requirements the
component itself (or the vehicle, because of the component) must meet, and drops the rest.

Experts usually drop a requirement when it:
- applies only to a device category, function, variant or vehicle category the product does not
  have (for example a requirement for a high-mounted stop lamp, a dipped-beam headlamp, a
  triangular retro-reflector or category N3 vehicles, when the product has none of these);
- is an obligation on the applicant, the manufacturer's paperwork, the approval authority or the
  communication form (what to submit, what to state in the application, what the authority
  records, approval numbering, extension, notification);
- describes test equipment, laboratory set-up or measurement procedure without setting a limit
  or criterion the component must meet;
- is a generic administrative or transitional clause (dates, "Contracting Parties shall",
  conformity-of-production sampling for inspectors).

Experts usually keep a requirement that sets a construction, performance, photometric,
colorimetric, dimensional, position, marking, durability or electrical/EMC requirement or test
limit for the product's own functions, including conditional ones ("Where ... is used, ...") that
could apply to this product.

When unsure, lean to keep: a missed requirement costs four times as much as an extra one."""

_SCHEMA = {
    "type": "object",
    "properties": {
        "keep": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "p_keep": {
                        "type": "number",
                        "description": "probability (0-1) that the expert list keeps it",
                    },
                },
                "required": ["id", "p_keep"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["keep"],
    "additionalProperties": False,
}


def _batch(chunk: list[tuple[str, Draft]], product: str) -> dict[str, float]:
    items = "\n".join(
        json.dumps(
            {
                "id": rid,
                "regulation": d.paragraph.regulation,
                "paragraph": d.paragraph.label,
                "text": d.text,
            },
            ensure_ascii=False,
        )
        for rid, d in chunk
    )
    prompt = (
        f"Product profile:\n{product}\n\nDraft requirements (JSON lines):\n{items}\n\n"
        "Return p_keep for every id."
    )
    data = llm.complete_json(_SYSTEM, prompt, _SCHEMA, tier="strong", effort="low")
    return {k["id"]: min(1.0, max(0.0, float(k["p_keep"]))) for k in data["keep"]}


def scores(drafts: list[Draft], product: str) -> list[float]:
    """p_keep per draft, in order. An id the model skips gets one more pass; any still unscored
    stops the run."""
    ids = [(f"r{i}", d) for i, d in enumerate(drafts)]
    _, workers = llm.batching(BATCH, BATCH, 8)
    out: dict[str, float] = {}
    todo = ids
    for _ in range(2):
        chunks = [todo[i : i + BATCH] for i in range(0, len(todo), BATCH)]
        with ThreadPoolExecutor(workers) as pool:
            for part in pool.map(lambda c: _batch(c, product), chunks):
                out |= part
        todo = [(rid, d) for rid, d in todo if rid not in out]
        if not todo:
            break
    if todo:
        raise RuntimeError(f"keep: {len(todo)} requirements unscored after a retry")
    return [out[rid] for rid, _ in ids]
