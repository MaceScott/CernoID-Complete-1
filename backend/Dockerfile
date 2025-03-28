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
RUN pip install --no-cache-dir --timeout 1000 --retries 3 -r requirements.txt

# Install ML dependencies separately with optimizations
RUN pip install --no-cache-dir --timeout 1000 --retries 3 \
    dlib==19.24.0 \
    opencv-python-headless==4.8.1.78 \
    numpy==1.24.3 \
    scipy==1.11.4

# Install PyTorch with CUDA support if available
ARG CUDA_VERSION=11.8
ARG TORCH_VERSION=2.1.2
RUN pip install --no-cache-dir --timeout 1000 --retries 3 \
    torch==${TORCH_VERSION}+cu${CUDA_VERSION} \
    torchvision==0.16.1+cu${CUDA_VERSION} \
    --extra-index-url https://download.pytorch.org/whl/cu${CUDA_VERSION}

# Install face recognition
RUN pip install --no-cache-dir --timeout 1000 --retries 3 \
    face-recognition==1.3.0

# Download shape predictor model
COPY download_models.py .
RUN python download_models.py

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
RUN useradd -m -u 1000 appuser && \
    mkdir -p /home/appuser/.cache && \
    chown -R appuser:appuser /home/appuser

# Set working directory
WORKDIR /app

# Copy application files from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app/models /app/models

# Create necessary directories and set permissions
RUN mkdir -p /app/src /app/data /app/logs && \
    chown -R appuser:appuser /app

# Copy application code
COPY src/ /app/src/
COPY migrations/ /app/migrations/
COPY alembic.ini /app/
COPY healthcheck.sh /app/
COPY entrypoint.sh /app/

# Set ownership and permissions
RUN chown -R appuser:appuser /app && \
    chmod +x /app/healthcheck.sh /app/entrypoint.sh && \
    chmod -R 755 /app/data /app/logs

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV ALEMBIC_CONFIG=/app/alembic.ini
ENV HOME=/home/appuser
ENV CUDA_VISIBLE_DEVICES=all
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}

# Switch to non-root user
USER appuser

# Health check with increased timeout
HEALTHCHECK --interval=60s --timeout=60s --start-period=30s --retries=3 \
    CMD nc -z localhost 8000 || exit 1

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"] 