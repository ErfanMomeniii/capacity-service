FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# system deps for some libs (if needed)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev gcc netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy requirement files first to leverage docker cache
COPY pyproject.toml requirements.txt /app/

RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Create a non-root user for security in production images
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# Default to Uvicorn for development; in production swap with Gunicorn via environment or entrypoint
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
