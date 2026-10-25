import json
from pathlib import Path

from .models import Assessment, UpdateRun
from .paths import DATA_DIR, UPDATES

_FILE = DATA_DIR / "assessments.json"
# Assessments available even on an empty store: the rear lamp the landing page shows (the dev
# case's expert answer) and the front bumper (the held-out run in out/heldout-silver-r10r148.json).
_SEEDS = [Path(__file__).with_name(n) for n in ("showcase.json", "front-bumper.json")]
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
    for seed in _SEEDS:
        assessment = Assessment.model_validate_json(seed.read_text())
        assessments[assessment.id] = assessment
    for file in sorted(UPDATES.glob("*.json")):
        for item in json.loads(file.read_text()):
            run = UpdateRun.model_validate(item)
            runs[run.assessment_id, run.id] = run
    if not _FILE.is_file():
        return
    raw = json.loads(_FILE.read_text())
    for item in raw["assessments"]:
        assessment = Assessment.model_validate(item)
        assessments[assessment.id] = assessment
    for item in raw.get("runs", []):
        run = UpdateRun.model_validate(item)
        runs[run.assessment_id, run.id] = run
    for item in raw.get("before", []):
        before[item["assessmentId"], item["run"]] = Assessment.model_validate(item["assessment"])


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
        )
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
