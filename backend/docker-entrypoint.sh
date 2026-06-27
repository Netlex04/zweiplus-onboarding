#!/bin/sh
# Backend container entrypoint: run DB migrations, then start the app.
# depends_on(db: healthy) in compose guarantees Postgres is ready before this
# runs, so a plain `alembic upgrade head` suffices.
set -e

echo "[entrypoint] Running Alembic migrations (DATABASE_URL=${DATABASE_URL})"
alembic upgrade head

echo "[entrypoint] Starting: $*"
exec "$@"
