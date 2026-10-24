"""Spec (+ exploded view) -> ProductProfile: what the product is, its parts and functions.

The deterministic parser reads the spec layout the cases use (## Product Type, ## Vehicle
Category, ## Function, ## Main Parts, ## Materials) and falls back to every bullet. With an LLM
configured, a model also reads the exploded view and maps the parts to regulation vocabulary.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from . import llm
from .models import ProductProfile

CATEGORY = re.compile(r"\b([MNLOmnlo][1-7](?:[a-e]|G)?)\b")
ELECTRONICS = re.compile(
    r"\b(LED|PCB|electronic\w*|sensor\w*|radar|lidar|camera|ECU|wiring|harness|actuator|motor|"
    r"heater|heating|control unit|electronic control)\b",
    re.IGNORECASE,
)
# "without radar, cameras or LED lamps", "no electronics", "not equipped with sensors": the
# negated stretch runs to the end of the clause.
NEGATED = re.compile(
    r"\b(?:without|no|not(?:\s+\w+){0,2}\s+with|excluding|excludes|none)\b[^.;\n]*", re.I
)
BULLET = re.compile(r"^\s*[-*•]\s+(.*\S)\s*$")
TABLE_ROW = re.compile(r"^\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|")


def _sections(spec: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    current = "_"
    for line in spec.splitlines():
        if m := re.match(r"^#{1,6}\s+(.*)$", line):
            current = m[1].strip().lower()
            continue
        out.setdefault(current, []).append(line)
    return out


def _bullets(lines: list[str]) -> list[str]:
    return [m[1] for line in lines if (m := BULLET.match(line))]


def _terms(items: list[str]) -> list[str]:
    """Items plus the terms in their brackets: "Braking indication (stop lamp)" -> both."""
    out: list[str] = []
    for item in items:
        out.append(re.sub(r"\s*\([^)]*\)", "", item).strip())
        out.extend(t.strip() for t in re.findall(r"\(([^)]*)\)", item))
    return [t for t in dict.fromkeys(out) if t]


def parse_spec(spec: str) -> ProductProfile:
    sections = _sections(spec)

    def pick(*names: str) -> list[str]:
        return [
            line
            for key, lines in sections.items()
            if any(n in key for n in names)
            for line in lines
        ]

    title = next(
        (
            re.sub(r"^#\s*(spec:)?\s*", "", line, flags=re.I).strip()
            for line in spec.splitlines()
            if line.startswith("# ")
        ),
        "",
    )
    product_lines = [line.strip() for line in pick("product type") if line.strip()]
    product = product_lines[0].split("—")[0].strip() if product_lines else title
    functions = _terms(_bullets(pick("function")))
    parts = _terms(_bullets(pick("part", "component")))
    materials = []
    for line in pick("material"):
        if (m := TABLE_ROW.match(line)) and not set(m[1]) <= set("-: "):
            if m[1].lower() not in ("component",):
                materials.append(f"{m[1]}: {m[2]}")
    if not functions and not parts:
        parts = _terms(_bullets(spec.splitlines()))
    found = CATEGORY.findall(" ".join(pick("categor")) or spec)
    categories = list(dict.fromkeys(c[0].upper() + c[1:] for c in found))
    keywords = list(dict.fromkeys(t.lower() for t in [product, *functions, *parts] if t))
    electronics = bool(ELECTRONICS.search(NEGATED.sub(" ", spec)))
    if electronics:  # in EMC terms, any component with electronics is an ESA
        keywords += ["electrical/electronic sub-assembly", "esa"]
    return ProductProfile(
        product=product or title,
        vehicle_categories=categories,
        functions=functions,
        parts=parts,
        materials=materials,
        electronics=electronics,
        keywords=keywords,
    )


_SYSTEM = """You read product specifications and exploded-view drawings of vehicle components
for a regulatory engineer. List what the product is, the vehicle categories it is for, its
functions and parts, and the regulation vocabulary (UN Regulation terms such as "stop lamp",
"rear position lamp", "retro-reflector", "front protective device", "bumper", "ESA") that
names each function or part. Only list what the inputs show or state; do not guess extras."""

_SCHEMA = {
    "type": "object",
    "properties": {
        "product": {"type": "string"},
        "vehicle_categories": {"type": "array", "items": {"type": "string"}},
        "functions": {"type": "array", "items": {"type": "string"}},
        "parts": {"type": "array", "items": {"type": "string"}},
        "materials": {"type": "array", "items": {"type": "string"}},
        "electronics": {"type": "boolean"},
        "keywords": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "product",
        "vehicle_categories",
        "functions",
        "parts",
        "materials",
        "electronics",
        "keywords",
    ],
    "additionalProperties": False,
}


def build_profile(
    spec: str, image: Path | None = None, use_llm: bool | None = None
) -> ProductProfile:
    base = parse_spec(spec)
    if use_llm is False or (use_llm is None and not llm.available()):
        return base
    content: list[dict[str, object]] = []
    if image is not None and image.exists():
        if llm.reads_images():
            content.append(llm.image_block(image))
        else:
            print(
                f"[profile] BRAIN_LLM={llm.provider()} reads no images; {image.name} is not used",
                file=sys.stderr,
            )
    content.append({"type": "text", "text": f"Specification:\n\n{spec}"})
    data = llm.complete_json(_SYSTEM, content, _SCHEMA, tier="strong")  # type: ignore[arg-type]
    found = ProductProfile.model_validate(data)
    # Union with the deterministic parse: recall first.
    return ProductProfile(
        product=found.product or base.product,
        vehicle_categories=list(dict.fromkeys(base.vehicle_categories + found.vehicle_categories)),
        functions=list(dict.fromkeys(base.functions + found.functions)),
        parts=list(dict.fromkeys(base.parts + found.parts)),
        materials=base.materials or found.materials,
        electronics=base.electronics or found.electronics,
        keywords=list(dict.fromkeys(base.keywords + [k.lower() for k in found.keywords])),
    )
