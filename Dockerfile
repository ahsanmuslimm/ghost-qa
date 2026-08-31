# syntax=docker/dockerfile:1

# ---------- Stage 1: build dependencies ----------
FROM python:3.11-slim AS builder

WORKDIR /app

# Build deps for compiled wheels (psycopg2, cryptography)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ---------- Stage 2: production runtime ----------
FROM python:3.11-slim AS runtime

WORKDIR /app

# curl is used by the container HEALTHCHECK
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Installed Python packages from the builder stage
COPY --from=builder /root/.local /home/ghost/.local

# Application code only — no tests, docs or local databases
COPY app ./app
COPY alembic ./alembic
COPY templates ./templates
COPY alembic.ini run.py docker-entrypoint.sh ./

# Non-root runtime user
RUN useradd -m -u 1001 ghost \
    && chmod +x docker-entrypoint.sh \
    && chown -R ghost:ghost /app /home/ghost
USER ghost

ENV PATH=/home/ghost/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -fsS http://localhost:8000/ || exit 1

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["serve"]
