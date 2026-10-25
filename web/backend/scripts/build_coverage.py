"""Build the coverage page's data from the files in out/. Run from web/backend:

    uv run python -m scripts.build_coverage

Writes
- app/coverage_data/uploads.json: the platform's scores for each uploaded file in out/, keyed by
  the fingerprint of its requirement list, from the run logs in out/README.md;
- app/seeds.json: the best dev upload and the final held-out upload as stored assessments, with
  the scores of the paragraphs their runs cut;
- app/coverage_data/<fingerprint>.json: the local judge's output for every stored assessment that
  has an expert answer, so the page works without the brain's venv.

The best dev upload's section scores are read from its checkpoint branch, which keeps the inputs
of the run (`git fetch` it first). No model is called.
"""

import hashlib
import importlib.util
import json
import math
import re
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

from app import coverage, pipeline
from app.models import Assessment, CutParagraph, Requirement, RunCost
from app.paths import CASES, ROOT

OUT = ROOT / "out"
APP = Path(coverage.__file__).parent
CHECKPOINT = "origin/checkpoint/0794-consolidate-v2"

# (file in out/, case, name in the app, when the file was built in UTC)
SEEDS = [
    ("rear-lamp-consolidate-v2.json", "dev-rear-lamp", "Rear lamp, F2 0.794", "03:50"),
    ("heldout-silver-r10r148.json", "heldout-front-bumper", "Front bumper, F2 0.706", "08:16"),
]

_spec = importlib.util.spec_from_file_location("score_local", ROOT / "tools" / "score_local.py")
assert _spec and _spec.loader
_score_local = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_score_local)
paragraph_key = _score_local._paragraph_key

_FILE = re.compile(r"`([\w.-]+\.json)`")
_DEV = re.compile(r"\(([^()]*?\d\d:\d\d[^()]*?)\)\s*\**(\d+) / (0\.\d+)")
_HELDOUT = re.compile(r"([\d.]+)% / ([\d.]+)% / \**([\d.]+)%")


