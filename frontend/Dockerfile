# Build stage
FROM node:18-alpine as builder
WORKDIR /app

# Install build dependencies
RUN apk add --no-cache python3 make g++ netcat-openbsd

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

# Generate Prisma client and build
RUN npx prisma generate
RUN npm run build

# Production stage
FROM node:18-alpine
WORKDIR /app

# Install runtime dependencies
RUN apk add --no-cache curl bash netcat-openbsd

# Copy built assets
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/public ./public

# Copy runtime files
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

# Set environment variables
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000

# Create non-root user
RUN addgroup -g 1001 -S nodejs \
    && adduser -S nextjs -u 1001 \
    && chown -R nextjs:nodejs /app

USER nextjs

# Expose port
EXPOSE 3000

# Health check with improved parameters
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -sf http://localhost:3000/api/health || exit 1

# Start the application
ENTRYPOINT ["./docker-entrypoint.sh"] 