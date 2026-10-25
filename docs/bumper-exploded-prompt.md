# Prompt: front bumper exploded view, scroll and 3D

Paste everything below the line into a new Claude Code session at the repo root.

---

Build the exploded view for the front bumper (`cases/heldout-front-bumper`). Build both modes the rear lamp already has: first the scroll-driven 2D view, then the interactive 3D view. A user opening a bumper assessment should get the same experience as on the rear lamp:
- the product explodes into its parts;
- hovering a part shows how many regulations, requirements and paragraphs apply to it;
- clicking a part opens its path in the process graph.

Read `CLAUDE.md`, `DESIGN.md` and the files listed below before you start. Follow DESIGN.md exactly, including its list of AI-isms to avoid.

## What exists for the rear lamp

- **`web/frontend/src/lib/exploded/rearLamp.ts`.** The assembly data: `ExplodedAssembly` with `parts[]`, each part with `id`, `name`, `material`, `check` (the one test it has to pass), `facets` (the product-profile labels the graph highlights, worded as the spec words them) and its box in frame pixels.
- **`ExplodedView.svelte`, the scroll mode.** Its layers were cut from one generated render, in `web/frontend/static/exploded/rear-lamp/*.webp`, so every part shares the same camera and light. Scrolling separates the assembled stack into its parts, labels each one with its check, and ends on a parts table.
- **`lamp3d.ts` and `Lamp3D.svelte`, the 3D mode.** A parametric three.js model built from one face outline, so the parts fit together. The scene exposes `setExplode`, `setSelected`, `focus` (isolate a part and fly the camera in), `setLit`, `setInset`, `screenPoint`, `resetView` and `dispose`, plus CSS2D labels and `PartHoverCard.svelte`.
- **Graph link.** `lib/graph/model.ts` (`partFacets`, `partCoverage`) links a part to the graph through its facets. The graph route reads `?part=<id>`.
- **`rearLamp` is hard-coded in six places:**
  - the landing page;
  - `/a/[id]` (part filter);
  - `/a/[id]/exploded`;
  - `/a/[id]/graph`;
  - `lib/exploded/*`;
  - `lib/ui/theme.css`.
  
  A bumper assessment currently shows lamp parts.

## What the bumper is

- **Spec.** `cases/heldout-front-bumper/spec.md`, an M1 front bumper. Use its "Main Parts" and "Materials" wording.
- **Exploded view.** Look at `cases/heldout-front-bumper/exploded_view.png`. It's an OEM exploded drawing with red callouts for the cover part (fascia), grill, absorber, lower stiffener, licence plate holder, towing device cover, camera, radar sensor, radar/LIDAR with heating, PDC sensor, pedestrian impact sensors, temperature sensor, decorative lighting, side signalling lighting, keyless-entry aerial and the EV charge flap.
- **Regulations.** Which regulations the bumper cites, and why, is in the stored bumper assessment and in the run log, `out/README.md`, under the bumper rows. Look for UN R127 pedestrian protection, R42 front and rear protective devices, R26 external projections, R10 EMC and R48 lighting installation, and check them against the stored assessment.

## Parts

Use 10 to 12 parts, so the labels stay readable and the scroll view fits one row. Group the spec's 16 callouts. Suggested grouping, front to back:

1. Grill
2. Licence plate holder
3. Decorative lighting
4. Side signalling lighting
5. Cover part (fascia), with the towing device cover and the charge flap as details on it
6. Front camera
7. Radar and LIDAR sensors (with heating)
8. PDC sensors
9. Pedestrian impact sensors
10. Absorber (EPP)
11. Lower stiffener
12. Brackets and fasteners

Keep the temperature sensor and the aerial as small details on the nearest part rather than separate layers, unless the regulations cite them.

For each part, fill in `material` from the spec's table and `check` with the one plain-language check from the assessment's own requirements, for example "Fascia passes the pedestrian legform test" or "No external projection with a radius under 2.5 mm". `facets` must be the exact strings the bumper assessment's product profile uses (`profile.parts`, `functions`, `materials`), or the graph link highlights nothing. Read them from the stored assessment rather than guessing.

