import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import sql
import bcrypt
import logging
import os
from typing import List, Optional
from config import DATABASE_CONFIG  # Ensure this uses environment variables

# Configure logging for the application
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class Database:
    def __init__(self):
        """Initialize the database connection."""
        self.connection = None

    def connect(self, retries: int = 3, delay: int = 5):
        """
        Establish a connection to the database with retry logic.
        :param retries: Number of retry attempts for connection.
        :param delay: Delay in seconds between retries.
        """
        for attempt in range(retries):
            try:
                self.connection = psycopg2.connect(**DATABASE_CONFIG)
                logging.info("Database connected successfully.")
                return
            except Exception as e:
                logging.warning(f"Attempt {attempt + 1} to connect failed. Retrying in {delay}s...")
                if attempt < retries - 1:
                    import time
                    time.sleep(delay)
        logging.error("Failed to connect to the database after multiple attempts.")
        raise ConnectionError("Database connection failed.")

    def close_connection(self):
        """Close the database connection gracefully."""
        if self.connection:
            logging.info("Closing database connection...")
            self.connection.close()
            self.connection = None
            logging.info("Database connection closed.")

    def insert_user(self, username: str, password: str, face_encoding: List[float]):
        """
        Insert user credentials and face encoding into the database.
        Uses bcrypt for password hashing and validates data formats.
        :param username: User's username.
        :param password: User's plaintext password.
        :param face_encoding: List of numerical face encoding data.
        """
        if not self.connection:
            raise ConnectionError("Database connection not established. Call connect() first.")

        if not isinstance(face_encoding, list):
            raise ValueError("face_encoding must be a list of numerical values.")

        try:
            # Secure the password using bcrypt
            hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

            # Use a prepared query for insertion
            query = """
                INSERT INTO users (username, password, face_encoding)
                VALUES (%s, %s, %s)
            """

            with self.connection.cursor() as cursor:
                cursor.execute(query, (username, hashed_password, str(face_encoding)))
                self.connection.commit()
                logging.info("User successfully added.")
        except Exception as e:
            self.connection.rollback()
            logging.error(f"Error inserting user: {e}")
            raise

    def fetch_user(self, username: str) -> Optional[dict]:
        """
        Fetch user information from the database by username.
        :param username: User's username to search for.
        :return: Dictionary of user data, or None if the user is not found.
        """
        if not self.connection:
            raise ConnectionError("Database connection not established. Call connect() first.")

        try:
            query = """
                SELECT username, password, face_encoding FROM users WHERE username = %s
            """
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (username,))
                user = cursor.fetchone()
                logging.info(f"Fetched user: {username}")
                return user
        except Exception as e:
            logging.error(f"Error fetching user: {e}")
            raise

    def delete_user(self, username: str):
        """
        Delete a user from the database by username.
        :param username: The username of the user to delete.
        """
        if not self.connection:
            raise ConnectionError("Database connection not established. Call connect() first.")

        try:
            query = """
                DELETE FROM users WHERE username = %s
            """
            with self.connection.cursor() as cursor:
                cursor.execute(query, (username,))
                self.connection.commit()
                logging.info(f"User {username} successfully deleted.")
        except Exception as e:
            self.connection.rollback()
            logging.error(f"Error deleting user: {e}")
            raise

    def reset_table(self, table_name: str):
        """
        Delete all records from a specific table, useful for testing purposes.
        :param table_name: The name of the table to reset.
        """
        if not self.connection:
            raise ConnectionError("Database connection not established. Call connect() first.")

        try:
            query = sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE").format(
                sql.Identifier(table_name)
            )
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                self.connection.commit()
                logging.info(f"Table {table_name} reset successfully.")
        except Exception as e:
            self.connection.rollback()
            logging.error(f"Error resetting table {table_name}: {e}")
            raise


if __name__ == "__main__":
    db = Database()
    try:
        db.connect()
        # Example usage
        face_encoding = [0.1, 0.2, 0.3, 0.4]
        db.insert_user("john_doe", "securepassword123", face_encoding)

        # Example fetch
        user = db.fetch_user("john_doe")
        if user:
            print(f"Fetched user: {user}")

        # Example delete
        db.delete_user("john_doe")

    finally:
        db.close_connection()

