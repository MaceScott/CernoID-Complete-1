# Use NVIDIA CUDA base image
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ /app/src/
COPY models/ /app/models/
COPY config/ /app/config/

# Create necessary directories
RUN mkdir -p /app/data/logs /app/data/metrics /app/data/features

# Set environment variables
ENV PYTHONPATH=/app
ENV MODEL_PATH=/app/models
ENV DATA_PATH=/app/data
ENV CONFIG_PATH=/app/config

# Run the application
CMD ["uvicorn", "src.core.api.endpoints:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"] 