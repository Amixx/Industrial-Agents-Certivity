"""The regulation update endpoints: upload, the version guard, the whole-file guard and apply.

These run the real diff engine in the brain's environment (brain/.venv) on the corpus PDFs.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import store, updates
from app.main import app
from app.paths import REGULATIONS

LAMP = "f14b0208"
BUMPER = "8f93fc71"
PDF = REGULATIONS / "pdf"

pytestmark = pytest.mark.skipif(not updates.engine_available(), reason="brain/.venv is missing")


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setattr(store, "_FILE", tmp_path / "assessments.json")
    monkeypatch.setattr(store, "_UPLOADS", tmp_path / "uploads")
    for table in (store.assessments, store.runs, store.before):
        table.clear()
    with TestClient(app) as c:
        yield c


def upload(client: TestClient, assessment: str, pdf: Path, **form: str) -> dict:
    with pdf.open("rb") as f:
        res = client.post(
            f"/api/assessments/{assessment}/updates",
            files={"file": (pdf.name, f, "application/pdf")},
            data=form,
        )
    return {"status": res.status_code, **res.json()}


def test_cited_regulations_list_newer_versions(client: TestClient) -> None:
    rows = {r["regulation"]: r for r in client.get(f"/api/assessments/{LAMP}/updates").json()}
    assert rows["UN R148"]["version"] == "1.6.0"
    assert rows["UN R148"]["latest"] == "1.7.0"
    assert rows["UN R148"]["requirementCount"] == 63
    assert rows["UN R148"]["run"].startswith("r148-1.7.0-")
    assert "latest" not in rows["UN R150"]


def test_upload_and_compare_open_the_same_run(client: TestClient) -> None:
    run = upload(client, LAMP, PDF / "UN_R148" / "latest" / "UN_R148_latest.pdf")
    assert run["status"] == 200
    assert (run["regulation"], run["fromVersion"], run["toVersion"]) == (
        "UN R148",
        "1.6.0",
        "1.7.0",
    )
    assert run["identifiedBy"] == "sha256"
    hunk = next(h for h in run["hunks"] if h["label"] == "5.13.1.1")
    assert (hunk["status"], hunk["page"]) == ("new", 27)
    assert hunk["changes"] and all(c.startswith("U-R148-") for c in hunk["changes"])
    added = [c for c in run["changes"] if c["change"] == "added"]
    assert len(added) == 10

    compared = client.post(f"/api/assessments/{LAMP}/updates", data={"regulation": "UN R148"})
    assert compared.json()["id"] == run["id"]
    assert client.get(f"/api/assessments/{LAMP}/updates/{run['id']}").json()["id"] == run["id"]


def test_front_bumper_r127(client: TestClient) -> None:
    run = upload(client, BUMPER, PDF / "UN_R127" / "latest" / "UN_R127_latest.pdf")
    assert run["status"] == 200
    assert (run["fromVersion"], run["toVersion"]) == ("4.3.0", "4.4.0")
    assert {h["status"] for h in run["hunks"]} >= {"amended", "new", "deleted"}


def test_unrelated_regulation_is_refused(client: TestClient) -> None:
    res = upload(client, LAMP, PDF / "UN_R127" / "latest" / "UN_R127_latest.pdf")
    assert res["status"] == 422
    assert res["detail"] == (
        "This file is UN R127 4.4.0, which this assessment does not cite "
        "(it cites UN R48, UN R148, UN R150 and UN R10)."
    )


def test_cited_version_is_refused(client: TestClient) -> None:
    res = upload(client, LAMP, PDF / "UN_R148" / "base" / "UN_R148_base.pdf")
    assert res["status"] == 422
    assert res["detail"] == "This is UN R148 1.6.0, the version this assessment already cites."


def test_whole_file_guard(client: TestClient) -> None:
    """A file that names R148 but holds another regulation is not diffed paragraph by paragraph."""
    lamp = store.assessments[LAMP]
    old = updates.Version("UN R148", "1.6.0", PDF / "UN_R148" / "base" / "UN_R148_base.pdf")
    new = updates.Version("UN R148", "1.8.0", PDF / "UN_R48" / "latest" / "UN_R48_latest.pdf")
    with pytest.raises(updates.Refusal) as refused:
        updates.compare(lamp, old, new, "first page", "0" * 64, "other.pdf")
    assert refused.value.code == "mismatch"
    assert str(refused.value).startswith(
        "This file does not match UN R148 1.6.0 closely enough to compare paragraph by paragraph"
    )


def test_unknown_file_needs_a_version(client: TestClient, tmp_path: Path) -> None:
    """A PDF that is not in the corpus is identified from its first page."""
    copy = tmp_path / "UN R148 1.7.0.pdf"
    copy.write_bytes((PDF / "UN_R148" / "latest" / "UN_R148_latest.pdf").read_bytes() + b"\n")
    res = upload(client, LAMP, copy)
    assert (res["status"], res["code"], res["regulation"]) == (422, "version_needed", "UN R148")
    assert res["version"] == "1.7.0"
    run = upload(client, LAMP, copy, to_version="1.7.0")
    assert (run["status"], run["identifiedBy"]) == (200, "first page")


def test_apply_then_reupload_and_undo(client: TestClient) -> None:
    run = upload(client, LAMP, PDF / "UN_R148" / "latest" / "UN_R148_latest.pdf")
    before = client.get(f"/api/assessments/{LAMP}").json()
    applied = client.post(f"/api/assessments/{LAMP}/updates/{run['id']}/apply").json()
    r148 = next(d for d in applied["regulations"] if d["regulation"] == "UN R148")
    added = sum(1 for c in run["changes"] if c["change"] == "added")
    assert (r148["version"], r148["requirementCount"]) == ("1.7.0", 63 + added)
    assert len(applied["requirements"]) == len(before["requirements"]) + added
    assert all(
        r["source"]["version"] == "1.7.0"
        for r in applied["requirements"]
        if r["source"]["regulation"] == "UN R148"
    )

    again = upload(client, LAMP, PDF / "UN_R148" / "latest" / "UN_R148_latest.pdf")
    assert again["detail"] == "UN R148 1.7.0 is already applied to this assessment."

    undone = client.post(f"/api/assessments/{LAMP}/updates/{run['id']}/undo").json()
    assert undone == before
