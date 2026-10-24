import json

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import pipeline
from .paths import CASES, FRONTEND_BUILD, REGULATIONS

app = FastAPI()


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/cases")
def list_cases():
    return sorted(p.name for p in CASES.iterdir() if p.is_dir())


@app.get("/api/cases/{case}")
def get_case(case: str):
    folder = CASES / case
    if "/" in case or not (folder / "spec.md").is_file():
        raise HTTPException(404, "Unknown case")
    image = folder / "exploded_view.png"
    return {
        "spec": (folder / "spec.md").read_text(),
        "image_url": f"/api/cases/{case}/image" if image.is_file() else None,
    }


@app.get("/api/cases/{case}/image")
def get_case_image(case: str):
    image = CASES / case / "exploded_view.png"
    if "/" in case or not image.is_file():
        raise HTTPException(404, "Unknown case")
    return FileResponse(image)


@app.post("/api/requirements")
async def requirements(
    spec: UploadFile | str | None = Form(None),
    image: UploadFile | None = File(None),
):
    if isinstance(spec, UploadFile):
        spec = (await spec.read()).decode()
    return pipeline.run(spec, await image.read() if image else None)


@app.get("/api/regulations")
def regulations():
    return json.loads((REGULATIONS / "index.json").read_text())


app.mount("/pdfs", StaticFiles(directory=REGULATIONS / "pdf"), name="pdfs")

if FRONTEND_BUILD.is_dir():

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path.startswith("api/"):
            raise HTTPException(404)
        file = (FRONTEND_BUILD / path).resolve()
        if file.is_file() and file.is_relative_to(FRONTEND_BUILD.resolve()):
            return FileResponse(file)
        return FileResponse(FRONTEND_BUILD / "index.html")
