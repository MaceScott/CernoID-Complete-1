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

# Backend build stage
FROM python:3.11-slim AS backend-build
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Backend production stage
FROM python:3.11-slim AS backend
WORKDIR /app
COPY --from=backend-build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-build /app/src ./src
COPY --from=backend-build /app/main.py .
ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["python", "main.py"] 