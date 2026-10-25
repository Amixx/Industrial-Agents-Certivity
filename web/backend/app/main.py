import json
import os
import subprocess
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import anthropic
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.datastructures import UploadFile as StarletteUploadFile

from . import ask, brief, coverage, pipeline, spend, store, updates, voice
from .models import AskRequest, Assessment, BriefRequest, ReadAnswer, ReadRequest
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
        "spec": (folder / "spec.md").read_text(encoding="utf-8"),
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


@app.get("/api/assessments/{assessment_id}/updates")
def get_updates(assessment_id: str) -> JSONResponse:
    assessment = _find(assessment_id)
    found = updates.updates_for(assessment, store.applied.get(assessment_id, []))
    return JSONResponse([u.dump() for u in found])


@app.get("/api/assessments/{assessment_id}/coverage")
def get_coverage(assessment_id: str) -> JSONResponse:
    try:
        found = coverage.coverage_for(_find(assessment_id))
    except (OSError, subprocess.SubprocessError) as e:
        raise HTTPException(503, f"Local judge unavailable: {e}") from e
    return JSONResponse(found.dump())


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


@app.post("/api/read")
def read_aloud(request: ReadRequest) -> JSONResponse:
    assessment = _find(request.assessment_id)
    written = brief.cached(assessment.requirements)
    report = [assessment.dump(), written.dump() if written else None]
    text = voice.readable(request.text, report)
    if not text:
        raise HTTPException(422, "Nothing in the selection to read")
    speech_id = voice.remember(text) if voice.enabled() else None
    return JSONResponse(ReadAnswer(text=text, speech_id=speech_id).dump())


@app.get("/api/speak/{speech_id}")
def speak(speech_id: str) -> Response:
    try:
        mp3 = voice.audio(speech_id)
    except KeyError as e:
        raise HTTPException(404, "Unknown answer") from e
    except OSError as e:
        raise HTTPException(502, f"No voice: {e}") from e
    return Response(mp3, media_type="audio/mpeg")


@app.get("/api/spend")
def get_spend() -> dict[str, float]:
    return {"spentUsd": spend.spent(), "budgetUsd": spend.BUDGET_USD}


@app.get("/api/regulations")
def regulations() -> Any:
    return json.loads((REGULATIONS / "index.json").read_text(encoding="utf-8"))


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
