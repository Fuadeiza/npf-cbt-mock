# One image that runs the whole app: FastAPI serves both the API and the
# static frontend from a single process on port 8000.
FROM python:3.12-slim

# Don't buffer stdout/stderr (so logs show up immediately) and don't write .pyc.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies first so this layer is cached unless requirements change.
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy the application code. The backend expects the frontend to sit alongside
# it (../../frontend relative to backend/app/main.py), so keep this layout.
COPY backend/ backend/
COPY frontend/ frontend/

WORKDIR /app/backend

EXPOSE 8000

# IMPORTANT: a single worker only. Attempts are stored in memory, so multiple
# workers/replicas would each have their own store and break mid-exam.
# Listen on $PORT if the platform provides one (Render sets it); default to 8000.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
