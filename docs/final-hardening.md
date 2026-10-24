# Final hardening

What to fix, build and cut between now and the pitch on Sunday 15:00, and why. Checked against the [challenge brief](certivity-challenge-brief.pdf), the [meeting with the organisers](meeting%20with%20organizers/summary.txt) and [brain/docs/PLAN.md](../brain/docs/PLAN.md).

## Fix first

- The held-out case is a front bumper. The exploded view and the 3D model are cut by hand for the rear lamp (`web/frontend/src/lib/exploded/rearLamp.ts`, `lamp3d.ts`), and `web/backend/app/pipeline.py` still serves `fake_data`.
- The brief requires a demo that runs from input to requirements without manual steps (R3).
- So: wire `brain.pipeline.run()` into the backend, and run the synthetic bumper cases in `brain/data/synthetic/bumper-*` through the app today.
- Parts come from the spec. The drawing is navigation onto those parts. The organisers said the description is what the product is, and that a mesh can be rotated until it lies. Do not spend the night on a vision model that lists parts from the image.

## What scores

| Criterion | Weight |
|---|---|
| Score on the held-out case (F2, recall as tie-break) | 40% |
| Demo and user interface | 20% |
| Sub-goal result | 15% |
| Potential impact ("would Certivity continue, test or deploy it") | 15% |
| Pitch | 10% |

The organisers' tie-break for equal scores and UI: a solution that runs on the user's computer without heavy AI. Missing a requirement costs more than an extra one. A fixed list of regulations fails on a bumper. The citation (page and paragraph) matters more than the wording.

## Build, in order

1. **Eval panel.** F2 per level on dev, cost per run, runtime, local mode against LLM mode. The brief's strong submission "shows in the pitch where it is weak and how that was measured". Say both numbers.
2. **Excluded regulations, as the opening.** One line per dropped regulation, from the rule that fired. R7 no longer grants a new approval. R94 is the whole vehicle. No lamp, so R148 stays out. The organisers asked why this one and why not the others, including vehicle category. The brief calls citing regulations "to be safe" a weak submission. The `regulations` field already holds the rationale.
3. **One live link.** Click a requirement whose paragraph points at an annex. The graph walks the reference and the PDF lands on the test procedure. That is the organisers' point that regulations link to each other, and the optional test case comes with it. One rehearsed click.
4. **Quote check.** Verify each requirement's `quote` against the PDF text and show the count, for example "190 of 190 requirements traced to source text". The UI criterion asks that every requirement links to its source page.
5. **Change monitor.** Friday the product complied. The next supplement moves some obligations, removes one, adds others, each with the sentence that changed. It reuses the sub-goal diff. It matches the brief (find which requirements change, update the spec) and the organisers' idea of a tool that runs on the engineer's computer every morning.

## Cut

- Spec compliance check (spec values against requirement limits). Not asked for, hard on a bumper, risky live. Mention it as a next step.
- E-mark render. Lamp-specific.
- Live what-if editing, unless the deterministic run takes seconds.
- ReqIF export. The impact points they already handed us are the local run and the morning diff.
- Active-voice rewrites. The golden file keeps the regulation's passive voice. Citation, paragraph and base version are what they said to protect.
- A third product live, unless it has already been dry-run. An L-category lamp that drops R48 is the "no static list" proof. A wrong regulation on stage costs more than skipping it.

## Pitch

- Open on the regulations you refused, one sentence each.
- Turn the wifi off and run the bumper case in deterministic local mode. Upload whichever file scores higher, and say both numbers. Uploads close at 13:00 and the pitch starts at 15:00, so the rerun cannot affect the score.
- Follow one requirement into its annex and land on the test.
- Show the eval panel: where we are weak and what each mode costs.
- Say their windshield line back, on the bumper: the output is the impact and projection obligation, not "the skin shall be plastic."
- Close on the change monitor.

## Summary

The pipeline and the UI already cover most of the score. What sets us apart is the bumper running live, the regulations we refused and why, one citation followed into its test, a laptop run with the model off, and the morning diff when a supplement lands.
