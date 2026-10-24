import json
from pathlib import Path

from .models import Assessment
from .paths import DATA_DIR

_FILE = DATA_DIR / "assessments.json"
_IMAGES = DATA_DIR / "images"
_IMAGE_TYPES = {b"\x89PNG": "png", b"\xff\xd8\xff": "jpg", b"RIFF": "webp", b"GIF8": "gif"}

assessments: dict[str, Assessment] = {}
applied: dict[str, list[str]] = {}


def load() -> None:
    if not _FILE.is_file():
        return
    raw = json.loads(_FILE.read_text())
    for item in raw["assessments"]:
        assessment = Assessment.model_validate(item)
        assessments[assessment.id] = assessment
    applied.update(raw["applied"])


def save() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    _FILE.write_text(
        json.dumps({"assessments": [a.dump() for a in assessments.values()], "applied": applied})
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
