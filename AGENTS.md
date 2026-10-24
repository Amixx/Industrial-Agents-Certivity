# Agents

- Layout: the web app is in `web/` (`web/frontend` SvelteKit + Bun, `web/backend` FastAPI + uv). The requirement engine is in `brain/` (uv; run its commands from `brain/`, see [brain/README.md](brain/README.md)). Corpus and cases stay at the repo root.
- Paid LLM calls in `brain/` are opt-in through `BRAIN_LLM`. Don't set it, or run LLM experiments, without the owner's approval and a cost estimate.
- Checks: `make check` (read-only), `make fix`, `make test` (brain tests).
- Design and copy: follow [DESIGN.md](DESIGN.md), including its list of AI-isms to avoid.
- Everything goes straight to `main`. Pull before pushing; never force push.
