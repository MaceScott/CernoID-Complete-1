# Build stage
FROM node:18.19-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Set build environment variables
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_OPTIONS="--max_old_space_size=2048"
ENV NPM_CONFIG_REGISTRY=https://registry.npmjs.org/
ENV NPM_CONFIG_FETCH_RETRIES=5
ENV NPM_CONFIG_FETCH_RETRY_FACTOR=2
ENV NPM_CONFIG_FETCH_RETRY_MINTIMEOUT=10000
ENV NPM_CONFIG_FETCH_RETRY_MAXTIMEOUT=60000

# Copy package files
COPY package*.json ./
COPY prisma ./prisma/

# Install dependencies with retry logic
RUN npm config set fetch-retries 5 && \
    npm config set fetch-retry-factor 5 && \
    npm config set fetch-retry-mintimeout 20000 && \
    npm config set fetch-retry-maxtimeout 120000 && \
    npm install --legacy-peer-deps && \
    npm install --save-dev typescript @types/react @types/node @types/lodash eslint --legacy-peer-deps

# Copy source code
COPY . .

# Generate Prisma client and build
RUN npx prisma generate && \
    npm run build

# Production stage
FROM node:18.19-slim AS runner

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create non-root user and set up home directory
RUN useradd -r -u 1001 -m nextjs && \
    mkdir -p /app/data /app/public /app/public/models && \
    chown -R nextjs:nextjs /app && \
    chmod -R 755 /app/public/models && \
    mkdir -p /home/nextjs/.npm && \
    chown -R nextjs:nextjs /home/nextjs

# Copy necessary files from builder
COPY --chown=nextjs:nextjs package*.json ./
COPY --chown=nextjs:nextjs prisma ./prisma/
COPY --chown=nextjs:nextjs --from=builder /app/.next ./.next
COPY --chown=nextjs:nextjs --from=builder /app/public ./public
COPY --chown=nextjs:nextjs --from=builder /app/node_modules ./node_modules
COPY --chown=nextjs:nextjs --from=builder /app/next.config.js ./
COPY --chown=nextjs:nextjs --from=builder /app/package.json ./

# Set environment variables
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV HOME=/home/nextjs

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Start the application
CMD ["npm", "start"] 