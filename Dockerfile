# Use the latest Node.js LTS version for the frontend build
FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --legacy-peer-deps
COPY . .
RUN npm run build

# Use the latest Python slim version for the backend build
FROM python:3.11-slim-buster as backend-builder
WORKDIR /app
COPY requirements*.txt ./
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-distutils \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

# Install system dependencies for dlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake \
    g++ \
    make \
    build-essential \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    python3-distutils \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip to the latest version to avoid outdated package issues
RUN pip install --upgrade pip

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    mpg123 \
    alsa-utils \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Copy built Next.js assets
COPY --from=frontend-builder /app/.next ./.next
COPY --from=frontend-builder /app/public ./public
COPY --from=frontend-builder /app/package*.json ./

# Copy Python dependencies and code
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY src ./src
COPY scripts ./scripts

# Create non-root user
RUN useradd -m cernoid && \
    chown -R cernoid:cernoid /app
USER cernoid

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/health || exit 1

# Environment variables
ENV NODE_ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8000

# Start script
CMD ["./scripts/start.sh"] 