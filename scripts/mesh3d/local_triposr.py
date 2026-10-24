"""Run a cloned TripoSR on Apple MPS, using scikit-image for CPU marching cubes.

See README.md for the uv command and pinned upstream source revision.
"""

import argparse
import json
import sys
import time
import types
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from skimage.measure import marching_cubes


def cpu_marching_cubes(level, threshold):
    # TripoSR's helper expects torchmcubes' z/y/x vertex order.
    vertices, faces, _, _ = marching_cubes(level.detach().cpu().numpy(), threshold)
    return torch.from_numpy(vertices[:, [2, 1, 0]].copy()), torch.from_numpy(faces.copy())


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--source", type=Path, required=True, help="VAST-AI-Research/TripoSR checkout")
parser.add_argument("--output", type=Path, default=Path("web/frontend/static/mesh3d/dev-rear-lamp"))
parser.add_argument("--part", action="append")
parser.add_argument("--raw", action="store_true")
parser.add_argument("--resolution", type=int, default=256)
parser.add_argument("--device", choices=["mps", "cpu"], default="mps")
args = parser.parse_args()
sys.path.insert(0, str(args.source.resolve()))
mc = types.ModuleType("torchmcubes")
mc.marching_cubes = cpu_marching_cubes
sys.modules["torchmcubes"] = mc
from tsr.system import TSR

torch.set_num_threads(4)
started = time.monotonic()
print(f"Loading TripoSR on {args.device}", flush=True)
model = TSR.from_pretrained("stabilityai/TripoSR", config_name="config.yaml", weight_name="model.ckpt")
model.eval().to(args.device)
model.renderer.set_chunk_size(4096)
print(f"Model loaded in {time.monotonic() - started:.1f}s", flush=True)
manifest_path = args.output / "manifest.json"
manifest = json.loads(manifest_path.read_text())
for part in manifest["parts"]:
    if args.part and part["id"] not in args.part:
        continue
    started = time.monotonic()
    source = args.output / part["crop"] if args.raw else args.output / "renders" / f'{part["id"]}-transparent.png'
    image = Image.open(source).convert("RGBA")
    if args.raw:
        image.putalpha(image.convert("L").point(lambda value: 255 if value < 240 else 0))
    rgba = np.array(image).astype(np.float32) / 255
    rgb = rgba[:, :, :3] * rgba[:, :, 3:4] + (1 - rgba[:, :, 3:4]) * 0.5
    image = Image.fromarray((rgb * 255).astype(np.uint8))
    print(f'Inferring {part["id"]}', flush=True)
    with torch.no_grad():
        scene = model([image], device=args.device)
        mesh = model.extract_mesh(scene, has_vertex_color=False, resolution=args.resolution)[0]
    # TripoSR is Z-up and faces +X; the viewer uses Y-up and faces +Z.
    mesh.apply_transform(np.array([[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0], [0, 0, 0, 1]]))
    mesh.fix_normals(multibody=True)
    name = f'{part["id"]}-triposr-{"raw" if args.raw else "shaded"}.glb'
    mesh.export(args.output / name)
    part["file"] = name
    part["model"] = "TripoSR, local " + args.device
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    record = {"part": part["id"], "model": "TripoSR", "device": args.device,
              "shaded": not args.raw, "resolution": args.resolution,
              "seconds": round(time.monotonic() - started, 1), "faces": len(mesh.faces), "file": name}
    print(json.dumps(record), flush=True)
    with (args.output / "attempts.jsonl").open("a") as log:
        log.write(json.dumps(record) + "\n")
    del scene
    if args.device == "mps":
        torch.mps.empty_cache()
