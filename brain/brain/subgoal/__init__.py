"""Sub-goal: which requirements of an old regulation version change in a new one, and why.

    uv run python -m brain.subgoal --old-pdf ../subgoal/dev/old.pdf --new-pdf ../subgoal/dev/new.pdf
        --requirements-old ../subgoal/dev/requirements_old.json --case-id subgoal-dev --out out.json

Both versions are parsed with brain.ingest and cut into units (text.py), old and new units are
aligned (align.py), and the change records are written from the alignment (changes.py). The
scorer is score.py, the survey of every base and latest pair and the synthetic edits survey.py.
Design: docs/regulation-change.md at the repo root.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from brain.ingest import parse_pdf
from brain.models import Paragraph
from brain.paths import INDEX, TOOLS

from .align import Kind, Link, Span, align, kind, units
from .changes import (
    added_changes,
    cited_sections,
    fuse,
    map_requirements,
    obligations,
    system_name,
    top,
)
from .text import Op, bare, describe, fit, quote, sentences, shorten, substantive, word_ops

__all__ = [
    "Kind",
    "Link",
    "Op",
    "Span",
    "added_changes",
    "align",
    "bare",
    "describe",
    "diff_assessment",
    "diff_parsed",
    "fit",
    "fuse",
    "kind",
    "map_requirements",
    "obligations",
    "quote",
    "run",
    "sentences",
    "shorten",
    "substantive",
    "system_name",
    "top",
    "units",
    "validate",
    "version_of",
    "word_ops",
]


def version_of(pdf: Path) -> str | None:
    """The version label of the PDF in regulations/index.json with the same SHA-256, if any."""
    digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    for regulation in json.loads(INDEX.read_text()):
        for version in regulation["versions"]:
            if any(f.get("sha256") == digest for f in version.get("files", [])):
                return str(version["version_label"])
    return None


def diff_assessment(
    old_pdf: Path,
    new_pdf: Path,
    requirements: Sequence[dict[str, Any]],
    to_version: str | None = None,
    inclusive: bool = False,
) -> list[dict[str, Any]]:
    """The changes to a set of requirements when their regulation moves from `old_pdf` to
    `new_pdf`. Modified rows also carry `old_span` and `new_span`, the text before and after."""
    to_version = to_version or version_of(new_pdf)
    if to_version is None:
        digest = hashlib.sha256(new_pdf.read_bytes()).hexdigest()
        raise ValueError(f"pass --to-version: {digest} is not in regulations/index.json")
    regulation = requirements[0]["source"]["regulation"]
    old = parse_pdf(old_pdf, regulation, version_of(old_pdf) or "old", "base")
    new = parse_pdf(new_pdf, regulation, to_version, "latest")
    return diff_parsed(old, new, align(old, new), requirements, regulation, to_version, inclusive)


def diff_parsed(
    old: Sequence[Paragraph],
    new: Sequence[Paragraph],
    links: Sequence[Link],
    requirements: Sequence[dict[str, Any]],
    regulation: str,
    to_version: str,
    inclusive: bool = False,
) -> list[dict[str, Any]]:
    """`diff_assessment` on versions already parsed and aligned, for callers that also need the
    paragraphs and links, such as the web app's paragraph diff."""
    sections = cited_sections(requirements, old)
    modified = map_requirements(
        requirements,
        old,
        links,
        regulation,
        to_version,
        new=new,
        system=system_name(new),
        inclusive=inclusive,
    )
    consumed = {i for c in modified for i in c.pop("new_units", [])}
    added = added_changes(
        links,
        sections,
        regulation,
        to_version,
        consumed=consumed,
        inclusive=inclusive,
    )
    return modified + added


def run(
    old_pdf: Path,
    new_pdf: Path,
    requirements: Sequence[dict[str, Any]],
    case_id: str,
    team_id: str = "team-06",
    to_version: str | None = None,
    inclusive: bool = False,
) -> dict[str, Any]:
    """The sub-goal submission for one pair of regulation versions."""
    changes = [
        {k: v for k, v in c.items() if k not in ("old_span", "new_span")}
        for c in diff_assessment(old_pdf, new_pdf, requirements, to_version, inclusive)
    ]
    return {"team_id": team_id, "case_id": case_id, "changes": changes}


def validate(submission: dict[str, Any], requirements: Sequence[dict[str, Any]]) -> list[str]:
    """Problems that Certivity's tools/validate.py finds, with the requirement id check on."""
    spec = importlib.util.spec_from_file_location("validate", TOOLS / "validate.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["validate"] = module  # dataclasses need the module registered
    spec.loader.exec_module(module)
    return [str(p) for p in module.validate(submission, requirements_old=list(requirements))]
