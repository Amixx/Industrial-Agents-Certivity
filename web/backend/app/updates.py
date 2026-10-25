"""Regulation updates: compare a cited regulation with a newer version and apply the result.

The diff runs `brain.subgoal` in the brain's own environment through `subgoal_runner.py`.
A run is stored under a stable id, so its page survives a reload; the precomputed runs of the
seeded assessments are in data/regulation-updates/ (`python -m app.demo_data` writes them).
"""

import hashlib
import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import (
    Assessment,
    CitedRegulation,
    Hunk,
    Requirement,
    RequirementChange,
    RunStats,
    Source,
    UpdateRun,
)
from .paths import BRAIN, BRAIN_PYTHON, REGULATIONS, SUBGOAL_RUNNER
from .pipeline import regulation_index

# Below this share of the old version's units found unchanged in the upload, the upload is a
# different document or a full rewrite, and a paragraph diff would be noise. The four corpus
# pairs the demo uses keep 95% to 99%, a different regulation as the new version 1% to 5%.
MIN_UNCHANGED_SHARE = 0.5
RUN_TIMEOUT_S = 60


class Refusal(Exception):
    """An upload the app does not compare, with the sentence that says why."""

    def __init__(self, message: str, code: str = "refused", **extra: Any) -> None:
        super().__init__(message)
        self.code = code
        self.extra = extra


@dataclass(frozen=True)
class Version:
    regulation: str
    version: str
    pdf: Path


def _versions(regulation: str) -> list[Version]:
    entry = next((r for r in regulation_index() if r["regulation"] == regulation), None)
    if not entry:
        return []
    slug = regulation.replace(" ", "_")
    return [
        Version(regulation, v["version_label"], REGULATIONS / "pdf" / slug / v["role"] / f["name"])
        for v in entry["versions"]
        for f in v.get("files", [])[:1]
    ]


def _by_sha(digest: str) -> Version | None:
    for entry in regulation_index():
        for v in entry["versions"]:
            for f in v.get("files", []):
                if f.get("sha256") == digest:
                    slug = entry["regulation"].replace(" ", "_")
                    pdf = REGULATIONS / "pdf" / slug / v["role"] / f["name"]
                    return Version(entry["regulation"], v["version_label"], pdf)
    return None


def _key(version: str) -> tuple[int, ...]:
    return tuple(int(n) for n in re.findall(r"\d+", version))


def latest(regulation: str) -> Version | None:
    found = [v for v in _versions(regulation) if v.pdf.is_file()]
    return max(found, key=lambda v: _key(v.version)) if found else None


def _title(regulation: str) -> str:
    return next((r["title"] for r in regulation_index() if r["regulation"] == regulation), "")


def run_id(regulation: str, to_version: str, digest: str) -> str:
    """ "r148-1.7.0-3fa2c1": the regulation, the new version and the new file."""
    short = regulation.removeprefix("UN ").replace(" ", "").lower()
    return f"{short}-{to_version}-{digest[:6]}"


def cited(assessment: Assessment, runs: list[UpdateRun]) -> list[CitedRegulation]:
    """The assessment's included regulations, each with the newest version in the corpus."""
    out = []
    for d in assessment.regulations:
        if not d.included:
            continue
        newest = latest(d.regulation)
        newer = newest.version if newest and _key(newest.version) > _key(d.version) else None
        mine = [r for r in runs if r.regulation == d.regulation]
        out.append(
            CitedRegulation(
                regulation=d.regulation,
                title=d.title or _title(d.regulation),
                version=d.version,
                latest=newer,
                requirement_count=sum(
                    1 for r in assessment.requirements if r.source.regulation == d.regulation
                ),
                run=next(
                    (
                        r.id
                        for r in mine
                        if r.from_version == d.version and r.to_version == newer and not r.applied
                    ),
                    None,
                ),
                applied_run=next(
                    (r.id for r in mine if r.applied and r.to_version == d.version), None
                ),
            )
        )
    return out


