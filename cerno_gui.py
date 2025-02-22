import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import yaml
import threading
import logging
import sys
from app.face_recognition.face_detection import detect_faces
from app.face_recognition.face_encoding import encode_faces
from app.face_recognition.face_matching import match_faces

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
            sys.exit(1)

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
                if not self.config or "IMAGE_FOLDER" not in self.config:
                    raise ValueError("'IMAGE_FOLDER' is not set or invalid in the configuration file")

            self.image_folder = Path(self.config["IMAGE_FOLDER"])
            if not self.image_folder.exists() or not self.image_folder.is_dir():
                raise ValueError(f"'IMAGE_FOLDER' path is invalid or does not exist: {self.image_folder}")

            logging.info(f"Configuration loaded successfully. Image folder: {self.image_folder}")

        except yaml.YAMLError as e:
            logging.error(f"YAML parsing error: {e}", exc_info=True)
            messagebox.showerror("Error", f"Configuration file is invalid: {e}")
            sys.exit(1)
        except Exception as e:
            logging.error(f"Failed to load configuration file: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to load configuration file: {e}")
            sys.exit(1)


class CernoIDApp:
    """
    Main application class for the CernoID GUI.
    """

    def __init__(self, root, image_folder):
        self.root = root
        self.image_folder = image_folder
        self.threads = []

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
        Creates and starts a thread to execute a function.
        """

        def wrapper():
            thread = threading.Thread(target=func, daemon=True)
            # Start the thread and clean up finished threads
            self.threads = [t for t in self.threads if t.is_alive()]
            self.threads.append(thread)
            thread.start()

        return wrapper

    def detect_faces(self):
        """
        Logic for detecting faces in images.
        """
        try:
            logging.info("Starting face detection...")
            self.validate_image_folder()
            detect_faces(str(self.image_folder))
            messagebox.showinfo("Success", "Face detection completed successfully!")
            logging.info("Face detection completed.")
        except ValueError as ve:
            logging.error(f"Validation error: {ve}")
            messagebox.showerror("Error", str(ve))
        except Exception as e:
            logging.error(f"Face detection failed: {e}", exc_info=True)
            messagebox.showerror("Error", f"Face detection failed: {str(e)}")

    def encode_faces(self):
        """
        Logic for encoding faces for recognition.
        """
        try:
            logging.info("Starting face encoding...")
            self.validate_image_folder()
            encode_faces(str(self.image_folder))
            messagebox.showinfo("Success", "Face encoding completed successfully!")
            logging.info("Face encoding completed.")
        except ValueError as ve:
            logging.error(f"Validation error: {ve}")
            messagebox.showerror("Error", str(ve))
        except Exception as e:
            logging.error(f"Face encoding failed: {e}", exc_info=True)
            messagebox.showerror("Error", f"Face encoding failed: {str(e)}")

    def match_faces(self):
        """
        Logic for matching faces to encoded data.
        """
        try:
            logging.info("Starting face matching...")
            image1 = filedialog.askopenfilename(title="Select Image 1")
            image2 = filedialog.askopenfilename(title="Select Image 2")
            if not image1 or not image2:
                raise ValueError("Both images must be selected for face matching.")

            match_faces(image1, image2)
            messagebox.showinfo("Success", "Face matching completed successfully!")
            logging.info("Face matching completed.")
        except ValueError as ve:
            logging.error(f"Validation error: {ve}")
            messagebox.showerror("Error", str(ve))
        except Exception as e:
            logging.error(f"Face matching failed: {e}", exc_info=True)
            messagebox.showerror("Error", f"Face matching failed: {str(e)}")

    def validate_image_folder(self):
        """
        Validates that the image folder contains valid image files.
        """
        valid_extensions = ["*.jpg", "*.jpeg", "*.png"]
        if not any(file for ext in valid_extensions for file in self.image_folder.glob(ext)):
            raise ValueError(f"No images found in folder: {self.image_folder}")

    def on_exit(self):
        """
        Exit the application safely.
        """
        logging.info("Exiting application... Waiting for threads to complete.")
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=5)  # Timeout to prevent indefinite blocking
        self.root.quit()
        logging.info("Application exited safely.")


if __name__ == "__main__":
    # Load configuration
    CONFIG_FILE = sys.argv[1] if len(sys.argv) > 1 else "config/config.yaml"
    config_loader = ConfigurationLoader(CONFIG_FILE)

    # Start the application
    root = tk.Tk()
    app = CernoIDApp(root, config_loader.image_folder)
    root.mainloop()

