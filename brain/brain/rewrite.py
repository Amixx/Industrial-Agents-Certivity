"""Selected paragraphs -> atomic requirements in minimal-edit EARS style.

Deterministic path (always available):
  * one requirement per sentence that states a constraint (modal verb, or numbers with units);
  * "However, ..." sentences fold into the previous one as "..., except that ...";
  * telegraphic lines ("In height: not less than 250 mm ...") get the subject from the heading
    path: "The reversing lamp shall be not less than 250 mm ...".
LLM path: a model rewrites each paragraph into standalone EARS obligations, keeping numbers,
units, references and passive voice verbatim (few-shot examples in the style of the gold).
Every requirement keeps the verbatim source sentence as `quote`.
"""

from __future__ import annotations

import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from . import llm
from .features import UNITS
from .graph import Graph
from .models import Paragraph
from .obligations import condition, modality, sentences

TELEGRAPHIC = re.compile(r"^(?:In\s+)?([A-Z][\w\s/,()-]{1,60}?):\s+(.+)$")
HOWEVER = re.compile(r"^However,?\s+(.*)$", re.I)
GENERIC = re.compile(
    r"^(general|definitions?|specifications?|requirements?|measurement|"
    r"colour|failure provisions|additional|number|position|arrangement|"
    r"geometric visibility|orientation|electrical connections|tell-tale|"
    r"other requirements|presence|in width|in height|in length)\b",
    re.I,
)


@dataclass
class Draft:
    paragraph: Paragraph
    text: str
    quote: str


def subject(p: Paragraph, graph: Graph) -> str | None:
    """Nearest heading above the paragraph that names a thing: "Reversing lamp"."""
    for pid in [p.id, *reversed(p.path)]:
        q = graph.paragraphs.get(pid)
        if q is None:
            continue
        title = q.heading or (q.text if len(q.text) < 80 and modality(q.text) == "other" else None)
        if not title:
            continue
        title = re.sub(r"\s*\([^)]*\)", "", title).rstrip(":. ").strip()
        if title and not GENERIC.match(title) and len(title.split()) <= 8:
            return title[0].lower() + title[1:] if not title[:2].isupper() else title
    return None


def deterministic(p: Paragraph, graph: Graph) -> list[Draft]:
    body = p.text
    if p.heading and body.startswith(p.heading):
        body = body[len(p.heading) :].strip()
    subj = subject(p, graph)
    drafts: list[Draft] = []
    for _, sent in sentences(body):
        sent = re.sub(r"^\(?[a-z]\)\s+", "", sent).strip()
        if len(sent) < 12:
            continue
        if (m := HOWEVER.match(sent)) and drafts:
            prev = drafts[-1]
            prev.text = prev.text.rstrip(". ") + ", except that " + m[1]
            prev.quote += " " + sent
            continue
        mod = modality(sent)
        if mod in ("shall", "shall not", "must", "must not"):
            drafts.append(Draft(p, sent, sent))
        elif (t := TELEGRAPHIC.match(sent)) and subj and (UNITS.search(sent) or len(sent) < 160):
            aspect, rest = t[1].strip(), t[2].strip()
            drafts.append(Draft(p, f"The {subj} shall be {rest} ({aspect.lower()})", sent))
        elif mod == "may" and UNITS.search(sent):
            drafts.append(Draft(p, sent, sent))
        elif UNITS.search(sent) and subj and len(sent) < 200 and not drafts:
            drafts.append(Draft(p, f"The {subj} shall meet: {sent}", sent))
    if not drafts and p.heading and subj and UNITS.search(body):
        drafts.append(Draft(p, f"The {subj} shall meet: {body[:400]}", body[:400]))
    for d in drafts:
        if not d.text.endswith("."):
            d.text += "."
    return drafts


_SYSTEM = """You turn paragraphs of UN Regulations into engineering requirements for a product.
Write one requirement per obligation, in minimal-edit EARS style:
- "The <subject> shall <constraint>." or, with a condition first, "When/While/Where/If <condition>,
  the <subject> shall <constraint>."
- Name the subject explicitly from the heading path (e.g. "The reversing lamp", "The stop lamp",
  "The retro-reflective device"); never use pronouns.
- Keep numbers, units, tolerances, table and paragraph references, and passive voice verbatim.
- Turn telegraphic provisions into shall-statements ("In height: not less than 250 mm" ->
  "The reversing lamp shall be not less than 250 mm ... above the ground").
- When the paragraph completes its parent's clause (parent_text ends with ":" or "the
  following"), carry the parent's condition into each requirement.
- Fold "However, ..." exceptions into the same requirement as "..., except that ...".
- Split a paragraph with several obligations into several requirements; do not merge.
- Skip pure definitions, permissions with no constraint, and text that is not an obligation.
Return an empty list for a paragraph with no obligation."""

