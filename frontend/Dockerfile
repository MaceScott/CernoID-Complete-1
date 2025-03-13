# Build stage
FROM node:18-alpine AS builder
WORKDIR /app

# Install dependencies including OpenSSL
RUN apk add --no-cache python3 make g++ netcat-openbsd openssl openssl-dev

# Copy package files
COPY package*.json ./
COPY next.config.js ./
COPY tsconfig.json ./
COPY tailwind.config.ts ./
COPY postcss.config.js ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy source code
COPY app ./app
COPY public ./public
COPY .env* ./
COPY prisma ./prisma

# Generate Prisma client
RUN npx prisma generate

# Build the application
RUN npm run build

# Production stage
FROM node:18-alpine AS stage-1

# Install OpenSSL and other dependencies
RUN apk add --no-cache curl bash netcat-openbsd openssl openssl-dev

# Set working directory
WORKDIR /app

# Copy necessary files from builder
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/public ./public
COPY --from=builder /app/prisma ./prisma

# Copy entrypoint script
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

# Create non-root user
RUN addgroup -g 1001 -S nodejs \
    && adduser -S nextjs -u 1001 \
    && chown -R nextjs:nodejs /app

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Health check with improved parameters
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -sf http://localhost:3000/api/health || exit 1

# Start the application
CMD ["./docker-entrypoint.sh"] 