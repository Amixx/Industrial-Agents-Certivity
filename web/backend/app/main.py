import asyncio
import json
import os
import subprocess
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import anthropic
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.datastructures import UploadFile as StarletteUploadFile

from . import ask, brief, pipeline, spend, store, updates
from .models import AskRequest, Assessment, BriefRequest, UpdateRun
from .paths import CASES, FRONTEND_BUILD, REGULATIONS


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    store.load()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/version")
def version() -> dict[str, str | None]:
    """The commit this image was built from; Render passes it in as RENDER_GIT_COMMIT."""
    return {"commit": os.environ.get("RENDER_GIT_COMMIT")}


@app.get("/api/cases")
def list_cases() -> list[str]:
    return sorted(p.name for p in CASES.iterdir() if p.is_dir())


@app.get("/api/cases/{case}")
def get_case(case: str) -> dict[str, str | None]:
    folder = CASES / case
    if "/" in case or not (folder / "spec.md").is_file():
        raise HTTPException(404, "Unknown case")
    image = folder / "exploded_view.png"
    return {
        "spec": (folder / "spec.md").read_text(),
        "image_url": f"/api/cases/{case}/image" if image.is_file() else None,
    }


@app.get("/api/cases/{case}/image")
def get_case_image(case: str) -> FileResponse:
    image = CASES / case / "exploded_view.png"
    if "/" in case or not image.is_file():
        raise HTTPException(404, "Unknown case")
    return FileResponse(image)


@app.post("/api/requirements")
async def requirements(
    spec: UploadFile | str | None = Form(None),
    image: UploadFile | None = File(None),
) -> Any:
    if isinstance(spec, UploadFile):
        spec = (await spec.read()).decode()
    return pipeline.run(spec, await image.read() if image else None)


def _find(assessment_id: str) -> Assessment:
    assessment = store.assessments.get(assessment_id)
    if not assessment:
        raise HTTPException(404, "Unknown assessment")
    return assessment


@app.post("/api/assessments")
async def create_assessment(
    spec: UploadFile | str = Form(...),
    image: UploadFile | None = File(None),
    case_name: str | None = Form(None),
) -> StreamingResponse:
    spec_text = (await spec.read()).decode() if isinstance(spec, StarletteUploadFile) else spec
    image_bytes = await image.read() if image else None

    async def stream() -> AsyncIterator[str]:
        async for event in pipeline.run_assessment(spec_text, image_bytes, case_name or None):
            yield json.dumps(event.dump()) + "\n"

    return StreamingResponse(stream(), media_type="application/x-ndjson")


@app.get("/api/assessments")
def list_assessments() -> JSONResponse:
    newest_first = sorted(store.assessments.values(), key=lambda a: a.created_at, reverse=True)
    return JSONResponse([a.dump() for a in newest_first])


@app.get("/api/assessments/{assessment_id}")
def get_assessment(assessment_id: str) -> JSONResponse:
    return JSONResponse(_find(assessment_id).dump())


@app.get("/api/assessments/{assessment_id}/image")
def get_assessment_image(assessment_id: str) -> FileResponse:
    path = store.image_path(assessment_id)
    if not path:
        raise HTTPException(404, "No image")
    return FileResponse(path)


def _run(assessment_id: str, run_id: str) -> UpdateRun:
    run = store.runs.get((assessment_id, run_id))
    if not run:
        raise HTTPException(404, "Unknown update run")
    return run


@app.get("/api/assessments/{assessment_id}/updates")
def get_updates(assessment_id: str) -> JSONResponse:
    """The assessment's cited regulations, each with the newest version in the corpus."""
    assessment = _find(assessment_id)
    found = updates.cited(assessment, store.runs_for(assessment_id))
    return JSONResponse([c.dump() for c in found])