_EXAMPLES = """Examples (paragraph -> requirements):

[UN R48 6.4.4.2, heading path: Reversing lamp > Position] "In height: not less than 250 mm and
not more than 1,200 mm above the ground. For category N2G, N3G, M2G, M3G (off-road) vehicles the
maximum height may be increased to 1,400 mm."
-> "The reversing lamp shall be not less than 250 mm and not more than 1,200 mm above the ground,
except that for category N2G, N3G, M2G, M3G (off-road) vehicles the maximum height may be
increased to 1,400 mm."

[UN R42 6.1.4, parent_text: "After each impact test made in accordance with the conditions and
procedure specified in annex 3 to this Regulation, the vehicle shall meet the following
requirements:"]
"The vehicle's exhaust system shall not suffer any damage or displacement which would prevent its
normal function."
-> "After each impact test made in accordance with the conditions and procedure specified in
annex 3 to this Regulation, the vehicle's exhaust system shall not suffer any damage or
displacement which would prevent its normal function."

[UN R48 5.7.1] "Lamps may be grouped, combined or reciprocally incorporated with one another
provided that all requirements regarding colour, position, orientation, geometric visibility,
electrical connections and other requirements, if any, are fulfilled."
-> "While lamps are grouped, combined or reciprocally incorporated with one another, the lamps
shall fulfill all requirements regarding colour, position, orientation, geometric visibility,
electrical connections and other requirements, if any."

[UN R150 4.1.1] "Retro-reflective devices shall be so constructed that they function
satisfactorily and will continue to do so in normal use. In addition, they shall not have any
defect in design or manufacture that is detrimental to their efficient operation or to their
maintenance in good condition."
-> "The retro-reflective devices shall be so constructed that they function satisfactorily and
will continue to do so in normal use."
-> "The retro-reflective devices shall not have any defect in design or manufacture that is
detrimental to their efficient operation or to their maintenance in good condition."
"""

_SCHEMA = {
    "type": "object",
    "properties": {
        "paragraphs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "requirements": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"text": {"type": "string"}, "quote": {"type": "string"}},
                            "required": ["text", "quote"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["id", "requirements"],
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
    """The parent's full clause: it often carries the condition ("After each impact test made in
    accordance with ... annex 3, ...:") that each child item completes."""
    parent = graph.paragraphs.get(p.parent) if p.parent else None
    return parent.text[:600] if parent is not None else ""


def _batch(chunk: list[Paragraph], graph: Graph, product: str) -> list[Draft]:
    listing = "\n\n".join(
        json.dumps(
            {
                "id": p.id,
                "label": f"{p.regulation} {p.label}",
                "heading_path": _heading_path(p, graph),
                "parent_text": _parent_text(p, graph),
                "text": p.text[:4000],
            }
        )
        for p in chunk
    )
    prompt = (
        f"{_EXAMPLES}\nProduct: {product}\n\nParagraphs (JSON lines):\n\n{listing}\n\n"
        "Return requirements for every paragraph id. `quote` is the source sentence."
    )
    data = llm.complete_json(_SYSTEM, prompt, _SCHEMA, tier="bulk")
    by_id = {p.id: p for p in chunk}
    out = []
    for item in data["paragraphs"]:
        p = by_id.get(item["id"])
        if p is None:
            continue
        for r in item["requirements"]:
            text = r["text"].strip()
            if text:
                out.append(Draft(p, text, r.get("quote", "").strip()))
    return out


def with_llm(
    paragraphs: list[Paragraph],
    graph: Graph,
    product: str,
    batch: int | None = None,
    workers: int | None = None,
) -> list[Draft]:
    size, n_workers = llm.batching(12, 4, 16)
    batch, workers = batch or size, workers or n_workers
    chunks = [paragraphs[i : i + batch] for i in range(0, len(paragraphs), batch)]

    def safe(chunk: list[Paragraph]) -> list[Draft]:
        try:
            return _batch(chunk, graph, product)
        except Exception as e:  # one failed batch must not cost the submission
            print(f"[rewrite] batch failed ({e!r:.200}); deterministic fallback", file=sys.stderr)
            return [d for p in chunk for d in deterministic(p, graph)]

    with ThreadPoolExecutor(workers) as pool:
        return [d for drafts in pool.map(safe, chunks) for d in drafts]


def rewrite(
    paragraphs: list[Paragraph], graph: Graph, product: str, use_llm: bool | None = None
) -> list[Draft]:
    if use_llm is False or (use_llm is None and not llm.available()):
        return [d for p in paragraphs for d in deterministic(p, graph)]
    return with_llm(paragraphs, graph, product)


def condition_type(text: str) -> str:
    return condition(text)[0]
