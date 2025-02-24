FROM redis:alpine

# Copy custom Redis configuration
COPY redis.conf /usr/local/etc/redis/redis.conf

# Run Redis with custom config
CMD [ "redis-server", "/usr/local/etc/redis/redis.conf" ] 