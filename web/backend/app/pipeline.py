import asyncio
import json
import re
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

from .fake_data import EXCLUDED, INCLUDED, PARAGRAPH_COUNTS
from .models import (
    Assessment,
    Partial,
    PipelineEvent,
    Profile,
    RegulationDecision,
    Requirement,
)
from .paths import CASES, REGULATIONS

STUB_CASE = "dev-rear-lamp"
STUB_LIMIT = 20


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


def _section(spec: str, heading: str) -> str:
    match = re.search(
        rf"^##[ \t]+{heading}[ \t]*$(.*?)(?=^##\s|\Z)",
        spec,
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def _bullets(text: str) -> list[str]:
    return [
        m.group(1).strip()
        for line in text.splitlines()
        if (m := re.match(r"^\s*[-*]\s+(.*)$", line))
    ]


def _first_line(text: str) -> str:
    return next((line.strip() for line in text.splitlines() if line.strip()), "")


def derive_profile(spec: str) -> Profile:
    rows = [
        line.strip()
        for line in _section(spec, "Materials").splitlines()
        if line.strip().startswith("|") and not re.match(r"^\|\s*-", line.strip())
    ][1:]
    materials = []
    for row in rows:
        part, material = (cell.strip() for cell in row.split("|")[1:3])
        materials.append(f"{part}: {material}")
    return Profile(
        product_type=re.sub(r"\s+", " ", _first_line(_section(spec, "Product Type"))),
        vehicle_category=_first_line(_section(spec, "Vehicle Category")),
        parts=_bullets(_section(spec, "Main Parts")),
        functions=_bullets(_section(spec, "Functions?")),
        materials=materials,
    )


def _title(regulation: str) -> str:
    return next((r["title"] for r in regulation_index() if r["regulation"] == regulation), "")


def _base_version(regulation: str) -> str:
    for entry in regulation_index():
        if entry["regulation"] == regulation:
            return next((v["version_label"] for v in entry["versions"] if v["role"] == "base"), "")
    return ""


def decisions(requirements: list[Requirement]) -> list[RegulationDecision]:
    def count(regulation: str) -> int:
        return sum(1 for r in requirements if r.source.regulation == regulation)

    return [
        *(
            RegulationDecision(
                regulation=regulation,
                version=version,
                title=_title(regulation),
                included=True,
                reason=reason,
                requirement_count=count(regulation),
            )
            for regulation, version, reason in INCLUDED
        ),
        *(
            RegulationDecision(
                regulation=regulation,
                version=_base_version(regulation),
                title=_title(regulation),
                included=False,
                reason=reason,
                requirement_count=0,
            )
            for regulation, reason in EXCLUDED
        ),
    ]


def case_requirements() -> list[Requirement]:
    expected = json.loads((CASES / STUB_CASE / "expected.json").read_text())
    return [Requirement.model_validate(r) for r in expected["requirements"]]


async def run_assessment(
    spec: str, image: bytes | None, case_name: str | None
) -> AsyncIterator[PipelineEvent | Assessment]:
    """Yield progress events, ending with the `done` event and then the finished Assessment."""
    requirements = case_requirements()
    total_regulations = len(regulation_index())

    yield PipelineEvent(step="profile", message="Reading spec", progress=0.03)
    await asyncio.sleep(0.6)
    profile = derive_profile(spec)
    yield PipelineEvent(
        step="profile",
        message=(
            f"Reading spec: {len(profile.parts)} parts, {len(profile.functions)} functions, "
            f"{len(profile.materials)} materials"
        ),
        progress=0.15,
        partial=Partial(profile=profile),
    )
    await asyncio.sleep(0.7)

    yield PipelineEvent(
        step="selection",
        message=f"Screening {total_regulations} regulations against the profile",
        progress=0.22,
        partial=Partial(profile=profile),
    )
    await asyncio.sleep(0.8)
    regulations = decisions([])
    yield PipelineEvent(
        step="selection",
        message=(
            f"Selected {len(INCLUDED)} of {total_regulations} regulations, "
            f"{len(EXCLUDED)} excluded with reasons"
        ),
        progress=0.38,
        partial=Partial(profile=profile, regulations=regulations),
    )
    await asyncio.sleep(0.5)

    paragraph_count = 0
    total_paragraphs = sum(PARAGRAPH_COUNTS.values())
    for regulation, version, _ in INCLUDED:
        paragraph_count += PARAGRAPH_COUNTS[regulation]
        yield PipelineEvent(
            step="paragraphs",
            message=(
                f"Scanning {regulation} {version}: "
                f"{PARAGRAPH_COUNTS[regulation]} applicable paragraphs"
            ),
            progress=0.38 + 0.22 * paragraph_count / total_paragraphs,
            partial=Partial(
                profile=profile, regulations=regulations, paragraph_count=paragraph_count
            ),
        )
        await asyncio.sleep(0.3)
    yield PipelineEvent(
        step="paragraphs",
        message=f"Scanning {paragraph_count} paragraphs",
        progress=0.6,
        partial=Partial(profile=profile, regulations=regulations, paragraph_count=paragraph_count),
    )
    await asyncio.sleep(0.4)

    found: list[Requirement] = []
    for regulation, _, _ in INCLUDED:
        batch = [r for r in requirements if r.source.regulation == regulation]
        found.extend(batch)
        yield PipelineEvent(
            step="requirements",
            message=f"{regulation}: {len(batch)} requirements extracted",
            progress=0.6 + 0.38 * len(found) / len(requirements),
            partial=Partial(
                profile=profile,
                regulations=decisions(found),
                paragraph_count=paragraph_count,
                requirements=list(found),
            ),
        )
        await asyncio.sleep(0.45)

    assessment = Assessment(
        id=uuid.uuid4().hex[:8],
        created_at=datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        case_name=case_name,
        spec=spec,
        profile=profile,
        regulations=decisions(requirements),
        requirements=requirements,
        status="complete",
    )
    yield PipelineEvent(
        step="done",
        message=f"{len(requirements)} requirements from {len(INCLUDED)} regulations",
        progress=1,
        assessment_id=assessment.id,
        partial=Partial(
            profile=profile,
            regulations=assessment.regulations,
            paragraph_count=paragraph_count,
            requirements=requirements,
        ),
    )
    yield assessment
