FROM python:3.11-slim

# System Dependencies (Git: PyDriller/Cloning, gcc: native extensions)
RUN apt-get update && apt-get install -y \
    git \
    curl \
    gcc \
    g++ \
    procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python Dependencies (캐싱 레이어)
COPY pyproject.toml .
RUN pip install --no-cache-dir . && pip install --no-cache-dir .[dev]

# Copy Application Code
COPY . .

# Environment
ENV PYTHONPATH=/app/src

# Run
CMD ["uvicorn", "interface.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
