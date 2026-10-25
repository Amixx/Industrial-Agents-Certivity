"""Writes the demo's seeded front bumper assessment and the precomputed update runs.

    cd web/backend && uv run --no-sync python -m app.demo_data

- app/front-bumper.json: the held-out front bumper case as an assessment, from the main goal's
  output out/heldout-silver-r10r148.json (no model call; that run's spend is in out/README.md).
- data/regulation-updates/<case>.json: every cited regulation of each seeded assessment
  compared with its newest version in the corpus, by `brain.subgoal` (no model, about 1 s each).
"""

import json
from pathlib import Path

from . import pipeline, updates
from .models import Assessment, RunCost
from .paths import CASES, ROOT, UPDATES

BUMPER_CASE = "heldout-front-bumper"
BUMPER_OUT = ROOT / "out" / "heldout-silver-r10r148.json"
BUMPER_ID = "b7e1a9c4"
# The upload time of out/heldout-silver-r10r148.json (out/README.md, held-out run log).
BUMPER_CREATED = "2026-10-25T08:16:00.000Z"
SEEDS = {"dev-rear-lamp": "showcase.json", BUMPER_CASE: "front-bumper.json"}


def bumper() -> Assessment:
    submission = json.loads(BUMPER_OUT.read_text())
    spec = (CASES / BUMPER_CASE / "spec.md").read_text()
    assessment = pipeline._assessment(
        submission, spec, "Front bumper", RunCost(total_usd=0, models=[])
    )
    return assessment.model_copy(
        update={
            "id": BUMPER_ID,
            "created_at": BUMPER_CREATED,
            "image_url": f"/api/cases/{BUMPER_CASE}/image",
            "cost": None,
        }
    )


def main() -> None:
    seed = Path(__file__).with_name(SEEDS[BUMPER_CASE])
    seed.write_text(json.dumps(bumper().dump(), ensure_ascii=False) + "\n")
    UPDATES.mkdir(parents=True, exist_ok=True)
    for case, name in SEEDS.items():
        assessment = Assessment.model_validate_json(Path(__file__).with_name(name).read_text())
        runs = []
        for cited in updates.cited(assessment, []):
            if not cited.latest:
                continue
            old, new, identified_by, digest = updates.resolve(
                assessment, None, None, cited.regulation, None, [], Path()
            )
            run = updates.compare(assessment, old, new, "corpus", digest, new.pdf.name)
            runs.append(run)
            kinds = [c.change for c in run.changes]
            print(
                f"{case:22} {run.regulation:8} {run.from_version} to {run.to_version}: "
                f"{run.stats.amended} amended, {run.stats.new} new, {run.stats.deleted} deleted, "
                f"{run.stats.unchanged_share:.1%} unchanged; "
                f"{kinds.count('modified')} modified, {kinds.count('removed')} removed, "
                f"{kinds.count('added')} added"
            )
        (UPDATES / f"{case}.json").write_text(
            json.dumps([r.dump() for r in runs], ensure_ascii=False, indent=1) + "\n"
        )


if __name__ == "__main__":
    main()
