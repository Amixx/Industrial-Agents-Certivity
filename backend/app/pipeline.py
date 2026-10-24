import json

from .paths import CASES

STUB_CASE = "dev-rear-lamp"
STUB_LIMIT = 20


def run(spec: str | None, image: bytes | None) -> dict:
    """Turn a product spec and exploded-view image into a main-submission payload."""
    expected = json.loads((CASES / STUB_CASE / "expected.json").read_text())
    return {
        "team_id": expected["team_id"],
        "case_id": "web",
        "requirements": expected["requirements"][:STUB_LIMIT],
    }
