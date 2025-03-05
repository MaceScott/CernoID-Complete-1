# Use Python 3.10 slim image for better dlib compatibility
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libpq-dev \
    postgresql-client \
    redis-tools \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY models/ ./models/
COPY config/ ./config/
COPY migrations/ ./migrations/
COPY alembic.ini .
COPY docker-entrypoint.sh .

# Create necessary directories
RUN mkdir -p /app/data /app/logs

# Set permissions
RUN chmod +x docker-entrypoint.sh

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["./docker-entrypoint.sh"] 