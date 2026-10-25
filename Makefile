.DEFAULT_GOAL := help

UV := uv run --no-sync
BUN := bun
BACKEND := web/backend
BRAIN := brain
FRONTEND := web/frontend

# One line per passing step; full output on failure.
define step
@out=$$(mktemp); if ( $(2) ) >$$out 2>&1; then printf 'ok   %s\n' '$(1)'; rm -f $$out; \
else s=$$?; printf 'FAIL %s\n' '$(1)'; cat $$out; rm -f $$out; exit $$s; fi
endef

.PHONY: help check fix test dev-backend dev-frontend

help: ## Show this help.
	@awk 'BEGIN{FS=":.*## "} /^[a-zA-Z0-9_-]+:.*## / {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

check: ## Read-only lint, format and type checks for backend, brain and frontend.
	$(call step,ruff,cd $(BACKEND) && $(UV) ruff check)
	$(call step,ruff-format,cd $(BACKEND) && $(UV) ruff format --check)
	$(call step,mypy,cd $(BACKEND) && $(UV) mypy)
	$(call step,brain ruff,cd $(BRAIN) && $(UV) ruff check)
	$(call step,brain ruff-format,cd $(BRAIN) && $(UV) ruff format --check)
	$(call step,brain mypy,cd $(BRAIN) && $(UV) mypy)
	$(call step,biome,cd $(FRONTEND) && $(BUN) run lint)
	$(call step,svelte-check,cd $(FRONTEND) && $(BUN) run check)

fix: ## Apply ruff and biome fixes.
	$(call step,ruff,cd $(BACKEND) && $(UV) ruff check --fix)
	$(call step,ruff-format,cd $(BACKEND) && $(UV) ruff format)
	$(call step,brain ruff,cd $(BRAIN) && $(UV) ruff check --fix)
	$(call step,brain ruff-format,cd $(BRAIN) && $(UV) ruff format)
	$(call step,biome,cd $(FRONTEND) && $(BUN) run lint:fix)

test: ## Brain tests (some need the corpus from brain.ingest), then backend tests (need brain/.venv).
	$(call step,brain pytest,cd $(BRAIN) && $(UV) pytest -q)
	$(call step,backend pytest,cd $(BACKEND) && $(UV) pytest -q)

dev-backend: ## API on :8000.
	cd $(BACKEND) && uv run uvicorn app.main:app --reload

dev-frontend: ## UI on :5173, proxying /api and /pdfs to :8000.
	cd $(FRONTEND) && $(BUN) run dev
