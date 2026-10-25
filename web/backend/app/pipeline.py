import asyncio
import json
import logging
import os
import re
import tempfile
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import spend, store
from .models import (
    Assessment,
    Partial,
    PipelineEvent,
    Profile,
    RegulationDecision,
    Requirement,
    RunCost,
)
from .paths import BRAIN, BRAIN_PYTHON, BRAIN_RUNNER, CASES, REGULATIONS

STUB_CASE = "dev-rear-lamp"
STUB_LIMIT = 20

# Models for a pipeline run on the server: the brain's strong tier (profile, regulation review,
# expert filter, section cut) and its bulk tier (relevance, rewrite).
STRONG_MODEL = "claude-sonnet-5-5"
BULK_MODEL = "claude-haiku-5-5"
# A run starts only with this much budget left, and stops spending at RUN_CAP_USD.
RUN_RESERVE_USD = 1.5
RUN_CAP_USD = 2.0
# A `[partial]` line carries every rewritten requirement, far past asyncio's 64 KiB default.
STDERR_LINE_LIMIT = 2**24
# Seconds without brain output before the stream repeats its last event, so proxies keep it open.
HEARTBEAT_S = 15

# Progress for the brain's log lines, by prefix.
STEPS: list[tuple[str, str, float]] = [
    ("profile:", "profile", 0.15),
    ("regulations:", "selection", 0.3),
    ("paragraphs selected:", "paragraphs", 0.6),
    ("requirements:", "requirements", 0.8),
    ("pointer and approval-mark rows:", "requirements", 0.83),
    ("expert filter:", "requirements", 0.9),
    ("section cut:", "requirements", 0.95),
]

log = logging.getLogger("uvicorn.error")

_running = asyncio.Lock()
_tasks: set[asyncio.Task[None]] = set()  # keeps runs alive after their stream is dropped


def run(spec: str | None, image: bytes | None) -> dict[str, Any]:
    """Turn a product spec and exploded-view image into a main-submission payload."""
    expected = json.loads((CASES / STUB_CASE / "expected.json").read_text())
    return {
        "team_id": expected["team_id"],
        "case_id": "web",
        "requirements": expected["requirements"][:STUB_LIMIT],
    }


def regulation_index() -> list[dict[str, Any]]:
    index: list[dict[str, Any]] = json.loads((REGULATIONS / "index.json").read_text())
    return index


def _title(regulation: str) -> str:
    return next((r["title"] for r in regulation_index() if r["regulation"] == regulation), "")


def case_requirements() -> list[Requirement]:
    expected = json.loads((CASES / STUB_CASE / "expected.json").read_text())
    return [Requirement.model_validate(r) for r in expected["requirements"]]


def uses_llm() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def uses_jev() -> bool:
    return bool(os.environ.get("TYPESAFE_API_KEY"))


def _env(budget: float) -> dict[str, str]:
    """The runner's environment. Explicit values win over anything in brain/.env."""
    env = dict(os.environ)
    env.update(
        BRAIN_MODEL_STRONG=STRONG_MODEL,
        BRAIN_MODEL_BULK=BULK_MODEL,
        BRAIN_RELEVANCE_TIER="bulk",
        BRAIN_JEV="1" if uses_jev() else "0",
        BRAIN_JEV_KB="1",
        BRAIN_CONSOLIDATE="1",
        RUN_PRICES=json.dumps(spend.PRICES),
        RUN_BUDGET_USD=str(budget),
        PYTHONPATH=str(BRAIN),
        PYTHONUNBUFFERED="1",
    )
    return env


def _event(line: str) -> PipelineEvent | None:
    """The progress event for one of the brain's step log lines."""
    text = re.sub(r"^\[brain [\d:]+\] ", "", line)
    for prefix, step, progress in STEPS:
        if text.startswith(prefix):
            return PipelineEvent(step=step, message=text, progress=progress)  # type: ignore[arg-type]
    return None


def _profile(raw: dict[str, Any]) -> Profile:
    return Profile(
        product_type=raw["product"],
        vehicle_category=", ".join(raw["vehicle_categories"]),
        parts=raw["parts"],
        functions=raw["functions"],
        materials=raw["materials"],
    )


def _regulation(choice: dict[str, Any], requirement_count: int) -> RegulationDecision:
    return RegulationDecision(
        regulation=choice["regulation"],
        version=choice["version"],
        title=_title(choice["regulation"]),
        included=choice["selected"],
        reason=choice["rationale"],
        requirement_count=requirement_count,
    )


def _update(partial: Partial, data: dict[str, Any]) -> Partial:
    """`partial` with one `[partial]` line from the runner applied."""
    if "profile" in data:
        return partial.model_copy(update={"profile": _profile(data["profile"])})
    if "regulations" in data:
        regulations = [_regulation(c, 0) for c in data["regulations"]]
        return partial.model_copy(update={"regulations": regulations})
    if "paragraph_count" in data:
        return partial.model_copy(update={"paragraph_count": data["paragraph_count"]})
    requirements = [
        Requirement.model_validate(
            {
                "id": f"R-{i:04d}",
                "text": r["text"],
                "source": {k: r[k] for k in ("regulation", "version", "page", "paragraph")},
            }
        )
        for i, r in enumerate(data["requirements"], start=1)
    ]
    return partial.model_copy(update={"requirements": requirements})


