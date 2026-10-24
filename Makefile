.DEFAULT_GOAL := help

UV := uv run --no-sync
BUN := bun
BACKEND := backend
FRONTEND := frontend

# One line per passing step; full output on failure.
define step
@out=$$(mktemp); if ( $(2) ) >$$out 2>&1; then printf 'ok   %s\n' '$(1)'; rm -f $$out; \
else s=$$?; printf 'FAIL %s\n' '$(1)'; cat $$out; rm -f $$out; exit $$s; fi
endef

.PHONY: help check fix dev-backend dev-frontend

help: ## Show this help.
	@awk 'BEGIN{FS=":.*## "} /^[a-zA-Z0-9_-]+:.*## / {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

check: ## Read-only lint, format and type checks for backend and frontend.
	$(call step,ruff,cd $(BACKEND) && $(UV) ruff check)
	$(call step,ruff-format,cd $(BACKEND) && $(UV) ruff format --check)
	$(call step,mypy,cd $(BACKEND) && $(UV) mypy)
	$(call step,biome,cd $(FRONTEND) && $(BUN) run lint)
	$(call step,svelte-check,cd $(FRONTEND) && $(BUN) run check)

fix: ## Apply ruff and biome fixes.
	$(call step,ruff,cd $(BACKEND) && $(UV) ruff check --fix)
	$(call step,ruff-format,cd $(BACKEND) && $(UV) ruff format)
	$(call step,biome,cd $(FRONTEND) && $(BUN) run lint:fix)

dev-backend: ## API on :8000.
	cd $(BACKEND) && uv run uvicorn app.main:app --reload

dev-frontend: ## UI on :5173, proxying /api and /pdfs to :8000.
	cd $(FRONTEND) && $(BUN) run dev
