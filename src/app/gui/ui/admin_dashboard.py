import tkinter as tk
from tkinter import ttk, messagebox
from database.database import Database
from passlib.hash import bcrypt
import threading


class AdminDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Admin Dashboard - CernoID")
        self.root.geometry("800x600")  # Set dashboard window size
        self.db = Database()

        self.build_ui()

    def build_ui(self):
        """Build the main UI with navigation tabs."""
        tab_control = ttk.Notebook(self.root)

        # Tabs
        self.user_tab = ttk.Frame(tab_control)
        self.role_tab = ttk.Frame(tab_control)
        self.audit_tab = ttk.Frame(tab_control)
        self.config_tab = ttk.Frame(tab_control)

        tab_control.add(self.user_tab, text="User Management")
        tab_control.add(self.role_tab, text="Role Management")
        tab_control.add(self.audit_tab, text="Audit Logs")
        tab_control.add(self.config_tab, text="System Configuration")
        tab_control.pack(expand=1, fill="both")

        # Build UI components for each tab
        self.build_user_management_tab()
        self.build_role_management_tab()
        self.build_audit_logs_tab()
        self.build_system_config_tab()

    # User Management Tab
    def build_user_management_tab(self):
        """Construct the User Management tab."""
        tk.Label(self.user_tab, text="User Management", font=("Arial", 16)).pack(pady=10)

        # User List Table
        self.user_table = ttk.Treeview(self.user_tab, columns=("ID", "Username", "Role"), show="headings")
        self.user_table.heading("ID", text="ID")
        self.user_table.heading("Username", text="Username")
        self.user_table.heading("Role", text="Role")
        self.user_table.column("ID", width=50)
        self.user_table.column("Username", width=200)
        self.user_table.column("Role", width=100)
        self.user_table.pack(pady=20, fill=tk.BOTH, expand=1)

        # Buttons
        refresh_button = tk.Button(self.user_tab, text="Refresh", command=self.refresh_user_table)
        refresh_button.pack(pady=5)

        add_user_button = tk.Button(self.user_tab, text="Add User", command=self.add_user)
        add_user_button.pack(pady=5)

        # Load Data
        self.refresh_user_table()

    def refresh_user_table(self):
        """Refresh the user table by fetching data from the database."""

        def fetch_users():
            try:
                for row in self.user_table.get_children():
                    self.user_table.delete(row)

                with self.db.connect() as conn:
                    cursor = conn.cursor()
                    users = cursor.execute("SELECT id, username, role FROM users").fetchall()
                    for user in users:
                        self.user_table.insert("", "end", values=user)
            except Exception as e:
                messagebox.showerror("Error", f"Could not refresh user table: {str(e)}")

        threading.Thread(target=fetch_users).start()

    def add_user(self):
        """Add a new user via a popup window."""
        add_window = tk.Toplevel(self.user_tab)
        add_window.title("Add User")
        add_window.geometry("300x300")

        tk.Label(add_window, text="Username:").pack(pady=5)
        username_entry = tk.Entry(add_window)
        username_entry.pack(pady=5)

        tk.Label(add_window, text="Password:").pack(pady=5)
        password_entry = tk.Entry(add_window, show="*")
        password_entry.pack(pady=5)

        tk.Label(add_window, text="Role:").pack(pady=5)
        role_dropdown = ttk.Combobox(add_window, values=["admin", "security", "user", "visitor"])
        role_dropdown.pack(pady=5)
        role_dropdown.set("user")

        def save_user():
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            role = role_dropdown.get().strip()

            if not username or not password:
                messagebox.showerror("Error", "Username and Password cannot be empty!")
                return

            try:
                hashed_password = bcrypt.hash(password)
                with self.db.connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                        (username, hashed_password, role)
                    )
                    conn.commit()
                messagebox.showinfo("Success", "User added successfully!")
                self.refresh_user_table()
                add_window.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Could not add user: {str(e)}")

        save_button = tk.Button(add_window, text="Save", command=save_user)
        save_button.pack(pady=20)

    # Role Management Tab
    def build_role_management_tab(self):
        """Construct the Role Management tab."""
        tk.Label(self.role_tab, text="Role Management", font=("Arial", 16)).pack(pady=10)

        # Role Table
        self.role_table = ttk.Treeview(self.role_tab, columns=("Role", "Permissions"), show="headings")
        self.role_table.heading("Role", text="Role")
        self.role_table.heading("Permissions", text="Permissions")
        self.role_table.pack(pady=20, fill=tk.BOTH, expand=1)

        # Buttons
        button_frame = tk.Frame(self.role_tab)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Add Role", command=self.add_role).grid(row=0, column=0, padx=10)
        tk.Button(button_frame, text="Modify Role", command=self.modify_role).grid(row=0, column=1, padx=10)
        tk.Button(button_frame, text="Delete Role", command=self.delete_role).grid(row=0, column=2, padx=10)

        self.refresh_role_table()

    def refresh_role_table(self):
        """Refresh the role table by fetching data from the database."""
        try:
            for row in self.role_table.get_children():
                self.role_table.delete(row)

            with self.db.connect() as conn:
                cursor = conn.cursor()
                roles_data = cursor.execute(
                    "SELECT role, GROUP_CONCAT(permission, ', ') AS permissions FROM roles_permissions GROUP BY role"
                ).fetchall()

                for role, permissions in roles_data:
                    self.role_table.insert("", "end", values=(role, permissions or "None"))
        except Exception as e:
            messagebox.showerror("Error", f"Could not refresh role table: {str(e)}")

    def add_role(self):
        """Add a new role."""
        # Implementation follows similar patterns (error handling, threading, modularity).

    def delete_role(self):
        """Delete a role."""
        # Implementation follows similar patterns.

    def modify_role(self):
        """Modify a role."""
        # Implementation follows similar patterns.

    # Audit Logs Tab
    def build_audit_logs_tab(self):
        tk.Label(self.audit_tab, text="Audit Logs", font=("Arial", 16)).pack(pady=10)
        # Placeholder

    def build_system_config_tab(self):
        tk.Label(self.config_tab, text="System Configuration", font=("Arial", 16)).pack(pady=10)
        tk.Label(self.config_tab, text="(Under Development)").pack(pady=20)


if __name__ == "__main__":
    root = tk.Tk()
    dashboard = AdminDashboard(root)
    root.mainloop()
