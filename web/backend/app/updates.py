import json

from .fake_data import FAKE_UPDATES
from .models import (
    Assessment,
    ChangeSource,
    RegulationUpdate,
    Requirement,
    RequirementChange,
    Source,
)
from .paths import UPDATES
from .pipeline import case_requirements

_REAL_FILE = UPDATES / "dev-rear-lamp.json"


def _fake_updates() -> list[RegulationUpdate]:
    original = {r.id: r.text for r in case_requirements()}
    return [
        RegulationUpdate(
            regulation=u.regulation,
            from_version=u.from_version,
            to_version=u.to_version,
            changes=[
                RequirementChange(
                    requirement_id=c.requirement_id,
                    change=c.change,  # type: ignore[arg-type]
                    old_text=original.get(c.requirement_id) if c.requirement_id else None,
                    new_text=c.new_text,
                    reason=c.reason,
                    source=ChangeSource(page=c.page, paragraph=c.paragraph),
                )
                for c in u.changes
            ],
        )
        for u in FAKE_UPDATES
    ]


def catalogue() -> list[RegulationUpdate]:
    if _REAL_FILE.is_file():
        return [RegulationUpdate.model_validate(u) for u in json.loads(_REAL_FILE.read_text())]
    return _fake_updates()


def updates_for(assessment: Assessment, applied: list[str]) -> list[RegulationUpdate]:
    included = {d.regulation for d in assessment.regulations if d.included}
    return [
        u.model_copy(update={"applied": u.regulation in applied})
        for u in catalogue()
        if u.regulation in included
    ]


def apply_update(assessment: Assessment, update: RegulationUpdate) -> Assessment:
    regulation = update.regulation
    requirements = [
        r.model_copy(update={"source": r.source.model_copy(update={"version": update.to_version})})
        if r.source.regulation == regulation
        else r
        for r in assessment.requirements
    ]
    added = 0
    for change in update.changes:
        if change.change == "removed":
            requirements = [r for r in requirements if r.id != change.requirement_id]
        elif change.change == "modified":
            requirements = [
                r.model_copy(
                    update={
                        "text": change.new_text or r.text,
                        "source": r.source.model_copy(update=change.source.model_dump()),
                    }
                )
                if r.id == change.requirement_id
                else r
                for r in requirements
            ]
        else:
            added += 1
            requirements.append(
                Requirement(
                    id=change.requirement_id or f"U-{regulation.removeprefix('UN ')}-{added:02d}",
                    text=change.new_text or "",
                    source=Source(
                        regulation=regulation,
                        version=update.to_version,
                        page=change.source.page,
                        paragraph=change.source.paragraph,
                    ),
                )
            )

    def count(reg: str) -> int:
        return sum(1 for r in requirements if r.source.regulation == reg)

    return assessment.model_copy(
        update={
            "requirements": requirements,
            "regulations": [
                d.model_copy(
                    update={"version": update.to_version, "requirement_count": count(regulation)}
                )
                if d.regulation == regulation
                else d
                for d in assessment.regulations
            ],
        }
    )
