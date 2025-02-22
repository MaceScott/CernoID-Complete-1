import sqlite3
import os
import logging


class Database:
    def __init__(self, db_path="cerno_id.db"):
        self.db_path = db_path
        self.connection = None
        self.initialize_db()

    def connect(self):
        """
        Establish and return a connection to the database.
        """
        try:
            if not self.connection:
                self.connection = sqlite3.connect(self.db_path)
            return self.connection
        except sqlite3.Error as e:
            logging.error(f"Error connecting to the database: {e}")
            raise RuntimeError("Failed to establish a database connection.") from e

    def close_connection(self):
        """
        Safely close the database connection.
        """
        if self.connection:
            try:
                self.connection.close()
                self.connection = None
            except sqlite3.Error as e:
                logging.warning(f"Error closing the database connection: {e}")

    def initialize_db(self):
        """
        Initialize the database: Create tables and insert default data if necessary.
        """
        schema_file_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        if not os.path.exists(schema_file_path):
            logging.error(f"Schema file not found at {schema_file_path}")
            raise FileNotFoundError(f"Missing schema file: {schema_file_path}")

        try:
            conn = self.connect()
            with conn:
                with open(schema_file_path, "r") as schema_file:
                    conn.executescript(schema_file.read())
            logging.info("Database initialized successfully.")
        except (sqlite3.Error, FileNotFoundError, OSError) as e:
            logging.error(f"Error initializing the database: {e}")
            raise RuntimeError("Failed to initialize the database.") from e

    def fetch_user_by_username(self, username):
        """
        Fetch user details by username.
        Returns None if the user does not exist.
        """
        if not username:
            logging.warning("Username cannot be empty.")
            raise ValueError("The username parameter must not be empty.")

        query = "SELECT * FROM users WHERE username = ?"
        try:
            with self.connect() as conn:
                cursor = conn.execute(query, (username,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            logging.error(f"Error executing query for username {username}: {e}")
            raise RuntimeError("Failed to fetch user details.") from e

    def fetch_all_encodings(self):
        """
        Fetch all users' face encodings.
        Returns an empty list if no records are found.
        """
        query = "SELECT id, username, face_encoding FROM users"
        try:
            with self.connect() as conn:
                cursor = conn.execute(query)
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Error fetching all face encodings: {e}")
            raise RuntimeError("Failed to fetch face encodings.") from e

    def insert_user(self, username, password, role, face_encoding=None):
        """
        Add a new user to the database. Supports face encoding if provided.
        """
        if not username or not password or not role:
            logging.warning("Username, password, and role are required fields.")
            raise ValueError("Username, password, and role must not be empty.")

        query = "INSERT INTO users (username, password, role, face_encoding) VALUES (?, ?, ?, ?)"
        try:
            with self.connect() as conn:
                conn.execute(query, (username, password, role, face_encoding))
                conn.commit()
                logging.info(f"User '{username}' inserted successfully.")
        except sqlite3.IntegrityError as e:
            logging.error(f"Duplicate user insertion attempted for username '{username}': {e}")
            raise ValueError(f"User '{username}' already exists.") from e
        except sqlite3.Error as e:
            logging.error(f"Error inserting user {username}: {e}")
            raise RuntimeError("Failed to insert user into database.") from e

    def fetch_permissions_by_role(self, role):
        """
        Fetch permissions associated with a specific role.
        Returns an empty list if no permissions are found.
        """
        if not role:
            logging.warning("Role cannot be empty.")
            raise ValueError("The role parameter must not be empty.")

        query = "SELECT permission FROM roles_permissions WHERE role = ?"
        try:
            with self.connect() as conn:
                cursor = conn.execute(query, (role,))
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Error fetching permissions for role '{role}': {e}")
            raise RuntimeError("Failed to fetch role permissions.") from e

data');