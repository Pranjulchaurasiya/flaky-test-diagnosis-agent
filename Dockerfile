# ── FlakyGuard Agent + Eval Environment ──────────────────────────────────────
# Multi-stage build: keeps the final image lean (~400MB vs ~1.2GB)
FROM python:3.11-slim AS base

LABEL maintainer="Pranjul"
LABEL description="FlakyGuard: Autonomous Flaky Test Diagnosis Agent"

# System dependencies required for the agent toolchain
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        curl \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer-cached unless requirements change)
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy the full project (excluding .gitignore patterns via .dockerignore)
COPY . .

# Default: run the full benchmark evaluation
CMD ["python", "eval/run_eval.py", "--mode", "full"]
