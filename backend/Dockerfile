# ============================================================
# LungSight AI — Backend Dockerfile (multi-stage)
# ============================================================

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Builder stage ─────────────────────────────────────────────────────────────
FROM base AS builder
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# ── Final stage ───────────────────────────────────────────────────────────────
FROM base AS final
COPY --from=builder /install /usr/local

# Create non-root user
RUN useradd --uid 1000 --no-create-home --shell /bin/bash lungsight
RUN mkdir -p /app/uploads /app/reports/generated /app/backend/models/weights \
    && chown -R lungsight:lungsight /app

COPY --chown=lungsight:lungsight . .

USER lungsight

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
