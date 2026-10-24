"""Image crops, optional OpenRouter shading, and anonymous HF mesh generation.

Run with uv run --with pillow --with requests --with gradio_client scripts/mesh3d/pipeline.py --help.
"""

import argparse
import base64
import json
import os
import shutil
import time
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]


def prepare(args):
    regions = json.loads(args.regions.read_text())
    requirements = json.loads(args.requirements.read_text())["requirements"]
    image = Image.open(args.image).convert("RGB")
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "crops").mkdir(exist_ok=True)
    parts = []
    for part in regions["parts"]:
        polygon = [(round(x * image.width), round(y * image.height)) for x, y in part["polygon"]]
        mask = Image.new("L", image.size)
        ImageDraw.Draw(mask).polygon(polygon, fill=255)
        crop = Image.composite(image, Image.new("RGB", image.size, "white"), mask).crop(mask.getbbox())
        side = round(max(crop.size) * 1.16)
        square = Image.new("RGB", (side, side), "white")
        square.paste(crop, ((side - crop.width) // 2, (side - crop.height) // 2))
        square.resize((768, 768)).save(args.output / "crops" / f'{part["id"]}.png')
        ids = part.get("requirementIds")
        if ids is None:
            ids = [r["id"] for r in requirements if any(k.lower() in r["text"].lower() for k in part["keywords"])]
        parts.append({"id": part["id"], "name": part["name"], "file": None,
                      "order": part["depth"], "offset": [0, 0, part["depth"] * 1.3],
                      "requirementIds": ids, "crop": f'crops/{part["id"]}.png'})
    manifest = {"caseId": regions["caseId"], "mapping": "Supplied IDs where available; otherwise keyword matches, not reviewed compliance links.",
                "geometry": "Independent single-image inferences, not CAD or recovered assembly dimensions.",
                "parts": parts, "requirements": requirements}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def shade(args, part):
    import requests

    source = args.output / part["crop"]
    target = args.output / "renders" / source.name
    target.parent.mkdir(exist_ok=True)
    if target.exists():
        return target
    prompt = (f"Convert this patent line-art crop into one solid shaded 3D product render of the {part['name']} "
              "of an automotive rear lamp. Preserve the exact silhouette, visible features, holes, proportions and camera view. "
              "Do not add other parts or text. Neutral matte light gray material, visible thickness, diffuse studio lighting, "
              "pure white background. Interpret the lines as physical edges, not painted black lines. "
              "Only the object in this crop, centered with white margin.")
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", timeout=240,
                             headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
                             json={"model": args.image_model, "modalities": ["image", "text"],
                                   "messages": [{"role": "user", "content": [
                                       {"type": "text", "text": prompt},
                                       {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(source.read_bytes()).decode()}}]}]})
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    url = data["choices"][0]["message"]["images"][0]["image_url"]["url"]
    target.write_bytes(base64.b64decode(url.split(",", 1)[1]))
    return target


def generate(args):
    from gradio_client import Client, handle_file

    manifest_path = args.output / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    for part in manifest["parts"]:
        if args.part and part["id"] not in args.part:
            continue
        started = time.monotonic()
        record = {"part": part["id"], "model": args.model, "shaded": args.shade}
        try:
            source = shade(args, part) if args.shade else args.output / part["crop"]
            if args.transparent:
                image = Image.open(source).convert("RGBA")
                image.putalpha(image.convert("RGB").convert("L").point(lambda value: 255 if value < 240 else 0))
                source = args.output / "renders" / f'{part["id"]}-transparent.png'
                image.save(source)
            if args.shade_only:
                record["render"] = str(source)
            else:
                spaces = {"sf3d": "stabilityai/stable-fast-3d", "hunyuan": "Tencent/Hunyuan3D-2", "trellis2": "microsoft/TRELLIS.2"}
                client = Client(args.space or spaces[args.model], verbose=False)
                if args.model == "sf3d":
                    result = client.submit(input_image=handle_file(str(source)), foreground_ratio=0.85,
                                           remesh_option="None", vertex_count=-1, texture_size=512, api_name="/run_button").result(timeout=360)
                    mesh = result[1]
                elif args.model == "trellis2":
                    client.predict(api_name="/start_session")
                    processed = client.predict(input=handle_file(str(source)), api_name="/preprocess_image")
                    client.submit(image=processed, seed=1234, resolution="512", api_name="/image_to_3d").result(timeout=360)
                    result = client.submit(decimation_target=50000, texture_size=1024, api_name="/extract_glb").result(timeout=360)
                    mesh = result[0]
                else:
                    result = client.submit(image=handle_file(str(source)), steps=30, seed=1234,
                                           randomize_seed=False, check_box_rembg=not args.transparent,
                                           octree_resolution=256, api_name="/shape_generation").result(timeout=360)
                    mesh = result[0]
                    record["stats"] = result[2]
                if isinstance(mesh, dict):
                    mesh = mesh["value"]
                name = f'{part["id"]}-{args.model}-{"masked" if args.transparent else "shaded" if args.shade else "raw"}.glb'
                shutil.copyfile(mesh, args.output / name)
                part["file"] = name
                part["model"] = args.model
                record["file"] = name
                manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        except Exception as error:
            record["error"] = f"{type(error).__name__}: {error}"
        record["seconds"] = round(time.monotonic() - started, 1)
        print(json.dumps(record), flush=True)
        with (args.output / "attempts.jsonl").open("a") as log:
            log.write(json.dumps(record) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "generate"])
    parser.add_argument("--image", type=Path, default=ROOT / "cases/dev-rear-lamp/exploded_view.png")
    parser.add_argument("--regions", type=Path, default=ROOT / "web/frontend/static/parts3d/dev-rear-lamp/regions.json")
    parser.add_argument("--requirements", type=Path, default=ROOT / "cases/dev-rear-lamp/expected.json")
    parser.add_argument("--output", type=Path, default=ROOT / "web/frontend/static/mesh3d/dev-rear-lamp")
    parser.add_argument("--model", choices=["sf3d", "hunyuan", "trellis2"], default="hunyuan")
    parser.add_argument("--space", help="Override the HF Space, using the same model API")
    parser.add_argument("--part", action="append", help="Only process this part ID; repeatable")
    parser.add_argument("--shade", action="store_true")
    parser.add_argument("--shade-only", action="store_true")
    parser.add_argument("--transparent", action="store_true", help="Threshold the white render background and bypass remote rembg")
    parser.add_argument("--image-model", default="google/gemini-2.5-flash-image")
    args = parser.parse_args()
    prepare(args) if args.action == "prepare" else generate(args)
