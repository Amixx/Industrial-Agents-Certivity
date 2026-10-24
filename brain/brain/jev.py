"""Paragraph applicability from TypeSafe's Jev: five yes/no judgements per paragraph, combined
by a logistic regression fitted on the dev gold (data/jev_model.json).

Jev answers each judgement with a calibrated probability; code makes the decision. On dev the
combination ranks paragraphs at AUC 0.96 (decision model 0.84), and the dev-fit weights hold on
the synthetic lamps (0.966, 0.964). See docs/jev.md.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from . import llm
from .graph import Graph
from .models import Paragraph, ProductProfile
from .paths import CACHE, DATA
from .relevance import _heading_path, _parent_text

URL = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-1.14.0"
PRICE_PER_INPUT_TOKEN = 0.042 / 1e6
MODEL_PATH = DATA / "jev_model.json"
# 25 paragraphs with five questions each stay near 31k tokens, under the 64k request limit.
BATCH = 25
WORKERS = 4
TEXT_CHARS = 1500

# name: (question, what yes means, what no means)
NOULS = {
    "technical": (
        "Does this paragraph state a technical requirement: construction, performance, colour, "
        "dimensions, position, markings, or a limit the device or vehicle must meet in a test?",
        "It states a technical requirement or test limit, such as a minimum luminous intensity, "
        "a required colour, a mounting height, or a marking the device must carry.",
        "It is a definition, scope statement, administrative step (application, approval form, "
        "extension, communication, transitional provision), or a description of test equipment "
        "or laboratory set-up that sets no limit.",
    ),
    "own_function": (
        "Is this paragraph about one of the lamps, devices or functions that `product` has?",
        "It concerns a lamp, device or function listed in `product.functions` or "
        "`product.parts`, for example a stop lamp requirement for a product with a stop lamp.",
        "It concerns a different lamp, device or function, or none in particular.",
    ),
    "other_function": (
        "Is this paragraph specifically about a lamp, device or function that `product` does "
        "not have?",
        "It concerns only a lamp, device or function absent from `product`, for example a "
        "headlamp or direction indicator requirement for a product that has neither.",
        "It concerns the product's own functions, or applies to every device the regulation "
        "covers.",
    ),
    "installation": (
        "Is this paragraph about how a device is installed on the vehicle rather than about the "
        "device itself?",
        "It sets vehicle-level installation conditions: number of lamps, mounting position, "
        "geometric visibility, electrical connection or switching on the vehicle.",
        "It sets requirements on the device as a component, independent of the vehicle.",
    ),
    "electronics": (
        "Is this paragraph about electromagnetic compatibility of electrical or electronic "
        "equipment?",
        "It concerns electromagnetic emissions or immunity of a vehicle or an electrical or "
        "electronic sub-assembly.",
        "It concerns optical, mechanical or administrative matters.",
    ),
}


def enabled() -> bool:
    return os.environ.get("BRAIN_JEV") == "1"


def _questions(chunk: list[Paragraph], graph: Graph) -> dict[str, Any]:
    qs = {}
    for n, p in enumerate(chunk):
        para = json.dumps(
            {
                "regulation": p.regulation,
                "label": p.label,
                "heading_path": _heading_path(p, graph),
                "parent_clause": _parent_text(p, graph),
                "text": p.text[:TEXT_CHARS],
            },
            ensure_ascii=False,
        )
        for name, (ask, yes, no) in NOULS.items():
            qs[f"{name}__{n}"] = {
                "type": "noul",
                "instructions": f"{ask}\n\nParagraph: {para}",
                "criteria": {"true": yes, "false": no},
            }
    return qs


def _post(body: dict[str, Any]) -> dict[str, Any]:
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        raise RuntimeError("BRAIN_JEV=1 needs TYPESAFE_API_KEY")
    req = urllib.request.Request(
        URL,
        json.dumps(body).encode(),
        {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.loads(r.read())  # type: ignore[no-any-return]
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < 4:
                time.sleep(2 * 2**attempt)
                continue
            raise RuntimeError(f"Jev HTTP {e.code}: {e.read().decode()[:300]}") from None
    raise AssertionError("unreachable")


def _ask(body: dict[str, Any]) -> dict[str, Any]:
    """One request through the disk cache; usage is counted like an LLM call."""
    digest = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    path = CACHE / "jev" / f"{digest}.json"
    meta = path.with_suffix(".usage.json")
    if path.exists():
        llm._record_hit(meta)
        return json.loads(path.read_text())  # type: ignore[no-any-return]
    resp = _post(body)
    path.parent.mkdir(parents=True, exist_ok=True)
    tokens = int(resp.get("usage", {}).get("input_tokens", 0))
    cost = llm.record(MODEL, tokens, 0, cost=tokens * PRICE_PER_INPUT_TOKEN)
    llm._write(path, resp)
    llm._write(meta, {"cost_usd": cost})
    return resp


def _combine(answers: dict[str, float], model: dict[str, Any]) -> float:
    z = model["intercept"]
    for name, w in zip(model["nouls"], model["coef"], strict=True):
        p = min(max(answers[name], 1e-4), 1 - 1e-4)
        z += w * math.log(p / (1 - p))
    return 1 / (1 + math.exp(-z))


def score(paragraphs: list[Paragraph], graph: Graph, profile: ProductProfile) -> dict[str, float]:
    """P(cited) per paragraph id from Jev's judgements."""
    model = json.loads(Path(MODEL_PATH).read_text())
    state = {
        "product": profile.model_dump(
            include={"product", "vehicle_categories", "functions", "parts", "electronics"}
        )
    }
    chunks = [paragraphs[i : i + BATCH] for i in range(0, len(paragraphs), BATCH)]

    def run(chunk: list[Paragraph]) -> dict[str, float]:
        body = {"model": MODEL, "state": state, "questions": _questions(chunk, graph)}
        got = _ask(body)["answers"]
        return {
            p.id: _combine({name: got[f"{name}__{n}"]["noul"] for name in NOULS}, model)
            for n, p in enumerate(chunk)
        }

    out: dict[str, float] = {}
    with ThreadPoolExecutor(WORKERS) as pool:
        for part in pool.map(run, chunks):
            out |= part
    return out
