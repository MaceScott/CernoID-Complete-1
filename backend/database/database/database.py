import sqlite3
import os


class Database:
    def __init__(self, db_path="cerno_id.db"):
        self.db_path = db_path
        self.connection = None
        self.initialize_db()

    def connect(self):
        """
        Establish connection to the database.
        """
        if not self.connection:
            self.connection = sqlite3.connect(self.db_path)
        return self.connection

    def initialize_db(self):
        """
        Initialize the database: Create tables and insert default data if necessary.
        """
        conn = self.connect()
        cursor = conn.cursor()

        # Read and execute the schema file
        with open(os.path.join(os.path.dirname(__file__), "schema.sql"), "r") as schema_file:
            cursor.executescript(schema_file.read())

        conn.commit()

    def fetch_user_by_username(self, username):
        """
        Fetch user details by username.
        Returns None if the user does not exist.
        """
        cursor = self.connect().cursor()
        query = "SELECT * FROM users WHERE username = ?"
        cursor.execute(query, (username,))
        return cursor.fetchone()

    def fetch_all_encodings(self):
        """
        Fetch all users' face encodings.
        """
        cursor = self.connect().cursor()
        query = "SELECT id, username, face_encoding FROM users"
        cursor.execute(query)
        return cursor.fetchall()

    def insert_user(self, username, password, role, face_encoding=None):
        """
        Add a new user to the database. Supports face encoding if available.
        """
        conn = self.connect()
        cursor = conn.cursor()
        query = "INSERT INTO users (username, password, role, face_encoding) VALUES (?, ?, ?, ?)"
        cursor.execute(query, (username, password, role, face_encoding))
        conn.commit()

    def fetch_permissions_by_role(self, role):
        """
        Fetch permissions associated with a specific role.
        """
        cursor = self.connect().cursor()
        query = "SELECT permission FROM roles_permissions WHERE role = ?"
        cursor.execute(query, (role,))
        return [row[0] for row in cursor.fetchall()]
data');