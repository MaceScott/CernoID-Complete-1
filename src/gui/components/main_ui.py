import tkinter as tk
from tkinter import ttk
from camera_recognition import CameraRecognition
from multi_cam import MultiCameraMonitor
from admin import AdminPage
from individual_id import IndividualIdentificationPage


class MainUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CERNO ID - Facial Recognition System")
        self.root.geometry("1000x700")
        self.current_frame = None

        self.build_header()
        self.build_side_panel()
        self.switch_to_camera_page()  # Default page

    def build_header(self):
        # Top header panel with branding
        header = tk.Frame(self.root, height=50, bg="black")
        header.pack(side="top", fill="x")
        label = tk.Label(header, text="CERNO ID", font=("Arial", 20, "bold"), fg="white", bg="black")
        label.pack(pady=10)

    def build_side_panel(self):
        # Navigation side panel
        side_panel = tk.Frame(self.root, width=200, bg="grey")
        side_panel.pack(side="left", fill="y")

        # Buttons for core modules
        tk.Button(side_panel, text="Dashboard", command=self.switch_to_camera_page).pack(pady=10)
        tk.Button(side_panel, text="Admin Page", command=self.switch_to_admin_page).pack(pady=10)
        tk.Button(side_panel, text="Multi-Camera Monitoring", command=self.switch_to_multi_camera_page).pack(pady=10)
        tk.Button(side_panel, text="Individual Identification", command=self.switch_to_individual_id_page).pack(pady=10)

    def switch_frame(self, new_frame):
        # Clear current frame
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = new_frame
        self.current_frame.pack(fill="both", expand=True)

    def switch_to_camera_page(self):
        # Switch to real-time camera feed
        frame = tk.Frame(self.root)
        CameraRecognition(frame).start()
        self.switch_frame(frame)

    def switch_to_admin_page(self):
        # Switch to admin management page
        frame = AdminPage(self.root)
        self.switch_frame(frame)

    def switch_to_multi_camera_page(self):
        # Switch to multi-camera monitor
        frame = tk.Frame(self.root)
        MultiCameraMonitor(frame).start()
        self.switch_frame(frame)

    def switch_to_individual_id_page(self):
        # Switch to individual identification page
        frame = IndividualIdentificationPage(self.root)
        self.switch_frame(frame)


if __name__ == "__main__":
    root = tk.Tk()
    app = MainUI(root)
    root.mainloop()
