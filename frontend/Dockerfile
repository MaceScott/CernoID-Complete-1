# Build stage
FROM node:18.19-slim AS builder
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    make \
    g++ \
    netcat-traditional \
    openssl \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV BACKEND_URL=http://backend:8000
ENV NEXT_PUBLIC_BACKEND_URL=http://backend:8000
ENV NEXT_PUBLIC_APP_URL=http://localhost:3000
ENV DATABASE_URL="postgresql://postgres:postgres@db:5432/cernoid?schema=public"
ENV NODE_ENV=production

# Copy package files and Prisma schema
COPY package*.json ./
COPY prisma ./prisma/

# Install dependencies
RUN npm install --no-package-lock --legacy-peer-deps

# Copy the rest of the application
COPY . .

# Generate Prisma client
RUN npx prisma generate

# Build the application
RUN npm run build

# Production stage
FROM node:18.19-slim AS runner

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    netcat-traditional \
    openssl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy package files and Prisma schema
COPY package*.json ./
COPY prisma ./prisma/

# Install production dependencies
RUN npm install --no-package-lock --legacy-peer-deps --production

# Copy built application from builder
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/next.config.js ./next.config.js

# Set environment variables
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Expose the port the app runs on
EXPOSE 3000

# Health check with improved parameters
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -sf http://localhost:3000/health || exit 1

# Start the application
CMD ["npm", "start"] 