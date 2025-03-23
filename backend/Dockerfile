# Build stage
FROM python:3.10-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    pkg-config \
    libx11-6 \
    libatlas-base-dev \
    libgtk-3-0 \
    libboost-python1.74.0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies with increased timeout and retries
RUN pip install --no-cache-dir --timeout 1000 --retries 3 \
    fastapi==0.109.2 \
    uvicorn[standard]==0.27.1 \
    python-multipart==0.0.9 \
    aiohttp==3.9.3 \
    aiofiles==23.2.1 \
    sqlalchemy==2.0.27 \
    alembic==1.13.1 \
    psycopg2-binary==2.9.9 \
    asyncpg==0.29.0 \
    aiomysql==0.2.0 \
    python-jose[cryptography]==3.3.0 \
    passlib[bcrypt]==1.7.4 \
    PyJWT==2.8.0 \
    email-validator==2.1.0.post1 \
    cryptography==42.0.2 \
    python-dotenv==1.0.1 \
    pydantic==2.6.1 \
    pydantic-settings==2.1.0 \
    PyYAML==6.0.1 \
    redis==5.0.1 \
    aioredis==2.0.1 \
    cachetools==5.3.2 \
    tenacity==8.2.3 \
    psutil==5.9.8 \
    prometheus-client==0.19.0 \
    statsd==4.0.1 \
    gTTS==2.5.1 \
    pytest==8.0.0 \
    pytest-asyncio==0.23.5 \
    pytest-cov==4.1.0 \
    httpx==0.26.0 \
    black==24.1.1 \
    isort==5.13.2 \
    flake8==7.0.0 \
    mypy==1.8.0

# Install ML dependencies separately
RUN pip install --no-cache-dir --timeout 1000 --retries 3 \
    dlib==19.24.0 \
    opencv-python-headless==4.8.1.78 \
    numpy==1.24.3 \
    scipy==1.11.4

# Install PyTorch dependencies separately
RUN pip install --no-cache-dir --timeout 1000 --retries 3 \
    torch==2.1.1 \
    torchvision==0.16.1 \
    face-recognition==1.3.0

# Runtime stage
FROM python:3.10-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libx11-6 \
    libatlas-base-dev \
    libgtk-3-0 \
    libboost-python1.74.0 \
    curl \
    postgresql-client \
    redis-tools \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy application files from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create necessary directories and set permissions
RUN mkdir -p /app/src /app/models /app/data /app/logs && \
    chown -R appuser:appuser /app

# Copy application code
COPY src/ /app/src/
COPY models/ /app/models/
COPY alembic.ini /app/
COPY healthcheck.sh /app/
COPY entrypoint.sh /app/

# Set ownership
RUN chown -R appuser:appuser /app

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV ALEMBIC_CONFIG=/app/alembic.ini

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD nc -z localhost 3000 || exit 1

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"] 