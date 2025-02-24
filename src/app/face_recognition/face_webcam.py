import cv2
import dlib
from config import SHAPE_PREDICTOR_PATH  # If unused, remove this import


def face_detection_from_webcam():
    # Initialize dlib's face detector
    detector = dlib.get_frontal_face_detector()
    # Access the default webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise OSError("Webcam could not be opened. Please check if it's connected and permissions are granted.")

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

