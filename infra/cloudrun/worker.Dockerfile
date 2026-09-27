# syntax=docker/dockerfile:1
# Build services/worker/Dockerfile first. This adds only the Cloud Run HTTP adapter.
ARG WORKER_BASE=tsuyulabo-worker-base:local
FROM ${WORKER_BASE}
COPY --chown=tsuyu:tsuyu infra/cloudrun/worker_service.py /app/worker_service.py
EXPOSE 8080
CMD ["python", "/app/worker_service.py"]
