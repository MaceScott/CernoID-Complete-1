import cv2
import threading
import tkinter as tk
from tkinter import Canvas, Frame
from PIL import Image, ImageTk
from camera_recognition import detect_faces
import time
from queue import Queue, Empty


class MultiCameraMonitor:
    def __init__(self, container, cameras=None):
        """
        Initialize the MultiCameraMonitor with a container and optional list of camera indices.
        """
        self.container = container
        self.cameras = cameras or self.detect_available_cameras()  # Dynamically detect cameras if not provided
        self.threads = []
        self.stop_event = threading.Event()
        self.frames_queue = {}  # A queue for each camera to handle frames
        self.labels = {}  # Keeps references to Tkinter labels for each camera
        self.create_scrollable_frame()

    def detect_available_cameras(self):
        """
        Dynamically detect available cameras.
        """
        available_cameras = []
        for i in range(10):  # Check a reasonable number of camera indices
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available_cameras.append(i)
                cap.release()
        return available_cameras

    def create_scrollable_frame(self):
        """
        Create a scrollable frame to display multiple camera feeds.
        """
        # Main canvas for scrolling
        self.canvas = Canvas(self.container)
        self.canvas.pack(side="left", fill="both", expand=True)

        # Scrollbar
        scrollbar = tk.Scrollbar(self.container, orient="vertical", command=self.canvas.yview)
        scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Frame inside the canvas
        scrollable_frame = Frame(self.canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # Create labels and threads for each camera
        for i, camera_index in enumerate(self.cameras):
            tk.Label(scrollable_frame, text=f"Camera {i + 1}").pack()
            video_label = tk.Label(scrollable_frame)
            video_label.pack()

            # Maintain references to labels and queues
            self.labels[camera_index] = video_label
            self.frames_queue[camera_index] = Queue()

            # Start separate threads for capturing and displaying
            capture_thread = threading.Thread(target=self.capture_feed, args=(camera_index,))
            display_thread = threading.Thread(target=self.display_feed, args=(camera_index,))

            capture_thread.daemon = True
            display_thread.daemon = True

            capture_thread.start()
            display_thread.start()

            self.threads.append(capture_thread)
            self.threads.append(display_thread)

    def capture_feed(self, camera_index):
        """
        Captures frames from a specified camera index and puts them in a queue.
        """
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            print(f"Error: Unable to open camera {camera_index}")
            return

        while not self.stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                print(f"Warning: Camera {camera_index} stopped sending frames.")
                break

            # Perform face detection or any frame preprocessing
            frame_with_faces = detect_faces(frame)

            # Add the frame to the queue for the display thread
            if not self.frames_queue[camera_index].full():
                self.frames_queue[camera_index].put(frame_with_faces)
            time.sleep(0.03)  # Adjust frame capture rate to prevent overloading

        cap.release()

    def display_feed(self, camera_index):
        """
        Reads frames from the queue and updates the tkinter label.
        """
        label = self.labels[camera_index]
        queue = self.frames_queue[camera_index]

        while not self.stop_event.is_set():
            try:
                # Fetch a frame from the queue
                frame = queue.get(timeout=0.1)  # Timeout to prevent blocking
                img_tk = self.cv2_to_tkinter_image(frame)

                # Update Tkinter label
                label.imgtk = img_tk
                label.configure(image=img_tk)
            except Empty:
                continue  # If no frame is available, keep looping

    def stop_all_threads(self):
        """
        Signal all threads to stop and wait for them to finish.
        """
        self.stop_event.set()
        for thread in self.threads:
            thread.join()
        print("All threads stopped.")

    @staticmethod
    def cv2_to_tkinter_image(frame):
        """
        Converts a CV2 image into a format that Tkinter can display.
        """
        if frame is None:
            return None
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        return ImageTk.PhotoImage(img)


# Example usage
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Multi-Camera Monitor")
    root.geometry("800x600")

    # Create the MultiCameraMonitor instance
    app = MultiCameraMonitor(root)


    # Define cleanup behavior on app close
    def on_close():
        app.stop_all_threads()
        root.destroy()


    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

