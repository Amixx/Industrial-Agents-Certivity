FROM oven/bun:1 AS frontend
WORKDIR /app/web/frontend
COPY web/frontend/package.json web/frontend/bun.lock ./
RUN bun install --frozen-lockfile
COPY web/frontend/ ./
RUN bun run build

FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY web/backend/pyproject.toml web/backend/uv.lock web/backend/.python-version web/backend/
RUN cd web/backend && uv sync --frozen --no-dev --no-install-project
COPY web/backend/ web/backend/
COPY --from=frontend /app/web/frontend/build web/frontend/build
COPY regulations/ regulations/
COPY cases/ cases/
COPY schemas/ schemas/
COPY data/regulation-updates/ data/regulation-updates/
WORKDIR /app/web/backend
ENV PATH="/app/web/backend/.venv/bin:$PATH"
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
