# Build stage
FROM node:18-alpine AS builder
WORKDIR /app

# Copy package files first to leverage cache
COPY package*.json ./
COPY next.config.js ./
COPY tsconfig.json ./
COPY tailwind.config.ts ./
COPY postcss.config.js ./

# Install dependencies
RUN npm install

# Copy all source files
COPY src ./src
COPY public ./public
COPY .env* ./

# Build the application
RUN npm run build

# Production stage
FROM node:18-alpine
WORKDIR /app

# Install wget for health checks
RUN apk add --no-cache wget

# Copy only necessary files from builder
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/src ./src
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/next.config.js ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.env* ./

# Copy entrypoint script
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

# Set environment variables
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD wget --spider http://localhost:3000 || exit 1

# Use entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"] 