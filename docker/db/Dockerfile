FROM postgres:15-alpine

# Add initialization scripts
COPY ./init.sql /docker-entrypoint-initdb.d/

# Custom PostgreSQL configuration
COPY postgresql.conf /etc/postgresql/postgresql.conf

# Set environment variables
ENV POSTGRES_DB=cernoid
ENV POSTGRES_USER=cernoid
ENV POSTGRES_PASSWORD=cernoid

# Expose port
EXPOSE 5432 