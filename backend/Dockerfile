# Zweiplus Onboarding backend — FastAPI (Architektur §9).
# Runs Alembic migrations on startup, then serves the API on port 8000.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application (alembic/, app/, seeds/, alembic.ini, …).
COPY . .

# Persisted upload storage (mounted as a volume in compose).
RUN mkdir -p /app/storage

EXPOSE 8000

# Entrypoint runs migrations against the configured DATABASE_URL, then starts
# uvicorn. Seeds load via the FastAPI startup hook (SEED_ON_STARTUP).
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
