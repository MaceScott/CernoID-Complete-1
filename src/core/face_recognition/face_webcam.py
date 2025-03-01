import cv2
import dlib
from config import SHAPE_PREDICTOR_PATH  # If unused, remove this import
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def face_detection_from_webcam():
    # Initialize dlib's face detector
    detector = dlib.get_frontal_face_detector()
    # Access the default webcam
    cap = cv2.VideoCapture(0)

    # Enhanced logging for webcam initialization
    logger.info("Initializing webcam for face detection.")

    # Improved error handling for webcam access
    if not cap.isOpened():
        logger.error("Webcam could not be opened. Please check connection and permissions.")
        raise OSError("Webcam could not be opened.")

    # Adjust frame resolution for performance optimization
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("Press 'q' to quit")
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to capture frame")
                break
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Detect faces
            faces = detector(gray)
            # Enhanced logging for face detection
            logger.info(f"Detected {len(faces)} faces in current frame.")
            # Draw rectangles around the faces
            for face in faces:
                x, y = face.left(), face.top()
                w = face.right() - face.left()
                h = face.bottom() - face.top()
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            # Display the video with detected faces
            cv2.imshow("Webcam - Face Detection", frame)
            # Press 'q' to exit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        face_detection_from_webcam()
    except Exception as e:
        print(f"Error: {e}")

