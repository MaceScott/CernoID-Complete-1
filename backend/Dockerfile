# Backend production stage
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libbz2-dev \
    postgresql-client \
    postgresql-server-dev-all \
    redis-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify redis-cli is available
RUN which redis-cli || (echo "redis-cli not found" && exit 1)

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt psycopg2-binary

# Create models directory
RUN mkdir -p models

# Copy scripts first for model download
COPY scripts/download_models.py scripts/

# Run model download script
RUN python scripts/download_models.py

# Copy migrations directory
COPY migrations migrations/
COPY alembic.ini .

# Copy the rest of the application files
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs

ENV PYTHONPATH=/app
EXPOSE 8000

# Copy and set up entrypoint
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh
CMD ["./docker-entrypoint.sh"] 