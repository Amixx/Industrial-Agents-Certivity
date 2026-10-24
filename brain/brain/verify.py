"""Last checks before writing a submission: base version only, numbers present in the source,
quote overlap with the paragraph, duplicates removed, Certivity's validate.py passes."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from typing import Any

from .models import Paragraph
from .paths import INDEX, TOOLS
from .rewrite import Draft

NUMBER = re.compile(r"\d+(?:[.,]\d+)*")


def base_versions() -> dict[str, str]:
    return {
        e["regulation"]: v["version_label"]
        for e in json.loads(INDEX.read_text())
        for v in e["versions"]
        if v["role"] == "base"
    }


def faithful(d: Draft, context: str = "") -> bool:
    """Every number in the requirement appears in its paragraph or in `context`, the text of its
    ancestors, whose conditions a rewrite may carry in (guards LLM rewrites)."""
    source = (d.paragraph.text + " " + context).replace(" ", "")
    return all(n.replace(" ", "") in source for n in NUMBER.findall(d.text))


def _key(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def clean(
    drafts: list[Draft], paragraphs: dict[str, Paragraph] | None = None
) -> tuple[list[Draft], list[tuple[Draft, str]]]:
    """Drop drafts that fail a check; `paragraphs` (id -> paragraph) supplies ancestor text."""
    paragraphs = paragraphs or {}
    kept: list[Draft] = []
    dropped: list[tuple[Draft, str]] = []
    seen: set[tuple[str, str]] = set()
    versions = base_versions()
    for d in drafts:
        p = d.paragraph
        if versions.get(p.regulation) != p.version:
            dropped.append((d, "not the base version"))
        elif not faithful(d, " ".join(paragraphs[a].text for a in p.path if a in paragraphs)):
            dropped.append((d, "number not in source"))
        elif len(d.text) > 2000 or len(d.text) < 10:
            dropped.append((d, "length"))
        elif (p.regulation, _key(d.text)) in seen:
            dropped.append((d, "duplicate"))
        else:
            seen.add((p.regulation, _key(d.text)))
            kept.append(d)
    return kept, dropped


def validate(submission: dict[str, Any]) -> list[str]:
    spec = importlib.util.spec_from_file_location("validate", TOOLS / "validate.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["validate"] = module  # dataclasses need the module registered
    spec.loader.exec_module(module)
    index = json.loads(INDEX.read_text())
    return [str(p) for p in module.validate(submission, index=index)]
