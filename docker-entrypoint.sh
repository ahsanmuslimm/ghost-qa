#!/bin/sh
# Ghost QA container entrypoint.
#   serve   - run schema migrations then start the API (default)
#   migrate - run schema migrations only (init container / K8s job)
# Anything else is executed as-is.
set -e

case "${1:-serve}" in
  serve)
    echo "Running database migrations..."
    alembic upgrade head
    echo "Starting Ghost QA (workers=${UVICORN_WORKERS:-2})..."
    exec uvicorn app.main:app \
      --host 0.0.0.0 \
      --port "${APP_PORT:-8000}" \
      --workers "${UVICORN_WORKERS:-2}" \
      --proxy-headers \
      --forwarded-allow-ips "*"
    ;;
  migrate)
    exec alembic upgrade head
    ;;
  *)
    exec "$@"
    ;;
esac
