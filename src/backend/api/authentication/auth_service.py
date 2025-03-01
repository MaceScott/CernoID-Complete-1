import cv2
import numpy as np
from face_recognition import face_encodings, compare_faces
from database.database import Database
from bcrypt import checkpw

class AuthService:
    def __init__(self):
        self.db = Database()
        self.known_encodings_cache = None

    def load_known_encodings(self):
        if self.known_encodings_cache is None:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                users = self.db.fetch_all_encodings(cursor)
                self.known_encodings_cache = [(username, np.frombuffer(saved_encoding, dtype=np.float64)) for _, username, saved_encoding in users]

    def authenticate_face(self, frame):
        self.load_known_encodings()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        detected_encodings = face_encodings(rgb_frame)

        if detected_encodings:
            matches = compare_faces([encoding for _, encoding in self.known_encodings_cache], detected_encodings[0], tolerance=0.6)
            for match, (username, _) in zip(matches, self.known_encodings_cache):
                if match:
                    return username
        return None

    def authenticate_manual(self, username, password):
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            user = self.db.fetch_user_by_username(cursor, username)
            if user:
                stored_hashed_password = user[2]
                if checkpw(password.encode(), stored_hashed_password.encode()):
                    return True
        return False 