import cv2
import face_recognition
import numpy as np
import psycopg2
from scipy.spatial import distance
import logging
from app.config import DATABASE_CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def get_stored_encodings():
    """Fetch stored face encodings from the PostgreSQL database."""
    try:
        with psycopg2.connect(**DATABASE_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT name, encoding FROM face_encodings;")
                stored_faces = cur.fetchall()

        known_encodings = []
        known_names = []

        for name, encoding in stored_faces:
            if isinstance(encoding, str):
                try:
                    encoding_array = np.array([float(x) for x in encoding.split(" ")])
                except ValueError:
                    logging.warning(f"❌ Invalid encoding format for {name}: {encoding}")
                    continue
            elif isinstance(encoding, (list, tuple)):
                encoding_array = np.array(encoding)
            else:
                logging.warning(f"❌ Skipping entry with invalid encoding type for {name}")
                continue

            known_encodings.append(encoding_array)
            known_names.append(name)

        # Warn if encodings and names count mismatch
        if len(known_encodings) != len(known_names):
            logging.warning("⚠️ Mismatch between the number of encodings and names in the database.")

        return known_encodings, known_names

    except Exception as e:
        logging.error(f"❌ Database Error: {e}")
        return [], []


def match_face(detected_encoding, known_encodings, known_names, threshold=0.6):
    """Matches a detected face encoding with stored encodings."""
    if not known_encodings or not known_names:
        logging.warning("⚠️ No known encodings or names found for matching.")
        return None

    matches = face_recognition.compare_faces(known_encodings, detected_encoding, tolerance=threshold)
    face_distances = face_recognition.face_distance(known_encodings, detected_encoding)

    # Find the best match based on distance
    best_match_index = np.argmin(face_distances) if len(face_distances) > 0 else None

    if best_match_index is not None and matches[best_match_index]:
        return known_names[best_match_index]

    return None


def recognize_faces(video_source=0, max_iterations=None):
    """Captures a webcam feed, detects faces, and matches against stored encodings."""
    known_encodings, known_names = get_stored_encodings()

    cap = cv2.VideoCapture(video_source)
    if not cap.isOpened():
        logging.error("❌ Camera error: Unable to access video feed.")
        return

    iteration_count = 0

    try:
        while True:
            # Optional max iteration limit
            if max_iterations is not None and iteration_count >= max_iterations:
                logging.info("🔄 Max iteration limit reached. Exiting.")
                break
            iteration_count += 1

            ret, frame = cap.read()
            if not ret:
                logging.error("❌ Frame capture error.")
                break

            # Resize frame to improve performance
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            # Detect and encode faces
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            identified_faces = []

            for i, face_encoding in enumerate(face_encodings):
                match_name = match_face(face_encoding, known_encodings, known_names)
                label = match_name if match_name else "Unidentified"
                identified_faces.append((label, face_locations[i]))

            # Draw rectangles and labels on the original frame
            for label, (top, right, bottom, left) in identified_faces:
                # Adjust coordinates back to the original frame size
                top, right, bottom, left = (top * 4, right * 4, bottom * 4, left * 4)
                color = (0, 255, 0) if label != "Unidentified" else (0, 0, 255)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            # Display the result
            resized_frame = cv2.resize(frame, (800, 600))
            cv2.imshow("Live Face Recognition", resized_frame)

            # Break the loop on key press 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                logging.info("🛑 Termination signal received. Exiting.")
                break

    except Exception as e:
        logging.error(f"❌ An unexpected error occurred: {e}")
    finally:
        # Release resources
        cap.release()
        cv2.destroyAllWindows()
        logging.info("📷 Camera and resources released.")


if __name__ == "__main__":
    recognize_faces(video_source=0, max_iterations=1000)  # Example: Limit to 1000 iterations

    cv2.destroyAllWindows()