@app.post("/api/assessments/{assessment_id}/updates")
async def create_update(
    assessment_id: str,
    file: UploadFile | None = File(None),
    regulation: str | None = Form(None),
    to_version: str | None = Form(None),
) -> JSONResponse:
    """Compare a cited regulation with a newer version: an uploaded PDF, or the newest version
    of `regulation` in the corpus. Refusals are 422 with a one-sentence `detail`."""
    assessment = _find(assessment_id)
    pdf = await file.read() if file else None
    runs = store.runs_for(assessment_id)
    try:
        old, new, identified_by, digest = await asyncio.to_thread(
            updates.resolve,
            assessment,
            pdf,
            file.filename if file else None,
            regulation,
            to_version or None,
            runs,
            store.upload_dir(),
        )
        file_name = (file.filename if file else None) or new.pdf.name
        run_id = updates.run_id(old.regulation, new.version, digest)
        stored = store.runs.get((assessment_id, run_id))
        if stored and stored.from_version == old.version and not updates.engine_available():
            return JSONResponse(stored.dump())
        if not updates.engine_available():
            raise HTTPException(503, "The diff engine is not installed on this server.")
        run = await asyncio.to_thread(
            updates.compare, assessment, old, new, identified_by, digest, file_name
        )
    except updates.Refusal as e:
        return JSONResponse({"detail": str(e), "code": e.code, **e.extra}, status_code=422)
    store.put_run(run)
    return JSONResponse(run.dump())


@app.get("/api/assessments/{assessment_id}/updates/{run_id}")
def get_update(assessment_id: str, run_id: str) -> JSONResponse:
    _find(assessment_id)
    return JSONResponse(_run(assessment_id, run_id).dump())


@app.post("/api/assessments/{assessment_id}/updates/{run_id}/apply")
def apply_update(assessment_id: str, run_id: str) -> JSONResponse:
    assessment = _find(assessment_id)
    run = _run(assessment_id, run_id)
    if not run.applied:
        cited = next((d for d in assessment.regulations if d.regulation == run.regulation), None)
        if not cited or cited.version != run.from_version:
            raise HTTPException(
                409,
                f"This assessment cites {run.regulation} {cited.version if cited else 'no version'}"
                f", not {run.from_version}.",
            )
        store.before[assessment_id, run_id] = assessment
        assessment = updates.apply_update(assessment, run)
        store.assessments[assessment.id] = assessment
        store.put_run(run.model_copy(update={"applied": True}))
    return JSONResponse(assessment.dump())


@app.post("/api/assessments/{assessment_id}/updates/{run_id}/undo")
def undo_update(assessment_id: str, run_id: str) -> JSONResponse:
    """Put the assessment back as it was before the run was applied."""
    _find(assessment_id)
    run = _run(assessment_id, run_id)
    snapshot = store.before.pop((assessment_id, run_id), None)
    if not run.applied or not snapshot:
        raise HTTPException(409, "This update is not applied.")
    store.assessments[assessment_id] = snapshot
    store.put_run(run.model_copy(update={"applied": False}))
    return JSONResponse(snapshot.dump())


@app.post("/api/brief")
def get_brief(request: BriefRequest) -> JSONResponse:
    if not request.write:
        found = brief.cached(request.requirements)
        if found is None:
            raise HTTPException(404, "No brief written yet")
        return JSONResponse(found.dump())
    try:
        written = brief.brief_for(request.requirements)
    except (
        RuntimeError,
        OSError,
        subprocess.TimeoutExpired,
        spend.BudgetExceeded,
        anthropic.APIError,
    ) as e:
        raise HTTPException(503, f"Brief unavailable: {e}") from e
    return JSONResponse(written.dump())


@app.post("/api/ask")
def ask_question(request: AskRequest) -> JSONResponse:
    try:
        answer = ask.ask(request.question, request.selection, request.requirements)
    except spend.BudgetExceeded as e:
        raise HTTPException(429, str(e)) from e
    except (anthropic.APIError, RuntimeError) as e:
        raise HTTPException(502, f"No answer: {e}") from e
    return JSONResponse(answer.dump())


@app.get("/api/spend")
def get_spend() -> dict[str, float]:
    return {"spentUsd": spend.spent(), "budgetUsd": spend.BUDGET_USD}


@app.get("/api/regulations")
def regulations() -> Any:
    return json.loads((REGULATIONS / "index.json").read_text())


app.mount("/pdfs", StaticFiles(directory=REGULATIONS / "pdf"), name="pdfs")

if FRONTEND_BUILD.is_dir():

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str) -> FileResponse:
        if path.startswith("api/"):
            raise HTTPException(404)
        file = (FRONTEND_BUILD / path).resolve()
        if file.is_file() and file.is_relative_to(FRONTEND_BUILD.resolve()):
            return FileResponse(file)
        return FileResponse(FRONTEND_BUILD / "index.html")
