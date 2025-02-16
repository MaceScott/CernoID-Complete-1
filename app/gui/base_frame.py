import tkinter as tk
from tkinter import filedialog, messagebox
from app.face_recognition.face_detection import detect_faces
from app.face_recognition.face_encoding import encode_faces
from app.face_recognition.face_matching import match_faces
from pathlib import Path
import yaml
import threading

# Load configuration
CONFIG_FILE = Path("config/config.yaml")
if not CONFIG_FILE.exists():
    messagebox.showerror("Error", f"Configuration file not found: {CONFIG_FILE}")
    exit()

try:
    with open(CONFIG_FILE, "r") as f:
        config = yaml.safe_load(f)
    IMAGE_FOLDER = Path(config.get("IMAGE_FOLDER", ""))
    if not IMAGE_FOLDER.exists():
        raise ValueError(f"Invalid or missing 'IMAGE_FOLDER' in config.yaml: {IMAGE_FOLDER}")
except Exception as e:
    messagebox.showerror("Error", f"Failed to load configuration file: {e}")
    exit()


class CernoIDApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CernoID - Face Recognition System")
        self.root.geometry("600x400")

        # UI components
        self.create_widgets()

    def create_widgets(self):
        # Heading
        tk.Label(self.root, text="CernoID - Face Recognition", font=("Arial", 16, "bold")).pack(pady=10)

        # Instruction Label
        tk.Label(self.root, text=f"Images will be processed from: {IMAGE_FOLDER}", font=("Arial", 12)).pack(pady=5)

        # Detect Faces Button
        self.detect_faces_button = tk.Button(self.root, text="Detect Faces", command=self.threaded_detect_faces)
        self.detect_faces_button.pack(pady=10)

        # Encode Face Button
        self.encode_faces_button = tk.Button(self.root, text="Encode Faces", command=self.threaded_encode_faces)
        self.encode_faces_button.pack(pady=10)

        # Match Faces Button
        self.match_faces_button = tk.Button(self.root, text="Match Faces", command=self.threaded_match_faces)
        self.match_faces_button.pack(pady=10)

        # Exit Button
        tk.Button(self.root, text="Exit", command=self.root.quit).pack(pady=20)

    # Threaded helpers to keep the UI responsive
    def threaded_detect_faces(self):
        threading.Thread(target=self.detect_faces, daemon=True).start()

    def threaded_encode_faces(self):
        threading.Thread(target=self.encode_faces, daemon=True).start()

    def threaded_match_faces(self):
        threading.Thread(target=self.match_faces, daemon=True).start()

    # Core functionalities
    def detect_faces(self):
        # Logic for face detection
        pass

    def encode_faces(self):
        # Logic for face encoding
        pass

    def match_faces(self):
        # Logic for face matching
        pass


if __name__ == "__main__":
    root = tk.Tk()
    app = CernoIDApp(root)
    root.mainloop()


