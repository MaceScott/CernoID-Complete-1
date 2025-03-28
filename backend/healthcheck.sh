#!/bin/sh

# Check if the application is running
curl -f http://localhost:8000/health || exit 1

# Check if database is accessible
python3 -c "from sqlalchemy import create_engine; engine = create_engine('$DATABASE_URL'); engine.connect()" || exit 1

# Check if Redis is accessible
redis-cli -h redis -a "$REDIS_PASSWORD" ping || exit 1

exit 0 