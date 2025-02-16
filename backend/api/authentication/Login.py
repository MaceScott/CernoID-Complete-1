import tkinter as tk
from tkinter import messagebox
import threading
import hashlib
import cv2
import numpy as np
from face_recognition import face_encodings, compare_faces
from database.database import Database
from bcrypt import gensalt, hashpw, checkpw  # For secure password hashing


class LoginScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("CernoID Login")
        self.root.geometry("400x300")
        self.db = Database()  # Database connection
        self.camera_thread = None
        self.build_ui()

    def build_ui(self):
        """
        Build the main user interface for selecting login options.
        """
        tk.Label(self.root, text="Welcome to CernoID", font=("Arial", 16)).pack(pady=20)

        tk.Label(self.root, text="Login Options").pack(pady=10)
        tk.Button(self.root, text="Facial Recognition Login", command=self.start_face_login).pack(pady=10)
        tk.Button(self.root, text="Manual Login", command=self.manual_login).pack(pady=10)

    def start_face_login(self):
        """
        Start facial recognition login in a separate thread to avoid blocking the UI.
        """
        if not self.camera_thread or not self.camera_thread.is_alive():
            self.camera_thread = threading.Thread(target=self.face_login, daemon=True)
            self.camera_thread.start()

    def face_login(self):
        """
        Facial recognition-based authentication.
        """
        try:
            capture = cv2.VideoCapture(0)
            if not capture.isOpened():
                messagebox.showerror("Error", "Unable to access the camera!")
                return

            while True:
                ret, frame = capture.read()
                if not ret:
                    break

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                detected_encodings = face_encodings(rgb_frame)

                if detected_encodings:  # If faces are detected
                    for user_id, username, saved_encoding in self.db.fetch_all_encodings():
                        known_encoding = np.frombuffer(saved_encoding, dtype=np.float64)
                        if compare_faces([known_encoding], detected_encodings[0], tolerance=0.6)[0]:
                            self.shutdown_camera(capture)
                            self.on_login_success(username)
                            return

                # Display the camera feed
                cv2.imshow("Facial Login - CernoID", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):  # Exit on 'q'
                    break

            # If no face match, trigger login failure
            self.shutdown_camera(capture)
            self.on_login_failure()

        except Exception as e:
            self.shutdown_camera(None)
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    @staticmethod
    def shutdown_camera(capture):
        """
        Release the camera and close OpenCV windows.
        """
        if capture:
            capture.release()
        cv2.destroyAllWindows()

    def manual_login(self):
        """
        Manual login using username and password with a modal window.
        """
        manual_window = tk.Toplevel(self.root)
        manual_window.title("Manual Login")
        manual_window.geometry("300x200")
        manual_window.grab_set()  # Make the window modal

        tk.Label(manual_window, text="Username").pack(pady=5)
        username_entry = tk.Entry(manual_window)
        username_entry.pack(pady=5)

        tk.Label(manual_window, text="Password").pack(pady=5)
        password_entry = tk.Entry(manual_window, show="*")
        password_entry.pack(pady=5)

        tk.Button(
            manual_window,
            text="Login",
            command=lambda: self.check_manual_login(
                username_entry.get(), password_entry.get(), manual_window
            ),
        ).pack(pady=10)

    def check_manual_login(self, username, password, window):
        """
        Authenticate using username and password.
        """
        try:
            user = self.db.fetch_user_by_username(username)
            if user:
                # Check password hashes
                stored_hashed_password = user[2]
                if checkpw(password.encode(), stored_hashed_password.encode()):
                    window.destroy()
                    self.on_login_success(username)
                    return

            # If authentication fails
            messagebox.showerror("Error", "Invalid username or password!")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def on_login_success(self, username):
        """
        Handle successful login and redirect users based on their roles.
        """
        user = self.db.fetch_user_by_username(username)
        role = user[3]  # Assuming roles are stored in the 4th column
        messagebox.showinfo("Success", f"Welcome, {username}!\nRole: {role}")

        # Redirect based on role
        if role == "admin":
            self.redirect_to_admin_dashboard()
        elif role == "security":
            self.redirect_to_security_dashboard()
        else:
            self.redirect_to_user_dashboard()

    def on_login_failure(self):
        """
        Handle a failed login attempt.
        """
        messagebox.showerror("Error", "Login failed. Please try again!")

    def redirect_to_admin_dashboard(self):
        """
        Redirect to the admin dashboard.
        """
        messagebox.showinfo("Redirect", "Redirecting to admin dashboard...")

    def redirect_to_security_dashboard(self):
        """
        Redirect to the security dashboard.
        """
        messagebox.showinfo("Redirect", "Redirecting to security dashboard...")

    def redirect_to_user_dashboard(self):
        """
        Redirect to the user dashboard.
        """
        messagebox.showinfo("Redirect", "Redirecting to user dashboard...")

