import json
import subprocess
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import anthropic
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.datastructures import UploadFile as StarletteUploadFile

from . import ask, brief, pipeline, store, updates
from .models import AskRequest, Assessment, BriefRequest, PipelineEvent
from .paths import CASES, FRONTEND_BUILD, REGULATIONS


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    store.load()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


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
        async for item in pipeline.run_assessment(spec_text, image_bytes, case_name or None):
            if isinstance(item, PipelineEvent):
                yield json.dumps(item.dump()) + "\n"
                continue
            if image_bytes:
                store.store_image(item.id, image_bytes)
                item = item.model_copy(update={"image_url": f"/api/assessments/{item.id}/image"})
            store.put(item)

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


@app.get("/api/assessments/{assessment_id}/updates")
def get_updates(assessment_id: str) -> JSONResponse:
    assessment = _find(assessment_id)
    found = updates.updates_for(assessment, store.applied.get(assessment_id, []))
    return JSONResponse([u.dump() for u in found])


@app.post("/api/assessments/{assessment_id}/updates/{regulation}")
def apply_update(assessment_id: str, regulation: str) -> JSONResponse:
    assessment = _find(assessment_id)
    done = store.applied.setdefault(assessment_id, [])
    if regulation not in done:
        update = next(
            (u for u in updates.updates_for(assessment, done) if u.regulation == regulation), None
        )
        if not update:
            raise HTTPException(404, f"No update for {regulation}")
        assessment = updates.apply_update(assessment, update)
        done.append(regulation)
        store.put(assessment)
    return JSONResponse(assessment.dump())


@app.post("/api/brief")
def get_brief(request: BriefRequest) -> JSONResponse:
    try:
        written = brief.brief_for(request.requirements)
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as e:
        raise HTTPException(503, f"Brief unavailable: {e}") from e
    return JSONResponse(written.dump())


@app.post("/api/ask")
def ask_question(request: AskRequest) -> JSONResponse:
    try:
        answer = ask.ask(request.question, request.selection, request.requirements)
    except ask.BudgetExceeded as e:
        raise HTTPException(429, str(e)) from e
    except (anthropic.APIError, RuntimeError) as e:
        raise HTTPException(502, f"No answer: {e}") from e
    return JSONResponse(answer.dump())


@app.get("/api/spend")
def get_spend() -> dict[str, float]:
    return {"spentUsd": ask.spent(), "budgetUsd": ask.BUDGET_USD}


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
