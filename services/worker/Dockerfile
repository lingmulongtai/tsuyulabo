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
    uv sync --frozen --no-dev --package tsuyu-worker --no-install-workspace
COPY services/ services/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package tsuyu-worker --no-editable

FROM base AS runtime
RUN groupadd --gid 10001 tsuyu \
    && useradd --uid 10001 --gid tsuyu --create-home tsuyu
COPY --from=builder /app/.venv /app/.venv
USER tsuyu
CMD ["arq", "tsuyu_worker.main.WorkerSettings"]
