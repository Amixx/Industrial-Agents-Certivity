# Image-to-mesh spike

The working path is polygon crops → OpenRouter shaded images → explicit white-background masks → local TripoSR on MPS → individual GLBs → three.js. It produces real surfaces, not textured image planes. It does **not** recover CAD, hidden geometry, physical dimensions, or assembly constraints.

## Re-run the rear lamp

Run from the repository root. Python dependencies stay in uv's cache, outside the backend.

```sh
uv run --with pillow --with requests --with gradio_client \
  scripts/mesh3d/pipeline.py prepare

# Uses the paid OpenRouter image model. Existing renders are reused.
source ~/.config/secrets/secrets.env
uv run --with pillow --with requests --with gradio_client \
  scripts/mesh3d/pipeline.py generate --shade --shade-only --transparent

git clone https://github.com/VAST-AI-Research/TripoSR.git /tmp/mesh3d-triposr
git -C /tmp/mesh3d-triposr checkout 107cefdc244c39106fa830359024f6a2f1c78871

uv run --python 3.11 \
  --with 'torch>=2.6' --with 'transformers==4.35.0' \
  --with omegaconf --with einops --with pillow --with trimesh \
  --with scikit-image --with imageio --with 'huggingface-hub<1' \
  --with 'rembg[cpu]' \
  python scripts/mesh3d/local_triposr.py --source /tmp/mesh3d-triposr
```

The first local run downloads approximately 1.68 GB of model weights. Later runs reuse Hugging Face's cache. The local runner uses scikit-image's CPU marching cubes instead of compiling torchmcubes, and converts TripoSR's Z-up/+X-front coordinates to Y-up/+Z-front. It exports neutral geometry without textures and repairs winding with trimesh.

Default extraction resolution is 256. On this M1 Pro, the 128 preview took 2.6–4.5 seconds per part and the 256 passes took 11–23 seconds per part across repeated runs. Model loading took about 6 seconds. Shading took roughly 8–11 seconds per part using `google/gemini-2.5-flash-image`. `--resolution 128` gives a faster preview. Both scripts accept repeatable `--part ID`; the local runner also accepts `--raw` and `--device cpu` for experiments. CPU performance was not tested.

Outputs are in `web/frontend/static/mesh3d/dev-rear-lamp/`:

- `crops/`: polygon-masked, white-backed, square inputs.
- `renders/`: OpenRouter outputs and the transparent masks sent to TripoSR.
- `*-triposr-shaded.glb`: the five meshes used by the viewer.
- `manifest.json`: names, files, explode order/offset, requirement IDs, and source requirements.
- `attempts.jsonl`: model attempts, errors and measured timings. This includes failed experiments, not just successful runs.

The generated asset directory is ignored by Git. A checkout without these local files must run the pipeline before opening `/dev/mesh3d`.

## Hosted alternatives tested

```sh
uv run --with pillow --with requests --with gradio_client \
  scripts/mesh3d/pipeline.py generate --model hunyuan --shade

# Other adapters: --model sf3d or --model trellis2
# --space can override the Space while keeping the chosen adapter's API.
```

Hunyuan3D-2 accepted anonymous requests and returned meshes in about 9–17 seconds end to end on raw crops, or 11–21 seconds including cached/new shading. Raw line art often produced near-cubic artifacts. Shading improved some shapes but did not reliably remove slabs; thresholded alpha and bypassing remote background removal did not solve it. Anonymous GPU quota then ran out. Original TRELLIS and TripoSR Spaces were down; TRELLIS.2 was reachable but quota-blocked. SF3D raised an opaque upstream exception on both raw and shaded lens inputs. No HF token, paid 3D service or local SF3D run was used.

## What is still manual for a new drawing

Pass `--image`, `--regions`, `--requirements` and `--output` to `prepare`, then the same `--output` to both generation steps. Use a fresh output directory so cached shading from another image cannot be reused. The viewer is intentionally fixed to the dev-rear-lamp manifest; replacing that manifest and its local assets reuses the existing route.

The region schema is the supplied `parts3d` format: `caseId`, and a `parts` array containing `id`, `name`, `polygon` in normalized coordinates, `depth`, and either `requirementIds` or `keywords`. Region detection is **not** implemented. Polygons, names and ordering need human review. Explicit requirement IDs are preferable: the provided lamp file contains only keywords, so this spike materializes the previous viewer's keyword matching into IDs. These links include false positives and are not compliance decisions.

The supplied polygons cut through the lamp body and truncate the lens; they do not isolate five complete physical parts. The drawing shows a lamp body and detached lens, not independently drawn housing/board/reflector layers. The shaded lens turns glass reflection streaks into grooves. Single-image inference invents the unseen backs. Independent normalization and stacking do not produce a physically valid assembled lamp.

For Sunday's bumper, cropping, shading, masking, inference and GLB export are automatic **after** reviewed regions exist. Budget human time for complete-part segmentation, matching the named parts to the drawing, reviewing the generated surfaces, relative scales/orientations, assembly positions and requirement links. A few-hour runtime is plausible; acceptable geometry from that unseen drawing is not established.

## Viewer and checks

```sh
# Run these from web/frontend, in separate terminals.
bun run check
bun run dev -- --port 5176 --strictPort
```

Open `/dev/mesh3d`. Orbit, zoom, hover, mesh selection and the part buttons are supported. The slider changes depth offsets; zero is an explicitly inferred assembly layout, not recovered CAD. Selection is mint and displays all keyword-linked requirements with IDs, text, regulation and page.

Review artifacts are in `.amp/in/artifacts/`: the assembled, exploded and selected 1440×900 captures, `per-part-comparison.png`, `mesh-validation.json`, and failed hosted geometry. No production build is needed.
