import tkinter as tk
from tkinter import messagebox
import threading
import cv2
import numpy as np
from face_recognition import face_encodings, compare_faces
from database.database import Database
from bcrypt import hashpw, checkpw


class LoginScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("CernoID Login")
        self.root.geometry("400x300")
        self.db = Database()  # Database connection instance
        self.camera_thread = None  # Thread for running camera processes
        self.build_ui()

    def build_ui(self):
        """
        Build the main UI layout for the login screen.
        """
        tk.Label(self.root, text="Welcome to CernoID", font=("Arial", 16, "bold")).pack(pady=20)

        tk.Label(self.root, text="Login Options").pack(pady=10)

        tk.Button(self.root, text="Facial Recognition Login", command=self.start_face_login).pack(pady=10)
        tk.Button(self.root, text="Manual Login", command=self.manual_login).pack(pady=10)

    def start_face_login(self):
        """
        Launch facial recognition login in a separate thread.
        """
        if not self.camera_thread or not self.camera_thread.is_alive():
            self.camera_thread = threading.Thread(target=self.face_login, daemon=True)
            self.camera_thread.start()

    def face_login(self):
        """
        Perform facial recognition-based authentication.
        """
        try:
            capture = cv2.VideoCapture(0)  # Open the camera
            if not capture.isOpened():
                messagebox.showerror("Error", "Unable to access the camera.")
                return

            while True:
                ret, frame = capture.read()
                if not ret:  # If the frame is invalid, exit the loop.
                    break

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                detected_encodings = face_encodings(rgb_frame)

                if detected_encodings:  # If a face is detected in the frame
                    with self.db.connect() as conn:
                        cursor = conn.cursor()
                        users = self.db.fetch_all_encodings(cursor)  # Placeholder for fetching users from DB
                        for user_id, username, saved_encoding in users:
                            known_encoding = np.frombuffer(saved_encoding, dtype=np.float64)
                            if compare_faces([known_encoding], detected_encodings[0], tolerance=0.6)[0]:
                                self.shutdown_camera(capture)
                                self.on_login_success(username)
                                return

                cv2.imshow("Facial Login - CernoID", frame)  # Display the camera feed
                if cv2.waitKey(1) & 0xFF == ord("q"):  # Exit on 'q'
                    break

            # If no match is found, login fails
            self.shutdown_camera(capture)
            self.on_login_failure()

        except Exception as e:
            self.shutdown_camera(None)
            messagebox.showerror("Error", f"Unexpected error during facial login: {e}")

    @staticmethod
    def shutdown_camera(capture):
        """
        Safely release the camera and close OpenCV windows.
        """
        if capture:
            capture.release()
        cv2.destroyAllWindows()

    def manual_login(self):
        """
        Open a popup window for manual login using username and password.
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
        Authenticate a user using username and password.
        """
        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()
                user = self.db.fetch_user_by_username(cursor, username)  # Placeholder function fetching user data
                if user:
                    stored_hashed_password = user[2]  # Assuming 3rd field is the hashed password
                    if checkpw(password.encode(), stored_hashed_password.encode()):
                        window.destroy()
                        self.on_login_success(username)
                        return

            messagebox.showerror("Error", "Invalid username or password.")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def on_login_success(self, username):
        """
        Handle actions after login success.
        """
        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()
                user = self.db.fetch_user_by_username(cursor, username)
                role = user[3]  # Assuming 4th column stores the user's role

                messagebox.showinfo("Success", f"Welcome, {username}!\nRole: {role}")

                # Redirect based on the user's role
                if role == "admin":
                    self.redirect_to_admin_dashboard()
                elif role == "security":
                    self.redirect_to_security_dashboard()
                else:
                    self.redirect_to_user_dashboard()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while processing login: {e}")

    def on_login_failure(self):
        """
        Handle actions after login failure.
        """
        messagebox.showerror("Error", "Login failed. Please try again.")

    def redirect_to_admin_dashboard(self):
        """
        Redirect user to admin dashboard.
        """
        messagebox.showinfo("Redirect", "Redirecting to admin dashboard...")

    def redirect_to_security_dashboard(self):
        """
        Redirect user to security dashboard.
        """
        messagebox.showinfo("Redirect", "Redirecting to security dashboard...")

    def redirect_to_user_dashboard(self):
        """
        Redirect user to general user dashboard.
        """
        messagebox.showinfo("Redirect", "Redirecting to user dashboard...")


if __name__ == "__main__":
    root = tk.Tk()
    app = LoginScreen(root)
    root.mainloop()
