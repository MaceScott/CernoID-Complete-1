import tkinter as tk
from tkinter import filedialog, messagebox
from app.face_recognition.face_detection import detect_faces
from app.face_recognition.face_encoding import encode_faces
from app.face_recognition.face_matching import match_faces
from pathlib import Path
import yaml
import threading
import logging

# Logger setup for debugging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)


class ConfigurationLoader:
    """
    Class to handle configuration loading from a YAML file.
    """

    def __init__(self, config_file):
        self.config_file = Path(config_file)
        self.config = None
        self.image_folder = None
        self.load_config()

    def load_config(self):
        """
        Load and validate the configuration file.
        """
        if not self.config_file.exists():
            logging.error(f"Configuration file not found: {self.config_file}")
            messagebox.showerror("Error", f"Configuration file not found: {self.config_file}")
            exit()

        try:
            with open(self.config_file, "r") as f:
                self.config = yaml.safe_load(f)

            self.image_folder = Path(self.config.get("IMAGE_FOLDER", ""))
            if not self.image_folder.exists():
                raise ValueError(f"Invalid or missing 'IMAGE_FOLDER' in {self.config_file}")

            logging.info(f"Configuration loaded successfully. Image folder: {self.image_folder}")

        except Exception as e:
            logging.error(f"Failed to load configuration file: {e}")
            messagebox.showerror("Error", f"Failed to load configuration file: {e}")
            exit()


class CernoIDApp:
    """
    Main application class for the CernoID GUI.
    """

    def __init__(self, root, image_folder):
        self.root = root
        self.image_folder = image_folder

        # Application setup
        self.root.title("CernoID - Face Recognition System")
        self.root.geometry("600x400")
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)

        # Create UI components
        self.create_widgets()

    def create_widgets(self):
        """
        Create the UI components for the application.
        """
        # Heading
        tk.Label(self.root, text="CernoID - Face Recognition", font=("Arial", 16, "bold")).pack(pady=10)

        # Instruction Label
        tk.Label(self.root, text=f"Images will be processed from: {self.image_folder}", font=("Arial", 12)).pack(pady=5)

        # Buttons for each functionality
        buttons = [
            {"text": "Detect Faces", "command": self.threaded(self.detect_faces)},
            {"text": "Encode Faces", "command": self.threaded(self.encode_faces)},
            {"text": "Match Faces", "command": self.threaded(self.match_faces)},
        ]

        for btn in buttons:
            tk.Button(self.root, text=btn["text"], command=btn["command"], width=20).pack(pady=10)

        # Exit Button
        tk.Button(self.root, text="Exit", command=self.on_exit, width=20).pack(pady=20)

    def threaded(self, func):
        """
        Create thread to execute a function.
        """
        return lambda: threading.Thread(target=func, daemon=True).start()

    def detect_faces(self):
        """
        Logic for detecting faces in images.
        """
        try:
            logging.info("Starting face detection...")
            detect_faces(str(self.image_folder))  # Assuming this function is implemented elsewhere
            messagebox.showinfo("Success", "Face detection completed successfully!")
            logging.info("Face detection completed.")
        except Exception as e:
            logging.error(f"Face detection failed: {e}")
            messagebox.showerror("Error", f"Face detection failed: {e}")

    def encode_faces(self):
        """
        Logic for encoding faces for recognition.
        """
        try:
            logging.info("Starting face encoding...")
            encode_faces(str(self.image_folder))  # Assuming this function is implemented elsewhere
            messagebox.showinfo("Success", "Face encoding completed successfully!")
            logging.info("Face encoding completed.")
        except Exception as e:
            logging.error(f"Face encoding failed: {e}")
            messagebox.showerror("Error", f"Face encoding failed: {e}")

    def match_faces(self):
        """
        Logic for matching faces to encoded data.
        """
        try:
            logging.info("Starting face matching...")
            match_faces()  # Assuming this function is implemented elsewhere
            messagebox.showinfo("Success", "Face matching completed successfully!")
            logging.info("Face matching completed.")
        except Exception as e:
            logging.error(f"Face matching failed: {e}")
            messagebox.showerror("Error", f"Face matching failed: {e}")

    def on_exit(self):
        """
        Exit the application safely.
        """
        logging.info("Exiting application.")
        self.root.quit()


if __name__ == "__main__":
    # Load configuration
    CONFIG_FILE = "config/config.yaml"
    config_loader = ConfigurationLoader(CONFIG_FILE)

    # Start the application
    root = tk.Tk()
    app = CernoIDApp(root, config_loader.image_folder)
    root.mainloop()

