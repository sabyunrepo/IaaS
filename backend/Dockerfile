FROM python:3.11-slim AS base

WORKDIR /app

# System dependencies (Docling: tesseract, poppler / PyDriller: git)
RUN apt-get update && apt-get install -y \
    git \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Semgrep CLI (installed separately — large package, ~100MB)
RUN pip install --no-cache-dir semgrep>=1.50.0

# Source code
COPY . .

# Development target
FROM base AS development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production target
FROM base AS production
RUN pip install gunicorn
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
