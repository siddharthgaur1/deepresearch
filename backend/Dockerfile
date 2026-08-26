# Pinned to bookworm, not floating "slim" (now resolves to trixie, whose apt
# package renames break `playwright install --with-deps`).
FROM python:3.11-slim-bookworm AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpango-1.0-0 libpangocairo-1.0-0 libcairo2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt .
# ponytail: pip cache mount + shell retry loop compensate for a flaky build
# network (seen as ReadTimeoutError mid-download, which pip's own --retries
# doesn't cover since the failed layer's downloads aren't persisted without
# this cache mount). Drop both if the environment's network is reliable.
RUN --mount=type=cache,target=/root/.cache/pip \
    sh -c 'for i in 1 2 3 4 5; do pip install --retries 10 --timeout 120 -r requirements.txt && exit 0; echo "pip install attempt $i failed, retrying..."; sleep 5; done; exit 1'

FROM base AS api
COPY backend/ ./backend/
EXPOSE 8000
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS worker
RUN playwright install --with-deps chromium
COPY backend/ ./backend/
CMD ["celery", "-A", "backend.workers.celery_app", "worker", "--loglevel=info"]
