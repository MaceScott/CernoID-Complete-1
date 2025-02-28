import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import face_recognition
from database import Database


class IndividualRegistrationForm:
    """
    Handles the registration of a new individual by collecting their name,
    date of birth, and face image for encoding.
    """

    def __init__(self, root: tk.Tk, image_path: str):
        """
        Initializes the registration form window.

        :param root: Parent Tk instance.
        :param image_path: Path to the captured face image.
        """
        self.db = Database()
        self.image_path = image_path

        self.window = tk.Toplevel(root)
        self.window.title("Register New Individual")
        self.build_form()

    def build_form(self):
        """
        Constructs the form layout for registering a new individual.
        """
        tk.Label(self.window, text="Register New Individual", font=("Arial", 16)).pack(pady=10)

        # Input: Name
        tk.Label(self.window, text="Name:").pack()
        self.name_entry = tk.Entry(self.window)
        self.name_entry.pack()

        # Input: Date of Birth
        tk.Label(self.window, text="Date of Birth (yyyy-mm-dd):").pack()
        self.dob_entry = tk.Entry(self.window)
        self.dob_entry.pack()

        # Save Button
        save_button = tk.Button(self.window, text="Save", command=self.save_individual)
        save_button.pack(pady=10)

        # Face Image Preview
        self.preview_face()

    def preview_face(self):
        """
        Displays the selected face image in the registration form.
        """
        try:
            captured_image = Image.open(self.image_path)
            face_preview = ImageTk.PhotoImage(image=captured_image)
            label = tk.Label(self.window, image=face_preview)
            label.image = face_preview  # Prevent garbage collection
            label.pack(pady=10)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")
            self.window.destroy()

    def save_individual(self):
        """
        Validates the inputs, processes the face encoding, and saves the individual into the database.
        Provides feedback to the user upon success or failure.
        """
        name = self.name_entry.get().strip()
        dob = self.dob_entry.get().strip()

        # Validate inputs
        if not self.validate_input(name, dob):
            return

        try:
            # Load image and extract face encodings
            image = face_recognition.load_image_file(self.image_path)
            encodings = face_recognition.face_encodings(image)

            if not encodings:
                raise ValueError("No face detected in the image. Please use a valid image.")

            # Save the first detected face encoding
            self.db.insert_encoding(name, encodings[0].tobytes())
            messagebox.showinfo("Success", f"Registered {name} successfully!")
            self.window.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save the individual: {e}")

    def validate_input(self, name: str, dob: str) -> bool:
        """
        Validates the input fields for name and date of birth.

        :param name: User-entered name.
        :param dob: User-entered date of birth.
        :return: True if the inputs are valid, else False.
        """
        if not name:
            messagebox.showwarning("Validation Error", "Name cannot be empty.")
            return False

        if not self.validate_date_format(dob):
            messagebox.showwarning("Validation Error", "Date of Birth must be in the format yyyy-mm-dd.")
            return False

        return True

    @staticmethod
    def validate_date_format(dob: str) -> bool:
        """
        Validates if the provided date string matches the format yyyy-mm-dd.

        :param dob: User-entered date of birth.
        :return: True if valid, else False.
        """
        from datetime import datetime
        try:
            datetime.strptime(dob, "%Y-%m-%d")
            return True
        except ValueError:
            return False

