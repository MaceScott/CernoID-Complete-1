import cv2
import face_recognition
import numpy as np
import psycopg2
from scipy.spatial import distance
import logging
from app.config import DATABASE_CONFIG
from .anti_spoofing import analyze_frame

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def get_stored_encodings():
    """Fetch stored face encodings from the PostgreSQL database."""
    try:
        with psycopg2.connect(**DATABASE_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT name, encoding FROM face_encodings;")
                stored_faces = cur.fetchall()

        return _process_stored_faces(stored_faces)

    except psycopg2.Error as e:
        logging.error(f"Database connection failed: {e}")
        return [], []


def _process_stored_faces(stored_faces):
    """Process and validate stored faces from the database."""
    known_encodings, known_names = [], []

    for name, encoding in stored_faces:
        encoding_array = _convert_encoding(encoding, name)
        if encoding_array is not None:
            known_encodings.append(encoding_array)
            known_names.append(name)

    # Warn if encodings and names count mismatch
    if len(known_encodings) != len(known_names):
        logging.warning("⚠️ Mismatch between the number of encodings and names in the database.")

    return known_encodings, known_names


def _convert_encoding(encoding, name):
    """Convert encoding based on type and validate it."""
    if isinstance(encoding, str):
        return _convert_string_encoding(encoding, name)
    elif isinstance(encoding, (list, tuple)):
        return np.array(encoding)
    else:
        logging.warning(f"❌ Skipping entry with invalid encoding type for {name}")
        return None


def _convert_string_encoding(encoding, name):
    """Convert string encoding to a numpy array."""
    try:
        return np.array([float(x) for x in encoding.split(" ")])
    except ValueError:
        logging.warning(f"❌ Invalid encoding format for {name}: {encoding}")
        return None


def match_face(detected_encoding, known_encodings, known_names, threshold=0.6):
    """Matches a detected face encoding with stored encodings."""
    if not known_encodings or not known_names:
        logging.warning("⚠️ No known encodings or names found for matching.")
        return None

    matches, best_match_index = _get_best_match(detected_encoding, known_encodings, threshold)

    if best_match_index is not None and matches[best_match_index]:
        return known_names[best_match_index]
    return None


def _get_best_match(detected_encoding, known_encodings, threshold):
    """Get the best face match based on encodings and distances."""
    matches = face_recognition.compare_faces(known_encodings, detected_encoding, tolerance=threshold)
    face_distances = face_recognition.face_distance(known_encodings, detected_encoding)
    best_match_index = np.argmin(face_distances) if len(face_distances) > 0 else None
    return matches, best_match_index


def recognize_faces(video_source=0, max_iterations=None):
    """Captures a webcam feed, detects faces, and matches against stored encodings."""
    known_encodings, known_names = get_stored_encodings()

    cap = cv2.VideoCapture(video_source)
    if not cap.isOpened():
        logging.error("❌ Camera error: Unable to access video feed.")
        return

    _process_video_feed(cap, known_encodings, known_names, max_iterations)


def _process_video_feed(cap, known_encodings, known_names, max_iterations):
    """Process video feed for face recognition."""
    iteration_count = 0

    try:
        while True:
            if _should_terminate(iteration_count, max_iterations):
                break
            iteration_count += 1

            ret, frame = cap.read()
            if not ret:
                logging.error("❌ Frame capture error.")
                break

            identified_faces = _detect_and_match_faces(frame, known_encodings, known_names)
            _annotate_and_display_frame(frame, identified_faces)

    except Exception as e:
        logging.error(f"❌ An unexpected error occurred: {e}")
    finally:
        _release_resources(cap)


def _should_terminate(iteration_count, max_iterations):
    """Check whether the process should terminate based on iteration count."""
    if max_iterations is not None and iteration_count >= max_iterations:
        logging.info("🔄 Max iteration limit reached. Exiting.")
        return True
    return False


def _detect_and_match_faces(frame, known_encodings, known_names):
    """Detect faces in the frame and match them to known encodings."""
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

    # Enhanced logging for face detection and matching
    logging.info(f"Detected {len(face_encodings)} faces in current frame.")

    return identified_faces


def _annotate_and_display_frame(frame, identified_faces):
    """Annotate the frame with detected face data and display it."""
    for label, (top, right, bottom, left) in identified_faces:
        # Adjust coordinates back to the original frame size
        top, right, bottom, left = (top * 4, right * 4, bottom * 4, left * 4)
        color = (0, 255, 0) if label != "Unidentified" else (0, 0, 255)
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    resized_frame = cv2.resize(frame, (800, 600))
    cv2.imshow("Live Face Recognition", resized_frame)

    # Break the loop on key press 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        logging.info("🛑 Termination signal received. Exiting.")
        raise StopIteration


def _release_resources(cap):
    """Release video capture and destroy OpenCV windows."""
    cap.release()
    cv2.destroyAllWindows()
    logging.info("📷 Camera and resources released.")


async def verify_face(frame: np.ndarray) -> Optional[FaceMatch]:
    """
    Complete face verification pipeline with anti-spoofing checks.
    """
    # Anti-spoofing check
    if not analyze_frame(frame):
        await self.event_manager.publish('spoofing_detected', {'frame': frame})
        return None

    # Detect face
    detections = await self.detect_faces(frame)
    if not detections:
        await self.event_manager.publish('face_not_detected', {'frame': frame})
        return None

    # Use best detection
    best_detection = max(detections, key=lambda d: d.confidence)

    # Generate encoding
    encodings = await self.encode_faces([best_detection])
    if not encodings:
        await self.event_manager.publish('face_encoding_failed', 
                                      {'detection': best_detection})
        return None

    # Find matches
    matches = await self.find_matches(encodings[0])

    if matches:
        best_match = matches[0]
        await self.event_manager.publish('face_verified', {'match': best_match})
        return best_match

    await self.event_manager.publish('face_unverified', 
                                   {'encoding': encodings[0]})
    return None


if __name__ == "__main__":
    recognize_faces(video_source=0, max_iterations=1000)
