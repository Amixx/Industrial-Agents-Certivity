import json
from pathlib import Path

from .models import Assessment, UpdateRun
from .paths import CASES, DATA_DIR, UPDATES

_FILE = DATA_DIR / "assessments.json"
# The rear lamp assessment the landing page shows (the dev case's expert answer), available even
# on an empty store.
_SHOWCASE = Path(__file__).with_name("showcase.json")
# Assessments built from uploaded files, for the coverage page (scripts/build_coverage.py),
# among them the front bumper the update runs and the exploded view use.
_SEEDS = Path(__file__).with_name("seeds.json")
_IMAGES = DATA_DIR / "images"
_UPLOADS = DATA_DIR / "uploads"
_IMAGE_TYPES = {b"\x89PNG": "png", b"\xff\xd8\xff": "jpg", b"RIFF": "webp", b"GIF8": "gif"}

assessments: dict[str, Assessment] = {}
# Update runs by (assessment id, run id): the precomputed ones from data/regulation-updates/,
# then the stored ones.
runs: dict[tuple[str, str], UpdateRun] = {}
# The assessment as it was before a run was applied, by (assessment id, run id), for undo.
before: dict[tuple[str, str], Assessment] = {}


def load() -> None:
    showcase = Assessment.model_validate_json(_SHOWCASE.read_text(encoding="utf-8"))
    assessments[showcase.id] = showcase
    for item in json.loads(_SEEDS.read_text(encoding="utf-8")):
        seed = Assessment.model_validate(item)
        assessments[seed.id] = seed
    for file in sorted(UPDATES.glob("*.json")):
        for item in json.loads(file.read_text(encoding="utf-8")):
            run = UpdateRun.model_validate(item)
            runs[run.assessment_id, run.id] = run
    if not _FILE.is_file():
        return
    raw = json.loads(_FILE.read_text(encoding="utf-8"))
    for item in raw["assessments"]:
        assessment = Assessment.model_validate(item)
        assessments[assessment.id] = assessment
    for item in raw.get("runs", []):
        run = UpdateRun.model_validate(item)
        runs[run.assessment_id, run.id] = run
    for item in raw.get("before", []):
        before[item["assessmentId"], item["run"]] = Assessment.model_validate(item["assessment"])


def seed_for(case: str) -> str | None:
    """The id of the seeded engine run on `case`, by its spec."""
    spec = (CASES / case / "spec.md").read_text(encoding="utf-8").strip()
    seeds = [Assessment.model_validate(a) for a in json.loads(_SEEDS.read_text())]
    return next((a.id for a in seeds if a.spec.strip() == spec), None)


def save() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    _FILE.write_text(
        json.dumps(
            {
                "assessments": [a.dump() for a in assessments.values()],
                "runs": [r.dump() for r in runs.values()],
                "before": [
                    {"assessmentId": a, "run": r, "assessment": snapshot.dump()}
                    for (a, r), snapshot in before.items()
                ],
            }
        ),
        encoding="utf-8",
    )


def put(assessment: Assessment) -> None:
    assessments[assessment.id] = assessment
    save()


def put_run(run: UpdateRun) -> None:
    runs[run.assessment_id, run.id] = run
    save()


def runs_for(assessment_id: str) -> list[UpdateRun]:
    return [r for (a, _), r in runs.items() if a == assessment_id]


def upload_dir() -> Path:
    return _UPLOADS


def store_image(assessment_id: str, image: bytes) -> None:
    _IMAGES.mkdir(parents=True, exist_ok=True)
    ext = next((e for magic, e in _IMAGE_TYPES.items() if image.startswith(magic)), "png")
    (_IMAGES / f"{assessment_id}.{ext}").write_bytes(image)


def image_path(assessment_id: str) -> Path | None:
    return next(iter(_IMAGES.glob(f"{assessment_id}.*")), None)
