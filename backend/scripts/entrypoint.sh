#!/usr/bin/env bash
set -euo pipefail

echo "Running database migrations..."
alembic upgrade head

echo "Seeding database (idempotent)..."
python -m scripts.seed_database

echo "Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
