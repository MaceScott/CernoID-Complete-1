import os
import cv2
import threading
import time
import hashlib
import face_recognition
import numpy as np
from database import Database
from notifications import Notifications
from cachetools import TTLCache  # For efficient temporary caching


class CameraRecognition:
    """
    A professional, scalable, and extensible camera-based face recognition system.
    This class uses multithreading for efficient real-time processing and follows best practices for security, modularity, and maintainability.
    """

    def __init__(self, camera_index=0):
        """
        Initialize the CameraRecognition system.

        :param camera_index: Index of the camera to use.
        """
        self.camera_index = camera_index
        self.db = Database()  # Connect to face database
        self.notifications = Notifications(
            twilio_sid=os.getenv("TWILIO_ACCOUNT_SID"),
            twilio_auth=os.getenv("TWILIO_AUTH_TOKEN"),
            from_phone=os.getenv("TWILIO_PHONE"),
            smtp_server=os.getenv("SMTP_SERVER"),
            smtp_user=os.getenv("SMTP_USER"),
            smtp_pass=os.getenv("SMTP_PASSWORD")
        )
        self.known_face_encodings = []
        self.known_face_names = []
        self.unidentified_faces = TTLCache(maxsize=100,
                                           ttl=300)  # TTL cache for unrecognized faces (tracks them for 5 minutes)
        self.load_known_faces()

    def load_known_faces(self):
        """
        Load all known face encodings and their names from the database.
        Handles database-related errors gracefully.
        """
        try:
            users = self.db.fetch_all_encodings()
            for user in users:
                name, encoding = user[1], np.frombuffer(user[2], dtype=np.float64)
                self.known_face_names.append(name)
                self.known_face_encodings.append(encoding)
            print(f"[INFO] Loaded {len(self.known_face_names)} known faces from the database.")
        except Exception as e:
            print(f"[ERROR] Failed to load known faces: {e}")

    def detect_and_recognize_faces(self, frame):
        """
        Detect and recognize faces in the given frame. Registers unknown faces.

        :param frame: The current video frame to process.
        :return: Frame with annotated recognized and unrecognized faces.
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detect face locations and encodings
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            # Compare to known faces
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.6)
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            name, color = "Unidentified", (0, 0, 255)  # Default to unidentified

            if matches:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = self.known_face_names[best_match_index]
                    color = (0, 255, 0)  # Green for recognized faces

            # Handle unidentified faces
            if name == "Unidentified":
                face_hash = hashlib.sha256(face_encoding).hexdigest()
                if face_hash not in self.unidentified_faces:
                    self.unidentified_faces[face_hash] = time.time()
                    cropped_face = frame[top:bottom, left:right]
                    threading.Thread(target=self.trigger_registration, args=(cropped_face,)).start()

            # Annotate frame
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

        return frame

    def trigger_registration(self, cropped_face):
        """
        Trigger dynamic registration for an unidentified face. Saves the cropped face and logs the action.

        :param cropped_face: Cropped image of the unidentified face.
        """
        try:
            timestamp = int(time.time())
            save_dir = "unidentified_faces"
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, f"unidentified_{timestamp}.jpg")
            cv2.imwrite(save_path, cropped_face)
            print(f"[ALERT] Unidentified face saved to: {save_path}")
            self.trigger_alert()  # Optionally trigger an alert
        except Exception as e:
            print(f"[ERROR] Failed to save unidentified face: {e}")

    def trigger_alert(self):
        """
        Send notifications for an unidentified face in a restricted area.
        """
        try:
            self.notifications.send_sms_alert("+1234567890", "Unverified individual detected in a restricted area!")
            self.notifications.send_email_alert(
                "admin@example.com",
                "Security Alert: Unverified Individual",
                "An unverified individual was detected in a restricted area. Please check the surveillance feed."
            )
            print("[INFO] Alert sent successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to send alert: {e}")

    def start(self):
        """
        Start the real-time camera feed for face detection and recognition.
        Uses error handling and ensures proper resource cleanup.
        """
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            print(f"[ERROR] Failed to open camera (Index: {self.camera_index}). Please check the camera connection.")
            return

        try:
            print("[INFO] Camera started. Press 'q' to quit.")
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    print("[ERROR] Failed to capture frame. Exiting.")
                    break

                # Process and display the frame
                processed_frame = self.detect_and_recognize_faces(frame)
                cv2.imshow("Camera Feed - Real-Time Face Recognition", processed_frame)

                # Quit option
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("[INFO] Exiting camera feed...")
                    break
        except Exception as e:
            print(f"[ERROR] An error occurred during camera feed: {e}")
        finally:
            cap.release()
            cv2.destroyAllWindows()
            print("[INFO] Camera and windows released successfully.")