If no bumper assessment is stored yet, check `/history`. The regulation-change session may be creating one from an existing held-out output in `out/`. Don't run the paid pipeline; that needs the owner's approval and a cost estimate.

## Make the view work for both products

Before adding the bumper:
- Add an assembly registry: `lib/exploded/assemblies.ts` with `rearLamp`, `frontBumper` and `assemblyFor(assessment)`, which picks the assembly by case name or product type and returns `null` when neither fits.
- Replace each hard-coded `rearLamp`, except the landing page, which stays the lamp.
- An assessment with no assembly hides the "Exploded view" tab rather than showing the wrong product.
- Split `lamp3d.ts` into a shared scene, with the renderer, controls, environment, labels, focus, hover and explode tween, and a per-product builder. Keep the rear lamp looking and behaving exactly as it does now; check it against the landing page and `/a/<id>/exploded` before and after.

## 1. Scroll view first

The lamp's layers come from one generated render. Do the same for the bumper, so the part images match the lamp's look: a clean studio product render, neutral light gray, one camera and one light for every part. Pick the first route that works:

- **A. Generated render.** One image of the bumper exploded along the vehicle's long axis, front parts on the left, parts in a single row, consistent scale, with nothing overlapping. Then cut it into one transparent webp per part. Image generation through a paid service needs the owner's OK first, with the number of images and the cost.
- **B. Rendered from the 3D model.** If A doesn't give clean, separable parts, build the 3D model first (step 2). Then render each part to a transparent PNG from one fixed camera, with three.js offscreen or headless Chrome, and convert to webp. The parts are guaranteed to line up, at the cost of a less photographic look.

Either way, the files go in `web/frontend/static/exploded/front-bumper/`, the boxes and `cx` in `frontBumper.ts`, and the existing `ExplodedView.svelte` plays them unchanged, apart from any layout the wider part count needs. The bumper is wider than it is deep, so check that the label columns still fit at 1440 px and at phone width.

## 2. Then the 3D view

A parametric three.js bumper in the style of `lamp3d.ts`: simple, clean geometry that reads as a bumper at a glance, not a CAD model.
- **Fascia.** An extruded, slightly curved front profile, wrapped at the corners.
- **Grill.** A slatted insert.
- **Absorber.** A foam block behind the fascia.
- **Lower stiffener.** A beam.
- **Sensors.** Small boxes and cylinders at their real positions: the radar at the centre, PDC sensors along the fascia, the camera at the grill.
- **Lights.** Light bars at the corners.

Explode along the vehicle's long axis, front parts forward and structure back, with sensors also sliding out from their mounting points so they don't hide behind the fascia. The lamp's "Lamp on" toggle becomes "Lights on" for the signalling and decorative lighting. Hover, the hover card, click-to-graph, `focus` and the idle part tour all work as on the lamp.

## Copy

Sentence case, plain words, no exclamation marks, no em dashes or middle dots as separators, no "AI" badges. Part names follow the spec's wording.

## Done when

- A bumper assessment shows its own exploded view in both modes (`/a/<id>/exploded` and `?view=scroll`). The rear lamp's views are unchanged.
- Hovering each bumper part shows non-zero coverage wherever the assessment's requirements mention it. Clicking opens `/a/<id>/graph?part=<id>` with that part's path lit. A part with no requirements says so plainly.
- `/a/<id>?part=<id>` filters the requirement list for bumper parts as it does for lamp parts.
- `make check` passes. You checked both products in the browser preview, dark and light, at 1920×1080 and at phone width, and attached screenshots of the bumper in both modes, assembled and exploded.
- The work is committed straight to `main` (pull before pushing, never force push), with the static assets alongside.

Two other sessions may be editing the web app at the same time: the regulation-change UI and the coverage page. The regulation-change one may add markers to the exploded view. Keep your changes in `lib/exploded/` and the routes that pick the assembly, and rebase on `origin/main` before you push.
