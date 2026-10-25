"""LLM path: score the cited paragraphs of each section side by side and cut weak requirements.

The requirement filter judges one requirement at a time; here the strong model sees every
paragraph the kept requirements cite in one section of a regulation together, and gives each a
probability that an expert's list for the product cites it. A requirement goes when
p_keep * p_section < THRESHOLD, with no separate filter on p_keep. On cached scores this keeps
the dev estimate (0.694) and raises paragraph F2 on the bumper silver labels from 0.777 to 0.798
(plain) and 0.613 to 0.718 (sensors-fog) against filter 0.40 plus 0.2. A square root on
p_section with a higher threshold scores better on dev but cuts the test-procedure annexes the
bumper labels cite.
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import llm
from .graph import Graph
from .models import Paragraph
from .rewrite import Draft

ENABLED = True
THRESHOLD = 0.15
MAX_SECTION = 25  # a top-level section with more cited paragraphs is split into subsections
MAX_CHUNK = 20  # consecutive subsections are merged up to this many paragraphs
TEXT_CHARS = 700

_SYSTEM = """You are a type-approval engineer preparing the requirement list for one automotive
component. You see the paragraphs of one section of a UN Regulation that a first pass marked as
possibly relevant, together, in document order. For each paragraph give the probability that an
expert's final requirement list for this component cites it: the expert cites the paragraphs
whose requirements an engineer designing or testing this component has to meet, and leaves out
the rest of the section."""

_SCHEMA = {
    "type": "object",
    "properties": {
        "paragraphs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"label": {"type": "string"}, "p": {"type": "number"}},
                "required": ["label", "p"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["paragraphs"],
    "additionalProperties": False,
}


def _key(label: str) -> str:
    """Label key: "Annex 3, 1.2." and "annex 3 1.2" match; dots inside a number stay."""
    text = re.sub(r"[,;:()\[\]]", " ", label.casefold())
    text = re.sub(r"(?<![0-9a-z])\.|\.(?![0-9a-z])", " ", text)
    return " ".join(text.split())


def _section(p: Paragraph, depth: int) -> str:
    """Section of 5.1.3: "5" at depth 1, "5.1" at depth 2. Anything in Annex 3 is "annex 3"."""
    key = _key(p.label)
    if key.startswith("annex"):
        return " ".join(key.split()[:2])
    return ".".join(key.split(".")[:depth])


def _order(name: str) -> list[int]:
    return [int(x) if x.isdigit() else 0 for x in name.replace(" ", ".").split(".")]


def groups(paragraphs: Sequence[Paragraph]) -> dict[tuple[str, str], list[Paragraph]]:
    """(regulation, section name) -> paragraphs. Groups are top-level sections (annexes by
    annex number); one with more than MAX_SECTION paragraphs is split into its second-level
    subsections, consecutive ones merged up to MAX_CHUNK paragraphs."""
    top: dict[tuple[str, str], list[Paragraph]] = defaultdict(list)
    for p in paragraphs:
        top[(p.regulation, _section(p, 1))].append(p)
    out: dict[tuple[str, str], list[Paragraph]] = {}
    for (reg, name), ps in top.items():
        if len(ps) <= MAX_SECTION:
            out[(reg, name)] = ps
            continue
        subs: dict[str, list[Paragraph]] = defaultdict(list)
        for p in ps:
            subs[_section(p, 2)].append(p)
        chunk: list[Paragraph] = []
        first = last = ""
        for sub in sorted(subs, key=_order):
            if chunk and len(chunk) + len(subs[sub]) > MAX_CHUNK:
                out[(reg, first if first == last else f"{first}-{last}")] = chunk
                chunk = []
            if not chunk:
                first = sub
            chunk += subs[sub]
            last = sub
        out[(reg, first if first == last else f"{first}-{last}")] = chunk
    return out


def _heading_path(p: Paragraph, graph: Graph) -> str:
    names = []
    for pid in p.path:
        q = graph.paragraphs.get(pid)
        if q is not None:
            names.append(f"{q.label} {q.heading or q.text[:60]}")
    return " > ".join(names)


def _ask(
    reg: str, name: str, paragraphs: list[Paragraph], graph: Graph, product: str
) -> dict[str, float]:
    listing = "\n\n".join(
        f"[{p.label}] {_heading_path(p, graph)}\n{p.text[:TEXT_CHARS]}" for p in paragraphs
    )
    prompt = (
        f"Component: {product}\n\nRegulation: {reg}, section {name}\n\n{listing}\n\n"
        f"Give a probability for each of the {len(paragraphs)} paragraphs, by label."
    )
    data = llm.complete_json(_SYSTEM, prompt, _SCHEMA, tier="strong")
    got = {_key(d["label"]): min(1.0, max(0.0, float(d["p"]))) for d in data["paragraphs"]}
    return {p.id: got[_key(p.label)] for p in paragraphs if _key(p.label) in got}


def scores(drafts: Sequence[Draft], graph: Graph, product: str) -> dict[str, float]:
    """p_section per cited paragraph id. Paragraphs a section's answer misses are asked once
    more on their own; a paragraph still unscored stops the run."""
    out: dict[str, float] = {}
    if path := os.environ.get("BRAIN_SECTION_SCORES"):
        saved = json.loads(Path(path).read_text())
        for draft in drafts:
            p = draft.paragraph
            key = f"{p.regulation}|{_key(p.label)}"
            if key not in saved:
                raise ValueError(f"section scores {path}: missing {key}")
            score = float(saved[key])
            if not 0 <= score <= 1:
                raise ValueError(f"section scores {path}: {key} must be between 0 and 1")
            out[p.id] = score
        return out
    order = {pid: i for i, pid in enumerate(graph.paragraphs)}
    cited = sorted(
        {d.paragraph.id: d.paragraph for d in drafts}.values(), key=lambda p: order[p.id]
    )
    todo = sorted(groups(cited).items())
    _, workers = llm.batching(1, 1, 6)

    def safe(item: tuple[tuple[str, str], list[Paragraph]]) -> dict[str, float]:
        (reg, name), ps = item
        try:
            return _ask(reg, name, ps, graph, product)
        except Exception as e:
            print(f"[sections] {reg} {name} failed ({e!r:.200})", file=sys.stderr)
            return {}

    for _ in range(2):
        with ThreadPoolExecutor(workers) as pool:
            for part in pool.map(safe, todo):
                out |= part
        todo = [(sec, [p for p in ps if p.id not in out]) for sec, ps in todo]
        todo = [(sec, ps) for sec, ps in todo if ps]
        if not todo:
            break
    if todo:
        missing = sum(len(ps) for _, ps in todo)
        raise RuntimeError(f"sections: {missing} paragraphs unscored after a retry")
    return out


def cut(
    drafts: Sequence[Draft], p_keep: Sequence[float], p_section: dict[str, float]
) -> list[Draft]:
    """The drafts with p_keep * p_section >= THRESHOLD, in order."""
    return [
        d
        for d, pk in zip(drafts, p_keep, strict=True)
        if pk * p_section[d.paragraph.id] >= THRESHOLD
    ]