def _assessment(
    submission: dict[str, Any], spec: str, case_name: str | None, cost: RunCost
) -> Assessment:
    requirements = [Requirement.model_validate(r) for r in submission["requirements"]]

    def count(regulation: str) -> int:
        return sum(1 for r in requirements if r.source.regulation == regulation)

    return Assessment(
        id=uuid.uuid4().hex[:8],
        created_at=datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        case_name=case_name,
        spec=spec,
        profile=_profile(submission["profile"]),
        regulations=[_regulation(c, count(c["regulation"])) for c in submission["regulations"]],
        requirements=requirements,
        status="complete",
        cost=cost,
    )


async def _run(
    spec: str,
    image: bytes | None,
    case_name: str | None,
    budget: float,
    events: asyncio.Queue[PipelineEvent | None],
) -> None:
    """Run the brain in a subprocess, put progress on `events`, store the finished assessment,
    and end with None. Runs to the end even when nobody reads `events` any more."""
    try:
        with tempfile.TemporaryDirectory() as tmp:
            # The brain takes the image's media type from its suffix.
            suffix = ".png" if image and image.startswith(b"\x89PNG") else ".jpg"
            spec_path, image_path, out_path = (
                Path(tmp, n) for n in ("spec.md", f"image{suffix}", "out")
            )
            spec_path.write_text(spec)
            if image:
                image_path.write_bytes(image)
            proc = await asyncio.create_subprocess_exec(
                str(BRAIN_PYTHON),
                str(BRAIN_RUNNER),
                str(spec_path),
                str(image_path) if image else "",
                str(out_path),
                cwd=BRAIN,
                env=_env(budget),
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
                limit=STDERR_LINE_LIMIT,
            )
            assert proc.stderr
            partial = Partial()
            async for raw in proc.stderr:
                line = raw.decode().rstrip()
                if line.startswith("[partial] "):
                    partial = _update(partial, json.loads(line.removeprefix("[partial] ")))
                    continue
                log.info("brain: %s", line)
                event = _event(line)
                if m := re.match(r"\[cost\] calls=(\d+) usd=([\d.]+)", line):
                    event = PipelineEvent(
                        step="paragraphs",
                        message=f"{m[1]} model calls so far, ${float(m[2]):.2f}",
                        progress=0.6,
                    )
                if event:
                    await events.put(event.model_copy(update={"partial": partial}))
            code = await proc.wait()
            if not out_path.exists():
                raise RuntimeError(f"brain exited with code {code} before any output")
            result = json.loads(out_path.read_text())
        cost = RunCost.model_validate(result["cost"])
        spend.record(cost.total_usd)
        if result["error"]:
            raise RuntimeError(f"{result['error']} (exit code {code}, ${cost.total_usd:.2f} spent)")
        assessment = _assessment(result["submission"], spec, case_name, cost)
        if image:
            store.store_image(assessment.id, image)
            assessment = assessment.model_copy(
                update={"image_url": f"/api/assessments/{assessment.id}/image"}
            )
        store.put(assessment)
        spent = f", ${cost.total_usd:.2f}" if cost.models else ", no model calls"
        await events.put(
            PipelineEvent(
                step="done",
                message=f"{len(assessment.requirements)} requirements{spent}",
                progress=1,
                assessment_id=assessment.id,
                partial=partial,
            )
        )
    except Exception as e:
        log.exception("pipeline run failed")
        await events.put(PipelineEvent(step="failed", message=str(e), progress=1))
    finally:
        await events.put(None)
        _running.release()


async def run_assessment(
    spec: str, image: bytes | None, case_name: str | None
) -> AsyncIterator[PipelineEvent]:
    """Yield progress events, ending with `done` (carrying the stored assessment's id) or
    `failed`. With an API key the brain uses STRONG_MODEL and BULK_MODEL; without one it runs
    deterministically. With TYPESAFE_API_KEY, Jev scores the paragraphs."""
    if _running.locked():
        yield PipelineEvent(step="failed", message="Another run is in progress", progress=1)
        return
    budget = 0.0
    if uses_llm():
        try:
            spend.check(RUN_RESERVE_USD)
        except spend.BudgetExceeded as e:
            yield PipelineEvent(step="failed", message=str(e), progress=1)
            return
        budget = min(RUN_CAP_USD, spend.remaining())
    await _running.acquire()
    mode = f"{STRONG_MODEL} and {BULK_MODEL}" if uses_llm() else "no model, deterministic"
    if uses_jev():
        mode += ", Jev"
    last = PipelineEvent(step="profile", message=f"Reading spec ({mode})", progress=0.03)
    yield last
    events: asyncio.Queue[PipelineEvent | None] = asyncio.Queue()
    task = asyncio.create_task(_run(spec, image, case_name, budget, events))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    clock = asyncio.get_running_loop().time
    started = clock()
    while True:
        try:
            event = await asyncio.wait_for(events.get(), HEARTBEAT_S)
        except TimeoutError:
            yield last.model_copy(update={"message": f"{last.message}, {clock() - started:.0f} s"})
            continue
        if event is None:
            return
        last = event
        yield event
