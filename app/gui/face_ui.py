import os
import tkinter as tk
from tkinter import filedialog, messagebox
from face_encoding import encode_faces
from face_matching import match_faces
import threading

# Constants
IMAGE_TYPES = [("Image Files", "*.jpg *.jpeg *.png")]
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")


class FaceUI(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master

        # Set a default size for the window
        self.master.geometry("400x300")
        self.master.title("Face Processing UI")
        self.master.resizable(False, False)  # Disable resizing for consistent layout

        self.create_widgets()

    def create_widgets(self):
        # Header Label
        tk.Label(self, text="Face Processing UI", font=("TkDefaultFont", 16, "bold")).pack(pady=10)

        # Buttons for encoding and matching
        tk.Button(self, text="Encode Face", command=self.initiate_encode_face, width=15).pack(pady=10)
        tk.Button(self, text="Match Faces", command=self.initiate_match_faces, width=15).pack(pady=10)

    def validate_file_path(self, filepath):
        """Validate the selected file path."""
        if not filepath:
            return False

        if not os.path.isfile(filepath):
            messagebox.showerror("Error", "File does not exist. Please select a valid image file.")
            return False

        if not filepath.lower().endswith(IMAGE_EXTENSIONS):
            messagebox.showerror(
                "Error", "Invalid file type. Please select an image file (JPG, PNG)."
            )
            return False

        return True

    def initiate_encode_face(self):
        """Start the encode_face process in a separate thread."""
        filepath = filedialog.askopenfilename(title="Select Image", filetypes=IMAGE_TYPES)
        if self.validate_file_path(filepath):
            threading.Thread(target=self.encode_face, args=(filepath,), daemon=True).start()

    def encode_face(self, filepath):
        """Encode faces from an uploaded image."""
        try:
            encodings = encode_faces(filepath)
            if not encodings:
                messagebox.showinfo("Face Encoding", "No faces detected in the selected image.")
            else:
                messagebox.showinfo("Face Encoding", f"Encoded {len(encodings)} face(s) successfully.")
        except ValueError as ve:
            messagebox.showerror("Error", f"Input error: {ve}")
        except IOError as ioe:
            messagebox.showerror("Error", f"File processing error: {ioe}")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def initiate_match_faces(self):
        """Start the match_faces process in a separate thread."""
        img1_path = filedialog.askopenfilename(title="Select First Image", filetypes=IMAGE_TYPES)
        if not self.validate_file_path(img1_path):
            return

        img2_path = filedialog.askopenfilename(title="Select Second Image", filetypes=IMAGE_TYPES)
        if not self.validate_file_path(img2_path):
            return

        threading.Thread(target=self.match_faces, args=(img1_path, img2_path), daemon=True).start()

    def match_faces(self, img1_path, img2_path):
        """Match two uploaded face images."""
        try:
            match_result = match_faces(img1_path, img2_path)
            if match_result:
                messagebox.showinfo("Face Matching", "Faces match!")
            else:
                messagebox.showinfo("Face Matching", "Faces do not match.")
        except ValueError as ve:
            messagebox.showerror("Error", f"Input error: {ve}")
        except IOError as ioe:
            messagebox.showerror("Error", f"File processing error: {ioe}")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = FaceUI(master=root)
    app.pack(expand=True, fill=tk.BOTH)
    root.mainloop()

