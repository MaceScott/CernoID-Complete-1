"""Alembic migrations environment."""
import os
import sys
from logging.config import fileConfig

import psycopg2
from alembic import context

# Add src directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from core.database.models import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url="postgresql://postgres:postgres@db:5432/cernoid",
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Connect directly using psycopg2
    conn = psycopg2.connect(
        dbname="cernoid",
        user="postgres",
        password="postgres",
        host="db",
        port="5432"
    )
    conn.autocommit = False

    context.configure(
        connection=conn,
        target_metadata=target_metadata
    )

    try:
        with context.begin_transaction():
            context.run_migrations()
    finally:
        conn.close()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online() 