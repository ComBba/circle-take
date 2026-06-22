# syntax=docker/dockerfile:1
# Circle Take backend — FastAPI on Python 3.12 (official slim base, non-root).
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/backend \
    DATABASE_URL=sqlite:////app/data/circle_take.db \
    APP_ENV=fixture

WORKDIR /app

# System deps: ffmpeg extracts the Take frame the live Continuity Court judges.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install deps first for layer caching (only requirements change busts the cache).
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# App code + golden-path fixtures (main.py resolves examples relative to repo root).
COPY backend ./backend
COPY examples ./examples
COPY frontend ./frontend
# Demo media (take1/take2 clips+frames) is injected at runtime via a volume mount
# (-v host_media:/app/artifacts/live) so the image stays small and git-buildable.

# Non-root user owns the app + writable data dir.
RUN useradd -m appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').status==200 else 1)"

# Cloud Run injects $PORT (default 8080); fall back to 8000 for local/compose.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
