FROM oven/bun:1 AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/bun.lock ./
RUN bun install --frozen-lockfile
COPY frontend/ ./
RUN bun run build

FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock backend/.python-version backend/
RUN cd backend && uv sync --frozen --no-dev --no-install-project
COPY backend/ backend/
COPY --from=frontend /app/frontend/build frontend/build
COPY regulations/ regulations/
COPY cases/ cases/
COPY schemas/ schemas/
WORKDIR /app/backend
ENV PATH="/app/backend/.venv/bin:$PATH"
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