def identify(pdf: Path) -> dict[str, str | None]:
    """The regulation and version printed on the PDF's first page."""
    out = subprocess.run(
        [str(BRAIN_PYTHON), str(SUBGOAL_RUNNER), "identify", str(pdf)],
        cwd=BRAIN,
        env=_env(),
        capture_output=True,
        text=True,
        timeout=RUN_TIMEOUT_S,
        check=True,
    )
    found: dict[str, str | None] = json.loads(out.stdout)
    return found


def _env() -> dict[str, str]:
    return {**os.environ, "PYTHONPATH": str(BRAIN)}


def engine_available() -> bool:
    return BRAIN_PYTHON.is_file()


def _diff(request: dict[str, Any]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp:
        req, out = Path(tmp, "request.json"), Path(tmp, "out.json")
        req.write_text(json.dumps(request))
        proc = subprocess.run(
            [str(BRAIN_PYTHON), str(SUBGOAL_RUNNER), "diff", str(req), str(out)],
            cwd=BRAIN,
            env=_env(),
            capture_output=True,
            text=True,
            timeout=RUN_TIMEOUT_S,
        )
        if proc.returncode or not out.is_file():
            raise RuntimeError(proc.stderr.strip().splitlines()[-1] if proc.stderr else "no output")
        result: dict[str, Any] = json.loads(out.read_text())
    return result


def resolve(
    assessment: Assessment,
    pdf: bytes | None,
    file_name: str | None,
    regulation: str | None,
    to_version: str | None,
    runs: list[UpdateRun],
    upload_dir: Path,
) -> tuple[Version, Version, str, str]:
    """(old version, new version, how the new one was identified, its SHA-256) for an upload or
    a corpus comparison. Raises Refusal with the reason when there is nothing to compare."""
    identified_by = "corpus"
    if pdf is not None:
        digest = hashlib.sha256(pdf).hexdigest()
        found = _by_sha(digest)
        if found:
            new, identified_by = found, "sha256"
        else:
            upload_dir.mkdir(parents=True, exist_ok=True)
            path = upload_dir / f"{digest}.pdf"
            path.write_bytes(pdf)
            if not pdf.startswith(b"%PDF"):
                raise Refusal("This file is not a PDF.")
            seen = identify(path)
            if not seen["regulation"]:
                raise Refusal("This PDF does not name a UN Regulation on its first page.")
            if not to_version:
                raise Refusal(
                    f"This file of {seen['regulation']} is not in the corpus. "
                    "Enter the version it holds to compare it.",
                    code="version_needed",
                    regulation=seen["regulation"],
                    version=seen["version"],
                )
            new, identified_by = Version(seen["regulation"], to_version, path), "first page"
    else:
        if not regulation:
            raise Refusal("Upload a PDF or pick a cited regulation to compare.")
        newest = latest(regulation)
        if not newest:
            raise Refusal(f"No version of {regulation} is in the corpus.")
        new = newest
        digest = hashlib.sha256(new.pdf.read_bytes()).hexdigest()

    decision = next(
        (d for d in assessment.regulations if d.included and d.regulation == new.regulation), None
    )
    if not decision:
        names = [d.regulation for d in assessment.regulations if d.included]
        listed = ", ".join(names[:-1]) + f" and {names[-1]}" if len(names) > 1 else "".join(names)
        raise Refusal(
            f"This file is {new.regulation} {new.version}, which this assessment does not cite "
            f"(it cites {listed})."
        )
    if new.version == decision.version:
        if any(
            r.applied and r.regulation == new.regulation and r.to_version == new.version
            for r in runs
        ):
            raise Refusal(f"{new.regulation} {new.version} is already applied to this assessment.")
        raise Refusal(
            f"This is {new.regulation} {new.version}, the version this assessment already cites."
        )
    if _key(new.version) < _key(decision.version):
        raise Refusal(
            f"This is {new.regulation} {new.version}, older than the {decision.version} "
            "this assessment cites."
        )
    old = next(
        (v for v in _versions(new.regulation) if v.version == decision.version and v.pdf.is_file()),
        None,
    )
    if not old:
        raise Refusal(f"No PDF of {new.regulation} {decision.version} is on file to compare with.")
    return old, new, identified_by, digest


def compare(
    assessment: Assessment,
    old: Version,
    new: Version,
    identified_by: str,
    digest: str,
    file_name: str,
) -> UpdateRun:
    """Run the diff and build the stored run. Raises Refusal when the files are too far apart."""
    requirements = [
        r.model_dump(include={"id", "text", "source"})
        for r in assessment.requirements
        if r.source.regulation == old.regulation
    ]
    result = _diff(
        {
            "old_pdf": str(old.pdf),
            "new_pdf": str(new.pdf),
            "regulation": old.regulation,
            "from_version": old.version,
            "to_version": new.version,
            "requirements": requirements,
        }
    )
    stats = RunStats.model_validate(result["stats"])
    if stats.unchanged_share < MIN_UNCHANGED_SHARE:
        raise Refusal(
            f"This file does not match {old.regulation} {old.version} closely enough to compare "
            f"paragraph by paragraph: {stats.unchanged_share:.0%} of its sentences are found "
            "unchanged.",
            code="mismatch",
        )
    return build_run(assessment, old, new, identified_by, digest, file_name, result, stats)


def build_run(
    assessment: Assessment,
    old: Version,
    new: Version,
    identified_by: str,
    digest: str,
    file_name: str,
    result: dict[str, Any],
    stats: RunStats,
) -> UpdateRun:
    paragraph = {r.id: r.source.paragraph for r in assessment.requirements}
    text = {r.id: r.text for r in assessment.requirements}
    taken = set(paragraph)
    short = old.regulation.removeprefix("UN ").replace(" ", "")
    changes: list[RequirementChange] = []
    added = 0
    for raw in result["changes"]:
        c = RequirementChange.model_validate(raw)
        rid = c.requirement_id
        if c.change == "added":
            added += 1
            while f"U-{short}-{added:02d}" in taken:
                added += 1
            c.new_id = f"U-{short}-{added:02d}"
            taken.add(c.new_id)
        elif rid:
            c.old_paragraph = paragraph.get(rid)
            c.old_text = text.get(rid)
        changes.append(c)

    hunks = [Hunk.model_validate(h) for h in result["hunks"]]
    by_label = {h.label: h for h in hunks if h.status != "deleted"}
    by_old = {h.old_label: h for h in hunks if h.old_label}
    for c in changes:
        cid = c.requirement_id or c.new_id
        if c.change == "removed":
            hunk = by_old.get(c.old_paragraph or "") or next(
                (h for h in hunks if c.requirement_id in h.cited_by), None
            )
        else:
            hunk = by_label.get(c.source.paragraph) if c.source else None
        if hunk and cid:
            c.hunk = hunk.id
            hunk.changes.append(cid)

    return UpdateRun(
        id=run_id(old.regulation, new.version, digest),
        assessment_id=assessment.id,
        regulation=old.regulation,
        title=_title(old.regulation),
        from_version=old.version,
        to_version=new.version,
        created_at=datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        identified_by=identified_by,  # type: ignore[arg-type]
        file_name=file_name,
        stats=stats,
        hunks=hunks,
        changes=changes,
    )


def apply_update(assessment: Assessment, update: UpdateRun) -> Assessment:
    regulation = update.regulation
    requirements = [
        r.model_copy(update={"source": r.source.model_copy(update={"version": update.to_version})})
        if r.source.regulation == regulation
        else r
        for r in assessment.requirements
    ]
    for change in update.changes:
        if change.change == "removed":
            requirements = [r for r in requirements if r.id != change.requirement_id]
        elif change.change == "modified":
            requirements = [
                r.model_copy(
                    update={
                        "text": change.new_text or r.text,
                        "source": r.source.model_copy(
                            update=change.source.model_dump() if change.source else {}
                        ),
                    }
                )
                if r.id == change.requirement_id
                else r
                for r in requirements
            ]
        else:
            requirements.append(
                Requirement(
                    id=change.new_id or f"U-{len(requirements)}",
                    text=change.new_text or "",
                    source=Source(
                        regulation=regulation,
                        version=update.to_version,
                        page=change.source.page if change.source else 0,
                        paragraph=change.source.paragraph if change.source else "",
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
