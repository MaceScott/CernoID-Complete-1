import os
import psycopg2
import logging
from psycopg2 import sql

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler("db_connection.log")  # Log file
    ]
)

# Load database connection settings from environment variables
DB_NAME = os.getenv("DB_NAME", "cernoid")
DB_USER = os.getenv("DB_USER", "cernouser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "JolieAthena#02")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")


def test_db_connection():
    """
    Tests database connection. Inserts a dummy user, retrieves the data, 
    and prints/logs results.
    """
    try:
        # Establish a connection to the database using the `with` context
        with psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT
        ) as conn:
            with conn.cursor() as cursor:
                # Ensure the table 'users' exists
                logging.info("Ensuring the `users` table exists.")
                cursor.execute(sql.SQL("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        name TEXT NOT NULL,
                        face_encoding BYTEA
                    );
                """))

                # Insert a test user into the database
                logging.info("Inserting a test user into the database.")
                cursor.execute(
                    "INSERT INTO users (name, face_encoding) VALUES (%s, %s) RETURNING id;",
                    ("Test User", b'\x00\x01\x02')  # Dummy binary data
                )
                user_id = cursor.fetchone()[0]
                conn.commit()
                logging.info(f"Test user inserted with id: {user_id}")

                # Retrieve and log the inserted user data
                logging.info(f"Retrieving the inserted user with id: {user_id}")
                cursor.execute("SELECT * FROM users WHERE id = %s;", (user_id,))
                user_data = cursor.fetchone()
                logging.info(f"Retrieved User: {user_data}")

    except psycopg2.OperationalError as op_err:
        logging.error("Database Operational Error occurred!", exc_info=True)
    except psycopg2.DatabaseError as db_err:
        logging.error("Database Error occurred!", exc_info=True)
    except Exception as e:
        logging.error("An unexpected error occurred!", exc_info=True)
    else:
        logging.info("✅ Database connection and test operations completed successfully.")


if __name__ == "__main__":
    test_db_connection()


    print(str(e))