# 03 Fewer paragraphs outside the gold

## Prompt

You are joining a hackathon team mid-event (Certivity challenge, Munich). Read
`brain/docs/todo/README.md` first: it has the event, the scores, the rules and the tools. Work
from `brain/`.

**Why this task exists.** 155 of the 332 rows in our best dev run (Fable 5.1, platform F2 0.682)
come from paragraphs the gold does not cite, and none of them can match. Dropping all of them
would lift the local judge from 0.646 to 0.752. The relevance step decides which paragraphs go
to the rewrite: today a geometric blend of the decision model (`brain/decide.py`, logistic
regression on `brain/features.py`) and an LLM's P(cited) per paragraph (`brain/relevance.py`,
weight 0.7 on the LLM, cut-off 0.20, a floor of each regulation's top 6%).

**What is already measured** (do not redo it):
- Paragraph AUC on dev: decision model 0.84 to 0.86 out of fold, qwen3.5:9b 0.836, Jev 0.959,
  gpt-5.5 0.975, Opus 0.972, blend of gpt-5.5 and the decision model 0.981
  (`docs/jev.md`, `docs/local-models.md`).
- Jev (`jev-1.14.0`, five yes/no "Nouls" per paragraph: technical requirement, own function,
  other function, installation, EMC) costs about $0.14 and 11 s per dev case. Its top 30% holds
  98 to 100% of the gold paragraphs. Its best F2 alone is 0.07 to 0.12 below Opus.
- Section routing has a low ceiling: an oracle choice of sections lifts paragraph F2 only from
  0.76 to 0.83, because the gold is selective inside the right sections (R48 6.10.5.1 is gold,
  6.4.5.1, the same clause for the reversing lamp, is not). Rule-based gates on top of the LLM
  score lowered F2 on all four uploaded runs.
- Re-filtering rows by the blended score peaks at F2 0.61 on the gpt run: the cut-off is not
  the lever, the ranking is.
- On the silver bumper labels the decision model scores AUC 0.808 after the 24 Oct feature
  fixes (sibling routing, regulation title naming the product), 0.724 before. The weight 0.85
  on the LLM helped the bumper but cost the lamp (estimated dev requirement F2 0.61 to 0.54),
  so it went back to 0.7.

**The Jev API.** `POST https://api.typesafe.ai/v1/systemone`, header
`Authorization: Bearer <key>`, body `{"model": "jev-1.14.0", "state": {...}, "questions":
{"<id>": {"type": "noul", "instructions": "...", "criteria": {"true": "...", "false":
"..."}}}}`. The answer is `{"answers": {"<id>": {"type": "noul", "noul": 0.98}}, "usage":
{...}}`; validation errors are HTTP 422 with a `detail` list. Keep a request under 64k tokens
(25 paragraphs with five Nouls is about 31k). The questions used in the spike are at the end of
`docs/jev.md`. Ask the team whether the spike's client exists on a branch (a `kb-wired` branch
was mentioned) before writing a new one.

**What to do.**
1. Write `brain/jev.py`: a client that goes through the same disk cache as `brain/llm.py`
   (keyed on model, state and questions), opt-in through an environment variable like
   `BRAIN_LLM`, with the key in `brain/.env`. Offline tests with a fake response.
2. Score every candidate paragraph of dev (2,915) and of the four bumper regulations (814
   labelled) with the five Nouls. About $0.20 in total; get approval first.
3. Build a stack: the decision model's features, the five Noul probabilities, and the LLM
   P(cited) where you have it. The gpt-5.5 answers for dev are in `data/cache/llm/`, but they
   are only found if the prompt and profile are unchanged, and a miss becomes a paid call:
   read them with the provider calls patched to raise, never with a live key. Compare logistic regression and TabPFN
   (`uv sync --extra tabpfn`; ask before installing). Validate leaving one regulation out on
   dev, and fit on dev, test on the bumper labels.
4. Turn the best stack into a selection rule and measure it at the requirement level: apply it
   as a filter to the rows of `../out/rear-lamp-fable.json` and `../out/rear-lamp-opus.json`
   and score with `eval.score` (or the task 01 judge). That shows what it would have saved
   without a new paid run.
5. Measure Jev as a pre-filter for the strong model: keep its top 30 to 40% of paragraphs and
   let the LLM read only those. Report the recall lost and the strong-model cost saved; on the
   bumper that could turn a $6 Fable run into about $2.
6. Wire the winner into `brain/relevance.py` and `brain/pipeline.py` behind its environment
   variable, so the run without Jev stays exactly as it is.

**Acceptance.**
- On dev, out of fold: fewer rows outside gold paragraphs at the same recall of gold
  paragraphs, worth at least +0.02 requirement F2 when applied to the Fable and Opus rows.
- On the bumper labels: AUC and F2 at the chosen cut-off no worse than the current
  `eval.transfer` numbers (AUC 0.808, F2 0.423).
- The pipeline with Jev off gives the same output as before your change (compare the
  deterministic dev output row by row).

**Deliverables.** `brain/jev.py` with tests; the stack and its wiring; all numbers under
"Results"; a short update of `docs/jev.md`.

**Do not.** Tune the cut-off on dev alone; the bumper labels must agree. Touch
`brain/rewrite.py` (task 02).

## Results

(fill in)
