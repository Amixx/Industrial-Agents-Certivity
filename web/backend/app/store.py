import json
from pathlib import Path

from .models import Assessment
from .paths import CASES, DATA_DIR

_FILE = DATA_DIR / "assessments.json"
# The rear lamp assessment the landing page shows, available even on an empty store.
_SHOWCASE = Path(__file__).with_name("showcase.json")
# Assessments built from uploaded files, for the coverage page (scripts/build_coverage.py).
_SEEDS = Path(__file__).with_name("seeds.json")
_IMAGES = DATA_DIR / "images"
_IMAGE_TYPES = {b"\x89PNG": "png", b"\xff\xd8\xff": "jpg", b"RIFF": "webp", b"GIF8": "gif"}

assessments: dict[str, Assessment] = {}
applied: dict[str, list[str]] = {}


def load() -> None:
    showcase = Assessment.model_validate_json(_SHOWCASE.read_text(encoding="utf-8"))
    assessments[showcase.id] = showcase
    for item in json.loads(_SEEDS.read_text()):
        seed = Assessment.model_validate(item)
        assessments[seed.id] = seed
    if not _FILE.is_file():
        return
    raw = json.loads(_FILE.read_text(encoding="utf-8"))
    for item in raw["assessments"]:
        assessment = Assessment.model_validate(item)
        assessments[assessment.id] = assessment
    applied.update(raw["applied"])


def seed_for(case: str) -> str | None:
    """The id of the seeded engine run on `case`, by its spec."""
    spec = (CASES / case / "spec.md").read_text(encoding="utf-8").strip()
    seeds = [Assessment.model_validate(a) for a in json.loads(_SEEDS.read_text())]
    return next((a.id for a in seeds if a.spec.strip() == spec), None)


def save() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    _FILE.write_text(
        json.dumps({"assessments": [a.dump() for a in assessments.values()], "applied": applied}),
        encoding="utf-8",
    )


def put(assessment: Assessment) -> None:
    assessments[assessment.id] = assessment
    save()


def store_image(assessment_id: str, image: bytes) -> None:
    _IMAGES.mkdir(parents=True, exist_ok=True)
    ext = next((e for magic, e in _IMAGE_TYPES.items() if image.startswith(magic)), "png")
    (_IMAGES / f"{assessment_id}.{ext}").write_bytes(image)


def image_path(assessment_id: str) -> Path | None:
    return next(iter(_IMAGES.glob(f"{assessment_id}.*")), None)
