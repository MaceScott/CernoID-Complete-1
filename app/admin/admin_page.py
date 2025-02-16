import tkinter as tk
from database import Database


class AdminPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.db = Database()
        self.build_ui()

    def build_ui(self):
        tk.Label(self, text="User Management", font=("Arial", 16)).pack(pady=10)

        # Add user fields
        tk.Label(self, text="Name:").pack()
        self.name_entry = tk.Entry(self)
        self.name_entry.pack()

        tk.Button(self, text="Add User", command=self.add_user).pack(pady=10)

        # Display users
        self.refresh_users()

    def add_user(self):
        name = self.name_entry.get()
        if name.strip():
            self.db.insert_encoding(name, b"dummy_encoding")  # Store dummy encodings for now
            self.refresh_users()

    def refresh_users(self):
        for widget in self.winfo_children():
            if isinstance(widget, tk.LabelFrame):
                widget.destroy()

        frame = tk.LabelFrame(self, text="Users")
        frame.pack(pady=10)
        for user in self.db.fetch_all_encodings():
            tk.Label(frame, text=f"{user[0]} - {user[1]}").pack()
