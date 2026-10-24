# Agents

- Layout: the web app is in `web/` (`web/frontend` SvelteKit + Bun, `web/backend` FastAPI + uv). Corpus and cases stay at the repo root.
- Checks: `make check` (read-only), `make fix`.
- Design and copy: follow [DESIGN.md](DESIGN.md), including its list of AI-isms to avoid.
- Everything goes straight to `main`. Pull before pushing; never force push.
