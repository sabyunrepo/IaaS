# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

WORKDIR /app

# System dependencies (PyDriller: git, PDF: poppler)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies (BuildKit cache mount로 재빌드 가속)
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt && \
    pip install semgrep>=1.50.0

# Source code
COPY . .

# Development target
FROM base AS development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production target
FROM base AS production
RUN --mount=type=cache,target=/root/.cache/pip pip install gunicorn
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