def uploads() -> dict[str, list[dict[str, Any]]]:
    """The platform's scores per file name, from the three run log tables that record them."""
    found: dict[str, list[dict[str, Any]]] = defaultdict(list)
    section = ""
    for line in (OUT / "README.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            section = line
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        names = _FILE.findall(cells[1]) if line.startswith("| ") and len(cells) > 6 else []
        if section == "## Run log" and names:
            day = "25 Oct" if "25 Oct" in cells[0] else "24 Oct"
            for at, matched, f2 in _DEV.findall(cells[6]):
                at = at if "Oct" in at else f"{day} {at}"
                found[names[0]].append({"at": at, "matched": int(matched), "f2": float(f2)})
        elif section.startswith("## Held-out run log") and names:
            if m := _HELDOUT.search(cells[5]):
                p, r, f2 = (round(float(x) / 100, 3) for x in m.groups())
                at = f"25 Oct {cells[0]} CET"
                found[names[0]].append({"at": at, "f2": f2, "precision": p, "recall": r})
        elif section == "### Platform scores" and names:
            p, r, f2 = (float(x) for x in re.findall(r"[\d.]+", cells[3])[:3])
            found[names[0]].append(
                {
                    "at": "24 Oct 20:05 to 20:23 CEST",
                    "matched": int(cells[4]),
                    "f2": f2,
                    "precision": p,
                    "recall": r,
                }
            )
    return found


def requirements(path: Path) -> list[Requirement] | None:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("requirements") if isinstance(data, dict) else None
    try:
        return [Requirement.model_validate(r) for r in rows] if rows else None
    except ValueError:
        return None


def upload_index() -> dict[str, dict[str, Any]]:
    scores = uploads()
    index = {}
    for name, found in sorted(scores.items()):
        path = OUT / name
        rows = requirements(path) if path.is_file() else None
        if rows:
            index[coverage.fingerprint(rows)] = {"file": name, "rows": len(rows), "uploads": found}
    return index


def _git_json(path: str) -> Any:
    shown = subprocess.run(
        ["git", "show", f"{CHECKPOINT}:{path}"], capture_output=True, check=True, cwd=ROOT
    )
    return json.loads(shown.stdout)


def _cut(source: dict[str, Any], score: float, cut: float, stage: str) -> CutParagraph:
    return CutParagraph.model_validate(
        {**source, "score": round(score, 3), "cut": cut, "stage": stage}
    )


def lamp_below_cut(final: list[dict[str, Any]]) -> list[CutParagraph]:
    """Paragraphs the 0.794 file's run cut at its section stage: no row with p_keep times the
    square root of the section score at 0.3535 or more (checkpoint `repro/section_stage.py`)."""
    rows = _git_json("repro/j20f-all.json")["requirements"]
    p_keep = _git_json("repro/j20f-all.pkeep.json")
    p_section = _git_json("repro/p_section.json")
    cited = {(r["source"]["regulation"], r["source"]["paragraph"]) for r in final}
    best: dict[tuple[str, str], tuple[dict[str, Any], float]] = {}
    for row, pk in zip(rows, p_keep, strict=True):
        s = row["source"]
        key = (s["regulation"], s["paragraph"])
        ps = p_section.get(f"{s['regulation']}|{paragraph_key(s['paragraph'])}", 1.0)
        score = pk * math.sqrt(ps)
        if score > best.get(key, (s, -1.0))[1]:
            best[key] = (s, score)
    return [
        _cut(s, score, 0.3535, "section")
        for key, (s, score) in best.items()
        if key not in cited and score < 0.3535
    ]


def bumper_below_cut(final: list[dict[str, Any]]) -> list[CutParagraph]:
    """Paragraphs of `heldout-api.json` the final held-out file cut by confidence: under 0.25 in
    UN R48, under 0.20 in UN R10 and UN R148 (see the held-out run log)."""
    cuts = {"UN R48": 0.25, "UN R10": 0.20, "UN R148": 0.20}
    rows = json.loads((OUT / "heldout-api.json").read_text(encoding="utf-8"))["requirements"]
    cited = {(r["source"]["regulation"], r["source"]["paragraph"]) for r in final}
    found: dict[tuple[str, str], CutParagraph] = {}
    for row in rows:
        s, score = row["source"], row["confidence"]
        key = (s["regulation"], s["paragraph"])
        cut = cuts.get(s["regulation"])
        if cut and key not in cited and score < cut:
            found[key] = _cut(s, score, cut, "confidence")
    return list(found.values())


def seed(name: str, case: str, case_name: str, at: str) -> Assessment:
    submission = json.loads((OUT / name).read_text(encoding="utf-8"))
    final = submission["requirements"]
    below = lamp_below_cut(final) if case == "dev-rear-lamp" else bumper_below_cut(final)
    spec = (CASES / case / "spec.md").read_text(encoding="utf-8")
    built = pipeline._assessment(submission, spec, case_name, RunCost(total_usd=0, models=[]))
    return built.model_copy(
        update={
            "id": hashlib.sha256(name.encode()).hexdigest()[:8],
            "created_at": f"2026-10-25T{at}:00.000Z",
            "cost": None,
            "image_url": f"/api/cases/{case}/image",
            "below_cut": sorted(below, key=lambda c: (c.regulation, -c.score)),
        }
    )


def main() -> None:
    data = coverage.DATA
    data.mkdir(exist_ok=True)
    index = upload_index()
    (data / "uploads.json").write_text(json.dumps(index, indent=1) + "\n")
    print(f"uploads.json: {len(index)} uploaded files")
    seeds = [seed(*s) for s in SEEDS]
    (APP / "seeds.json").write_text(json.dumps([s.dump() for s in seeds], indent=1) + "\n")
    showcase = Assessment.model_validate_json((APP / "showcase.json").read_text())
    for old in data.glob("*.json"):
        if old.name != "uploads.json":
            old.unlink()
    for a in [showcase, *seeds]:
        case = coverage.case_of(a)
        expected = CASES / case / "expected.json" if case else None
        key = coverage.fingerprint(a.requirements)
        line = f"{a.id} {a.case_name}: platform {'yes' if key in index else 'no'}"
        if expected and expected.is_file():
            judged = coverage.judge(a, expected)
            (data / f"{key}.json").write_text(json.dumps(judged, ensure_ascii=False) + "\n")
            line += f", local matched {judged['local']['matched']}, missed {len(judged['missed'])}"
        print(line)


if __name__ == "__main__":
    main()
