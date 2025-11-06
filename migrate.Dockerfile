FROM python:3.11-slim

WORKDIR /app

# Install psql
RUN apt-get update \
    && apt-get install -y postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy scripts
COPY scripts/ ./scripts/

# Copy migrations & data
COPY migrations/ ./migrations/
COPY data/ ./data/

# Install Python dependencies if needed
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Run the migration script
ENTRYPOINT ["bash", "/app/scripts/load_sample_data.sh"]
