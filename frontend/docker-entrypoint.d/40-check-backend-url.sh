#!/bin/sh
set -e

# Railway sets RAILWAY_ENVIRONMENT; fail fast if BACKEND_URL was not configured.
if [ -n "${RAILWAY_ENVIRONMENT:-}" ]; then
  if [ -z "${BACKEND_URL:-}" ] || [ "${BACKEND_URL}" = "http://127.0.0.1:8000" ]; then
    echo "ERROR: BACKEND_URL must be set to your FastAPI service URL (e.g. https://your-backend.up.railway.app)"
    exit 1
  fi
fi
