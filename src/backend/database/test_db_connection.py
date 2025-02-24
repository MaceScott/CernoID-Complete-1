import os
import psycopg2
import logging
from psycopg2 import sql

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("db_connection.log")
    ]
)

# Validate critical environment variables
REQUIRED_ENV_VARS = ["DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT"]
for var in REQUIRED_ENV_VARS:
    if not os.getenv(var):
        logging.error(f"The required environment variable {var} is missing.")
        raise ValueError(f"Environment variable {var} is not set.")

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")


def ensure_table_exists(cursor):
    logging.info("Ensuring the `users` table exists.")
    cursor.execute(sql.SQL("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            face_encoding BYTEA
        );
    """))


def insert_test_data(cursor):
    logging.info("Inserting a test user.")
    test_face_data = b'\x00\x01\x02'  # Example binary data for testing purposes
    cursor.execute(
        "INSERT INTO users (name, face_encoding) VALUES (%s, %s) RETURNING id;",
        ("Test User", test_face_data)
    )
    user_id = cursor.fetchone()[0]
    logging.info(f"Test user inserted with id: {user_id}")
    return user_id


def retrieve_data(cursor, user_id):
    logging.debug(f"Retrieving user data for id: {user_id}")
    cursor.execute("SELECT * FROM users WHERE id = %s;", (user_id,))
    user_data = cursor.fetchone()
    logging.info(f"Retrieved User: {user_data}")
    return user_data


def test_db_connection():
    try:
        with psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT,
                connect_timeout=10
        ) as conn:
            with conn.cursor() as cursor:
                ensure_table_exists(cursor)
                user_id = insert_test_data(cursor)
                conn.commit()
                retrieve_data(cursor, user_id)

    except psycopg2.OperationalError:
        logging.error("Database Operational Error occurred.", exc_info=True)
    except Exception as e:
        logging.error("An unexpected error occurred.", exc_info=True)
        raise
    else:
        logging.info("✅ Database connection and test operations completed successfully.")


if __name__ == "__main__":
    test_db_connection()
