FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/app
WORKDIR /app

# System deps for psycopg2 / pillow.
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Build context is the project root (see docker-compose) so we can vendor the
# sibling ml/ package, which the backend imports for DICOM de-identification.
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ /app/
COPY ml/ /app/ml/

EXPOSE 8000
# Apply migrations, seed demo data, then serve.
CMD ["sh", "-c", "alembic upgrade head && python -m app.demo && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
