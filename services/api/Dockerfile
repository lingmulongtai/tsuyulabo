# syntax=docker/dockerfile:1
FROM python:3.13-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

FROM base AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12.19 /uv /usr/local/bin/uv
ENV UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
COPY pyproject.toml uv.lock ./
COPY services/api/pyproject.toml services/api/pyproject.toml
COPY services/brain/pyproject.toml services/brain/pyproject.toml
COPY services/shiori/pyproject.toml services/shiori/pyproject.toml
COPY services/worker/pyproject.toml services/worker/pyproject.toml
# The workspace routes Linux torch wheels to the CPU-only PyTorch index.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package tsuyulabo-api --no-install-workspace
COPY services/ services/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package tsuyulabo-api --no-editable

FROM base AS runtime
RUN groupadd --gid 10001 tsuyu \
    && useradd --uid 10001 --gid tsuyu --create-home tsuyu
COPY --from=builder /app/.venv /app/.venv
# Keep Alembic configuration and revisions at the agreed repository-relative paths.
COPY --from=builder /app/services/api /app/services/api
USER tsuyu
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)"]
CMD ["uvicorn", "tsuyulabo_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
