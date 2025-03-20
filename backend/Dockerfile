# Backend production stage
FROM python:3.11-slim

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
    pkg-config \
    libx11-dev \
    libatlas-base-dev \
    libgtk-3-dev \
    libboost-python-dev \
    python3-dev \
    git \
    curl \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Build and install dlib from source
RUN git clone https://github.com/davisking/dlib.git && \
    cd dlib && \
    python setup.py install && \
    cd .. && \
    rm -rf dlib

# Verify redis-cli and curl are available
RUN which redis-cli || (echo "redis-cli not found" && exit 1)
RUN which curl || (echo "curl not found" && exit 1)

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    python-multipart==0.0.6 \
    numpy==1.26.2 \
    opencv-python==4.9.0.80 \
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
    aioredis==2.0.1 \
    PyYAML==6.0.1 \
    GPUtil==1.4.0 \
    cachetools==5.3.2 \
    psutil==5.9.8 \
    gTTS==2.5.1 \
    email-validator==2.1.0.post1 \
    cryptography==42.0.2 \
    PyJWT==2.8.0

# Create models directory
RUN mkdir -p models

# Create OpenCV haarcascades directory
RUN mkdir -p /usr/local/share/opencv4/haarcascades

# Copy scripts first for model download
COPY scripts/download_models.py scripts/

# Run model download script
RUN python scripts/download_models.py

# Copy migrations directory
COPY migrations migrations/
COPY alembic.ini .

# Copy the rest of the application files
COPY . .

# Copy cascade file to OpenCV directory
RUN cp models/haarcascade_frontalface_default.xml /usr/local/share/opencv4/haarcascades/

# Create necessary directories with proper permissions
RUN mkdir -p /app/data /app/logs && \
    chmod -R 755 /app/data /app/logs

ENV PYTHONPATH=/app/src

# Set default environment
ENV ENVIRONMENT=production

EXPOSE 8000

# Copy and set up entrypoint
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

# Add health check script
COPY <<'EOF' /app/health_check.sh
#!/bin/bash
curl -f http://localhost:8000/health || exit 1
EOF
RUN chmod +x /app/health_check.sh

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD /app/health_check.sh

CMD ["./docker-entrypoint.sh"] 