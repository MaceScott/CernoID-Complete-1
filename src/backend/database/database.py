import os
import logging
from psycopg2 import sql, pool
from psycopg2.extras import RealDictCursor
import bcrypt
from typing import List, Optional, Dict
from config import DATABASE_CONFIG
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


class Database:
    """
    A class to interact with the PostgreSQL database using connection pooling.
    """

    _connection_pool = None

    def __init__(self):
        """Initialize the class and ensure the connection pool is created."""
        if not Database._connection_pool:
            self._initialize_pool()

    @classmethod
    def _initialize_pool(cls):
        """
        Create the connection pool with the database configuration.
        This should only be done once during the lifetime of the application.
        """
        try:
            logging.info("Initializing database connection pool...")
            cls._connection_pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                **DATABASE_CONFIG
            )
            logging.info("Database connection pool initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize database connection pool: {e}")
            raise

    def _get_connection(self):
        """
        Get a connection from the connection pool.
        This method ensures a connection is always available.
        """
        if not self._connection_pool:
            raise ConnectionError("Connection pool not initialized.")
        try:
            return self._connection_pool.getconn()
        except Exception as e:
            logging.error(f"Error retrieving connection from the pool: {e}")
            raise

    def _release_connection(self, conn):
        """
        Release a connection back to the pool.
        :param conn: The connection to be released.
        """
        if not self._connection_pool:
            raise ConnectionError("Connection pool not initialized.")
        try:
            self._connection_pool.putconn(conn)
        except Exception as e:
            logging.error(f"Error releasing connection to the pool: {e}")
            raise

    def insert_user(self, username: str, password: str, face_encoding: List[float]):
        """
        Insert user credentials and face encoding into the database.
        Passwords are hashed for security using bcrypt.
        :param username: The user's username.
        :param password: The user's plaintext password.
        :param face_encoding: List of numerical face encoding data.
        """
        if not isinstance(face_encoding, list) or not all(isinstance(val, float) for val in face_encoding):
            raise ValueError("face_encoding must be a list of numerical (float) values.")

        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        query = """
            INSERT INTO users (username, password, face_encoding)
            VALUES (%s, %s, %s)
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (username, hashed_password, str(face_encoding)))  # Store face encoding as string
                conn.commit()
                logging.info(f"User '{username}' successfully added.")
        except Exception as e:
            conn.rollback()
            logging.error(f"Error inserting user '{username}': {e}")
            raise
        finally:
            self._release_connection(conn)

    def fetch_user(self, username: str) -> Optional[Dict]:
        """
        Fetch user information from the database by username.
        :param username: The username to search for.
        :return: A dictionary of user data or None if user not found.
        """
        query = """
            SELECT username, password, face_encoding
            FROM users
            WHERE username = %s
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (username,))
                user = cursor.fetchone()
                logging.info(f"Fetched user '{username}': {user}")
                return user
        except Exception as e:
            logging.error(f"Error fetching user '{username}': {e}")
            raise
        finally:
            self._release_connection(conn)

    def delete_user(self, username: str):
        """
        Delete a user from the database by username.
        :param username: The username of the user to be deleted.
        """
        query = """
            DELETE FROM users WHERE username = %s
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (username,))
                conn.commit()
                logging.info(f"User '{username}' successfully deleted.")
        except Exception as e:
            conn.rollback()
            logging.error(f"Error deleting user '{username}': {e}")
            raise
        finally:
            self._release_connection(conn)

    def reset_table(self, table_name: str):
        """
        Deletes all records from a specified table for testing purposes.
        :param table_name: The name of the table to reset.
        """
        query = sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE").format(
            sql.Identifier(table_name)
        )
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query)
                conn.commit()
                logging.info(f"Table '{table_name}' reset successfully.")
        except Exception as e:
            conn.rollback()
            logging.error(f"Error resetting table '{table_name}': {e}")
            raise
        finally:
            self._release_connection(conn)

    @classmethod
    def close_pool(cls):
        """
        Closes all connections in the connection pool.
        This method should be called at application shutdown.
        """
        if cls._connection_pool:
            logging.info("Closing all connections in the database pool...")
            cls._connection_pool.closeall()
            logging.info("Database connection pool closed.")


# Example only: avoid using this setup in actual main.py
if __name__ == "__main__":
    database = Database()

    try:
        # Example usage
        face_encoding = [0.1, 0.2, 0.3, 0.4]
        database.insert_user("john_doe", "securepassword123", face_encoding)

        # Fetch user
        user = database.fetch_user("john_doe")
        if user:
            print(f"Fetched user: {user}")

        # Delete user
        database.delete_user("john_doe")

    finally:
        Database.close_pool()

# Add connection pooling
engine = create_engine('postgresql://...', 
                      poolclass=QueuePool,
                      pool_size=20,
                      max_overflow=10,
                      pool_timeout=30)
