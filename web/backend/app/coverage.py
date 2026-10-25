"""An assessment against the expert's answer, for the coverage page.

The local judge (`brain/eval/coverage.py`, token overlap) runs in the brain's venv; responses for
the stored assessments are precomputed in `coverage_data/` so the page works without it. The
challenge platform's score comes from `coverage_data/uploads.json`, the files in `out/` that were
uploaded, found by the fingerprint of the requirement list. `scripts/build_coverage.py` writes
both.
"""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from . import store
from .models import Assessment, Coverage, NearCut, PlatformScore, Requirement, Source
from .paths import BRAIN, BRAIN_PYTHON, CASES

DATA = Path(__file__).with_name("coverage_data")
UPLOADS = DATA / "uploads.json"
# Paragraphs on each side of the cut the page lists when there is no expert answer.
NEAR_CUT = 12

_judged: dict[str, dict[str, Any]] = {}


def fingerprint(requirements: list[Requirement]) -> str:
    """The same for two lists with the same rows in any order, ids aside."""
    rows = sorted(
        [r.source.regulation, r.source.version, r.source.page, r.source.paragraph, r.text]
        for r in requirements
    )
    return hashlib.sha256(json.dumps(rows).encode()).hexdigest()[:16]


def case_of(assessment: Assessment) -> str | None:
    """The case whose spec this assessment ran on."""
    spec = assessment.spec.strip()
    for folder in sorted(CASES.iterdir()):
        path = folder / "spec.md"
        if path.is_file() and path.read_text(encoding="utf-8").strip() == spec:
            return folder.name
    return None


def platform(key: str) -> PlatformScore | None:
    found = json.loads(UPLOADS.read_text()).get(key) if UPLOADS.is_file() else None
    return PlatformScore.model_validate(found) if found else None


def judge(assessment: Assessment, expected: Path) -> dict[str, Any]:
    """`eval.coverage`'s output for this assessment: precomputed, or run in the brain's venv."""
    key = fingerprint(assessment.requirements)
    stored = DATA / f"{key}.json"
    if stored.is_file():
        found: dict[str, Any] = json.loads(stored.read_text())
        return found
    if key not in _judged:
        payload = {
            "requirements": [r.model_dump() for r in assessment.requirements],
            "below_cut": [c.model_dump() for c in assessment.below_cut or []],
        }
        done = subprocess.run(
            [str(BRAIN_PYTHON), "-m", "eval.coverage", "--expected", str(expected)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            cwd=BRAIN,
            timeout=120,
            check=True,
        )
        _judged[key] = json.loads(done.stdout)
    return _judged[key]


def near_cut(assessment: Assessment) -> list[NearCut]:
    """The paragraphs closest to the cut on each side: those the run cut with the highest score
    against their cut, and those it kept with the lowest score."""
    under = sorted(assessment.below_cut or [], key=lambda c: -c.score / c.cut)[:NEAR_CUT]
    kept: dict[tuple[str, str], Requirement] = {}
    for r in assessment.requirements:
        if r.confidence is not None:
            kept.setdefault((r.source.regulation, r.source.paragraph), r)
    over = sorted(kept.values(), key=lambda r: r.confidence or 0.0)[:NEAR_CUT]
    return [
        NearCut(
            source=Source(
                regulation=c.regulation, version=c.version, page=c.page, paragraph=c.paragraph
            ),
            text=c.text,
            score=c.score,
            cut=c.cut,
            stage=c.stage,
            kept=False,
        )
        for c in under
    ] + [
        NearCut(source=r.source, text=r.quote or r.text, score=r.confidence or 0.0, kept=True)
        for r in over
    ]


def coverage_for(assessment: Assessment) -> Coverage:
    case = case_of(assessment)
    expected = CASES / case / "expected.json" if case else None
    excluded = [d for d in assessment.regulations if not d.included]
    score = platform(fingerprint(assessment.requirements))
    if not expected or not expected.is_file():
        return Coverage(
            case=case,
            has_answer=False,
            platform=score,
            excluded=excluded,
            near_cut=near_cut(assessment),
        )
    judged = judge(assessment, expected)
    ours = {(r.source.regulation, r.source.paragraph, r.text) for r in assessment.requirements}
    gold = [Requirement.model_validate(r) for r in json.loads(expected.read_text())["requirements"]]
    copies = sum((r.source.regulation, r.source.paragraph, r.text) in ours for r in gold)
    return Coverage.model_validate(
        {
            **judged,
            "case": case,
            "has_answer": True,
            "platform": score,
            "excluded": excluded,
            "near_cut": near_cut(assessment),
            "expert_copies": copies,
            "engine_run": store.seed_for(case) if case and copies == len(gold) else None,
        }
    )
