"""A short prose brief for product developers, written by one `claude -p` call over an
assessment's requirements. Every sentence cites the requirement ids it rests on; briefs are cached
on disk by the requirement set they were written from.
"""

import hashlib
import json
import os
import subprocess
import threading
from typing import Any

from .models import Brief, Requirement
from .paths import BRIEFS

MODEL = "claude-opus-5-5"
TIMEOUT = 600  # seconds per call
ATTEMPTS = 3

SYSTEM = """You write the developer brief at the top of a UN Regulation compliance report.
The reader is the engineer designing the component. They need to know what the design must meet,
not how the regulations are organised.

Rules:
- Group the brief into 3 to 6 sections by function or design topic (for example photometry,
  colour, markings, installation). Section titles are short and in sentence case.
- Each section has 1 to 4 sentences. Each sentence states one concrete obligation or a tight group
  of related ones, with the numbers that matter (angles, intensities, colours, dimensions, tests).
- Be as concise as possible. Skip administrative paperwork (approval documents, conformity of
  production procedures) unless it changes the physical design.
- Every sentence lists in `cites` the ids of the requirements it rests on, and only ids from the
  input. Never state anything the cited requirements do not say.
- Write in the language an engineer uses, not legal language: "the lamp", "the lens", "must",
  concrete values and units. Translate regulatory phrasing into design consequences.
- Plain technical English. No em dashes, no middle dots, no exclamation marks, no filler words
  such as "robust", "seamless" or "ensure compliance"."""

SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "sentences": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string"},
                                "cites": {"type": "array", "items": {"type": "string"}},
                            },
                            "required": ["text", "cites"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["title", "sentences"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["sections"],
    "additionalProperties": False,
}

_locks: dict[str, threading.Lock] = {}


def _prompt(requirements: list[Requirement]) -> str:
    lines = [
        f"{r.id} | {r.source.regulation} paragraph {r.source.paragraph}, page {r.source.page} "
        f"| {r.text}"
        for r in requirements
    ]
    return "Requirements (id | source | text):\n" + "\n".join(lines)


def problems(brief: Brief, ids: set[str]) -> list[str]:
    """Citation errors: sentences without a citation, or citing an id that isn't in `ids`."""
    found = []
    for section in brief.sections:
        for sentence in section.sentences:
            if not sentence.cites:
                found.append(f"No citation: {sentence.text!r}")
            unknown = [c for c in sentence.cites if c not in ids]
            if unknown:
                found.append(f"Unknown ids {unknown} in: {sentence.text!r}")
    return found


def _complete(prompt: str) -> dict[str, Any]:
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    cmd = [
        "claude", "-p", prompt,
        "--model", MODEL,
        "--system-prompt", SYSTEM,
        "--tools", "",
        "--strict-mcp-config",
        "--setting-sources", "",
        "--disable-slash-commands",
        "--no-session-persistence",
        "--output-format", "json",
        "--json-schema", json.dumps(SCHEMA),
    ]  # fmt: skip
    done = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT, env=env)
    out = done.stdout
    reply = json.loads(out[out.find("{") : out.rfind("}") + 1])
    if reply.get("is_error"):
        raise RuntimeError(str(reply.get("result"))[:300])
    result: dict[str, Any] = reply.get("structured_output") or json.loads(reply["result"])
    return result


def _generate(requirements: list[Requirement]) -> Brief:
    ids = {r.id for r in requirements}
    prompt = _prompt(requirements)
    errors: list[str] = []
    for _ in range(ATTEMPTS):
        try:
            brief = Brief.model_validate(_complete(prompt))
        except (json.JSONDecodeError, RuntimeError, ValueError) as e:
            errors = [str(e)[:300]]
            continue
        errors = problems(brief, ids)
        if not errors:
            return brief
        prompt = (
            _prompt(requirements)
            + "\n\nYour previous brief had citation errors. Fix them:\n"
            + "\n".join(errors)
        )
    raise RuntimeError(f"No valid brief after {ATTEMPTS} attempts: {errors}")


def key(requirements: list[Requirement]) -> str:
    payload = [r.model_dump(include={"id", "text", "source"}) for r in requirements]
    blob = json.dumps({"model": MODEL, "system": SYSTEM, "requirements": payload}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def brief_for(requirements: list[Requirement]) -> Brief:
    digest = key(requirements)
    path = BRIEFS / f"{digest}.json"
    with _locks.setdefault(digest, threading.Lock()):
        if path.is_file():
            return Brief.model_validate_json(path.read_text())
        brief = _generate(requirements)
        BRIEFS.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(brief.dump(), indent=1) + "\n")
        return brief
