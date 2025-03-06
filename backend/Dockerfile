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
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    python-multipart==0.0.6 \
    numpy==1.26.2 \
    opencv-python==4.9.0.80 \
    dlib==19.24.2 \
    torch==2.1.1 \
    torchvision==0.16.1 \
    redis==5.0.1 \
    pydantic==2.5.2 \
    pydantic-settings==2.1.0 \
    python-jose==3.3.0 \
    passlib==1.7.4 \
    bcrypt==4.0.1 \
    python-dotenv==1.0.0 \
    alembic==1.12.1 \
    psycopg2-binary==2.9.9 \
    sqlalchemy==2.0.23 \
    asyncpg==0.29.0 \
    aioredis==2.0.1

# Create models directory
RUN mkdir -p models

# Copy scripts first for model download
COPY scripts/download_models.py scripts/

# Run model download script
RUN python scripts/download_models.py

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