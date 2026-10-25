# Agents

- Layout: the web app is in `web/` (`web/frontend` SvelteKit + Bun, `web/backend` FastAPI + uv). The requirement engine is in `brain/` (uv; run its commands from `brain/`, see [brain/README.md](brain/README.md)). Corpus and cases stay at the repo root.
- Paid LLM calls in `brain/` are opt-in through `BRAIN_LLM`. Don't set it, or run LLM experiments, without the owner's approval and a cost estimate.
- Prod (Render) calls the Anthropic API on the owner's key: only Sonnet 5.5 (`claude-sonnet-5-5`) or Haiku 5.5 (`claude-haiku-5-5`) there, never Opus or Fable.
- Checks: `make check` (read-only), `make fix`, `make test` (brain tests).
- Benchmarks: record every benchmark or test run of the brain in `out/`, on any branch, before you report it. Save the submission as `out/<case>-<variant>.json` and its log as `.log`. Add a row to the run log in [out/README.md](out/README.md) with the date and time (CEST), branch and commit, method (models, flags, prompt changes), requirement count, local scores and spend. Write up what changed and why in a dated section below it. When a file is uploaded to the submission platform, add the platform's scores and upload time to the same row and section. Commit the results with the code that produced them.
- Design and copy: follow [DESIGN.md](DESIGN.md), including its list of AI-isms to avoid.
- Everything goes straight to `main`. Pull before pushing; never force push.
