# Build stage
FROM python:3.10-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
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

# Install Poetry
RUN pip install --no-cache-dir poetry==1.6.1

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --only main

# Install ML dependencies with optimizations
RUN pip install --no-cache-dir --no-deps \
    dlib==19.24.0 \
    opencv-python-headless==4.8.1.78 \
    numpy==1.24.3 \
    scipy==1.11.4 \
    torch==2.2.1 \
    torchvision==0.17.1 \
    face-recognition==1.3.0

# Final stage
FROM python:3.10-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
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
RUN useradd -m -u 1000 appuser && \
    mkdir -p /home/appuser/.cache && \
    chown -R appuser:appuser /home/appuser

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create necessary directories and set permissions
RUN mkdir -p /app/src /app/data /app/logs /etc/cernoid/secrets /var/log/cernoid /var/lib/cernoid/models && \
    chown -R appuser:appuser /app /etc/cernoid /var/log/cernoid /var/lib/cernoid && \
    chmod -R 755 /app/data /app/logs /var/log/cernoid /var/lib/cernoid && \
    chmod -R 700 /etc/cernoid/secrets

# Copy application code
COPY src/ /app/src/
COPY migrations/ /app/migrations/
COPY alembic.ini /app/
COPY entrypoint.sh /app/
COPY healthcheck.sh /app/

# Set ownership and permissions
RUN chown -R appuser:appuser /app && \
    chmod +x /app/entrypoint.sh /app/healthcheck.sh && \
    chmod -R 755 /app/src /app/migrations

# Set environment variables
ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    ALEMBIC_CONFIG=/app/alembic.ini \
    HOME=/home/appuser \
    FACE_RECOGNITION_MODEL_PATH=/var/lib/cernoid/models \
    LOG_PATH=/var/log/cernoid \
    SECRETS_PATH=/etc/cernoid/secrets \
    PORT=8000

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD /app/healthcheck.sh

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"] 