import cv2
import threading
from camera_recognition import detect_faces
import time


class MultiCameraMonitor:
    def __init__(self, cameras=None):
        """
        Initialize MultiCameraMonitor with optional configurable cameras.

        :param cameras: List of camera indexes or None for default cameras [0, 1].
        """
        self.cameras = cameras if cameras is not None else [0, 1]
        self.threads = []
        self.stop_event = threading.Event()  # Event to signal threads to stop
        self.lock = threading.Lock()  # Ensure thread-safe operations on shared resources

    def start(self):
        """
        Start monitoring all configured cameras.
        Launches a thread for each camera.
        """
        for index in self.cameras:
            thread = threading.Thread(target=self.process_camera_feed, args=(index,))
            thread.daemon = True
            self.threads.append(thread)
            thread.start()

    def process_camera_feed(self, camera_index):
        """
        Capture and process the frames from a single camera feed.

        :param camera_index: Index of the camera to access.
        """
        cap = cv2.VideoCapture(camera_index)

        if not cap.isOpened():
            print(f"[Error] Cannot open camera with index {camera_index}")
            return

        try:
            while not self.stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    print(f"[Warning] No frame captured from camera {camera_index}")
                    time.sleep(0.1)  # Prevent busy waiting when no frame is available
                    continue

                # Detect faces
                faces = detect_faces(frame)
                with self.lock:  # Thread-safe modifications of the frame
                    for (x, y, w, h), name in faces:
                        color = (0, 255, 0) if name != "Unidentified" else (0, 0, 255)
                        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                        cv2.putText(frame, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

                # Display the feed
                cv2.imshow(f"Camera {camera_index}", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.stop_event.set()  # Allow all threads to stop gracefully
                    break
        finally:
            cap.release()
            with self.lock:
                cv2.destroyAllWindows()

    def stop(self):
        """
        Signal all threads to stop and clean up resources.
        """
        print("[Info] Stopping all camera feeds...")
        self.stop_event.set()
        for thread in self.threads:
            thread.join()
        print("[Info] All camera feeds stopped.")

    def add_camera(self, camera_index):
        """
        Add a new camera to the monitor dynamically.

        :param camera_index: Index of the new camera to add.
        """
        print(f"[Info] Adding camera {camera_index}")
        self.cameras.append(camera_index)
        thread = threading.Thread(target=self.process_camera_feed, args=(camera_index,))
        thread.daemon = True
        self.threads.append(thread)
        thread.start()

    def remove_camera(self, camera_index):
        """
        Remove a camera from monitoring (stops associated feed).

        :param camera_index: Index of the camera to remove.
        """
        print(f"[Info] Removing camera {camera_index}")
        self.stop()  # Stop all cameras
        self.cameras = [c for c in self.cameras if c != camera_index]  # Exclude camera
        self.start()  # Restart all remaining cameras


if __name__ == "__main__":
    # Example usage of the MultiCameraMonitor class
    monitor = MultiCameraMonitor()

    try:
        monitor.start()  # Start monitoring cameras
        while True:
            # The main loop to keep the application running
            time.sleep(1)
    except KeyboardInterrupt:
        print("[Info] Ctrl+C detected. Stopping...")
    finally:
        monitor.stop()

