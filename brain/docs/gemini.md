# Gemini (free tier) on paragraph relevance

A test on 24 Oct 2026, 22:15 to 22:49 CEST: can a free hosted model replace the paid strong model
in the relevance step (P(cited) per paragraph)? On the paragraphs it reached, Gemini 3.5 Flash
ranked as well as gpt-5.5. The free quota is the catch: about 20 requests per model per day.

## Setup

No code change: `brain/llm.py`'s `local` provider talks to any OpenAI-compatible server, and
Gemini has one.

```bash
# brain/.env holds GEMINI_API_KEY (from https://aistudio.google.com/app/apikey)
BRAIN_LLM=local \
BRAIN_LOCAL_URL=https://generativelanguage.googleapis.com/v1beta/openai/ \
BRAIN_LOCAL_KEY=$GEMINI_API_KEY BRAIN_LOCAL_MODEL=gemini-3.5-flash BRAIN_LOCAL_BATCH=100 ...
```

- The endpoint accepted the pipeline's JSON schema, temperature 0 and `reasoning_effort: none`.
- Use large batches. Local mode sends 8 paragraphs per request by default, which is about 350
  requests for the dev case, far over the free quota. At 100 per request dev needs 29 and the
  likely bumper regulations about 11.
- The test scripts are `out/scripts/cached_relevance_dump.py` (recovers the cached gpt-5.5
  answers and the decision model's out-of-fold scores, with network calls disabled) and
  `out/scripts/gemini_relevance.py`. The log is `out/rear-lamp-gemini-relevance.log`.
- The product profile was the deterministic parse of the spec (`parse_spec`), not an LLM
  profile.

## Results on dev

**Gemini 3.5 Flash**, batches of 100, 13 requests before the quota ran out: 1,100 of the 2,805
candidate paragraphs scored, all of UN R10 and UN R148 and the start of UN R150 (60 gold
paragraphs). UN R48 was not reached.

| Same 1,100 paragraphs | AUC | Best paragraph F2 |
|---|---|---|
| Decision model (out of fold) | 0.853 | 0.529 |
| Gemini 3.5 Flash | **0.974** | **0.746** |
| gpt-5.5 (cached, paid) | 0.968 | 0.741 |
| Gemini 3.5 Flash blended with the decision model (`relevance.blend`, weight 0.7) | 0.980 | 0.786 |

| Regulation | Gold / paragraphs | Gemini 3.5 Flash | gpt-5.5 |
|---|---|---|---|
| UN R10 | 15 / 673 | 0.992 | 0.987 |
| UN R148 | 40 / 374 | 0.951 | 0.944 |
| UN R150 | 5 / 53 | 0.931 | 0.925 |

**Gemini 3.8 Flash**, batches of 25: 425 paragraphs scored, all UN R10 with 13 gold, before its
quota ran out. AUC 0.998 against 0.987 for gpt-5.5 on the same paragraphs.

For reference on the full dev set: gpt-5.5 0.975, Opus 0.972, Jev 0.959, qwen3.5:9b 0.836, the
decision model 0.84 to 0.86 (see `jev.md`, `local-models.md`).

What this does not show yet:
- UN R48, the largest dev regulation (1,166 candidates), is not covered.
- These are paragraph scores. No Gemini run has gone through the full pipeline or been
  uploaded, so its requirement-level effect is unmeasured.
- One test, one profile, one prompt, untuned.

## Limits that decide whether we can use it

- **About 20 requests per model per day per project.** The 429 names the quota:
  `GenerateRequestsPerDayPerProjectPerModel-FreeTier`, value 20. Retries of failed requests
  count. Each model has its own quota, so 3.5 Flash and 3.8 Flash ran out separately.
- **The day resets at midnight Pacific, 09:00 CEST.** Requests made on Saturday evening and on
  Sunday before 09:00 share one day. On 24 Oct, 3.5 Flash and 3.8 Flash were used up; 3.6 and
  3.7 Flash were not touched. Do not spend them before Sunday 08:00.
- **Availability.** One request got HTTP 503 ("This model is currently experiencing high
  demand") and one batch took 15 minutes with retries. `gemini-2.5-flash` returns 404 for new
  users.
- **Models reachable with the key** (24 Oct): `gemini-3.5-flash`, `gemini-3.5-flash-lite`,
  `gemini-3.6-flash`, `gemini-3.7-flash`, `gemini-3.8-flash`, `gemini-3.1-flash-lite`,
  `gemini-3.1-pro-preview`, `gemini-2.5-pro` (5 requests per minute, 50 per day) and others.
- **Data terms.** The relevance prompt carries the product profile, which comes from the
  hackathon spec (`LICENSE-DATA.md`: hackathon use only). In the EEA, free-tier prompts are
  not used to improve Google's products. Keep it that way: do not route spec data through free
  providers that train on prompts or log them.

## Where it fits

1. **Relevance on Sunday, after 09:00.** A bumper relevance pass is about 11 requests at 100
   paragraphs each, inside one model's quota. Before 09:00 only the models not used on
   Saturday are available.
2. **Not the rewrite on the same quota.** The rewrite needs about 20 more requests, and the
   pipeline uses one provider for every step. Gemini for relevance with a paid or local rewrite
   needs a provider per step in `brain/pipeline.py` and `brain/relevance.py` (owned by tasks 06
   and 03 in `todo/`).
3. **Keep a paid key as the fallback.** The quota and the 503s make a free tier a poor single
   point of failure for the one upload that counts.

## Next

- After 09:00 on Sunday: score UN R48 and the rest of UN R150 on 3.5 Flash (about 17 requests)
  to complete the dev comparison.
- Add a per-step provider so relevance can run on Gemini while the rewrite runs elsewhere, then
  run the full pipeline on dev and upload it.
