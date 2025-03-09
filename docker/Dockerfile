# Base stage for shared dependencies
FROM node:18-alpine AS base
WORKDIR /app
COPY package*.json ./
RUN npm ci

# Frontend build stage
FROM base AS frontend-build
COPY . .
WORKDIR /app
RUN npm run build

# Frontend production stage
FROM node:18-alpine AS frontend
WORKDIR /app
COPY --from=frontend-build /app/.next ./.next
COPY --from=frontend-build /app/public ./public
COPY --from=frontend-build /app/package*.json ./
COPY --from=frontend-build /app/node_modules ./node_modules
COPY --from=frontend-build /app/next.config.js ./
ENV NODE_ENV=production
EXPOSE 3000
CMD ["npm", "start"]

# Backend production stage
FROM python:3.10-slim AS backend
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY backend/src/ ./src/
COPY backend/models/ ./models/
COPY backend/config/ ./config/
COPY backend/migrations/ ./migrations/
COPY backend/alembic.ini .
COPY backend/docker-entrypoint.sh .

# Create necessary directories and set permissions
RUN mkdir -p /app/data /app/logs && \
    chmod +x docker-entrypoint.sh

ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["./docker-entrypoint.sh"] 