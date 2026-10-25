"""Writes the precomputed update runs for the demo's seeded assessments.

    cd web/backend && uv run --no-sync python -m app.demo_data

data/regulation-updates/<case>.json: every cited regulation of each seeded assessment (the rear
lamp in app/showcase.json, the front bumper in app/seeds.json) compared with its newest version
in the corpus, by `brain.subgoal` (no model, about 1 s each).
"""

import json
from pathlib import Path

from . import updates
from .models import Assessment
from .paths import UPDATES

BUMPER_ID = "8f93fc71"


def seeded() -> dict[str, Assessment]:
    here = Path(__file__).parent
    lamp = Assessment.model_validate_json((here / "showcase.json").read_text(encoding="utf-8"))
    seeds = json.loads((here / "seeds.json").read_text(encoding="utf-8"))
    bumper = next(Assessment.model_validate(a) for a in seeds if a["id"] == BUMPER_ID)
    return {"dev-rear-lamp": lamp, "heldout-front-bumper": bumper}


def main() -> None:
    UPDATES.mkdir(parents=True, exist_ok=True)
    for case, assessment in seeded().items():
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
