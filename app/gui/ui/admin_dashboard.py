import tkinter as tk
from tkinter import ttk, messagebox
from database.database import Database


class AdminDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Admin Dashboard - CernoID")
        self.root.geometry("800x600")  # Set dashboard window size
        self.db = Database()

        self.build_ui()

    def build_ui(self):
        # Create Navigation Tabs
        tab_control = ttk.Notebook(self.root)
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

        # Refresh Button
        refresh_button = tk.Button(self.user_tab, text="Refresh", command=self.refresh_user_table)
        refresh_button.pack(pady=5)

        # Add User Button
        add_user_button = tk.Button(self.user_tab, text="Add User", command=self.add_user)
        add_user_button.pack(pady=5)

        # Load User Data on Initialization
        self.refresh_user_table()

    def refresh_user_table(self):
        """
        Refresh the user table by fetching data from the database.
        """
        for row in self.user_table.get_children():
            self.user_table.delete(row)

        users = self.db.connect().cursor().execute("SELECT id, username, role FROM users").fetchall()
        for user in users:
            self.user_table.insert("", "end", values=user)

    def add_user(self):
        """
        Add a new user via a popup window.
        """
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
            username = username_entry.get()
            password = password_entry.get()
            role = role_dropdown.get()

            if not username or not password:
                messagebox.showerror("Error", "Username and Password cannot be empty!")
                return

            # Add new user to the database
            self.db.insert_user(username, password, role)
            messagebox.showinfo("Success", "User added successfully!")
            self.refresh_user_table()
            add_window.destroy()

        save_button = tk.Button(add_window, text="Save", command=save_user)
        save_button.pack(pady=20)

    # Role Management Tab
   def build_role_management_tab(self):
    tk.Label(self.role_tab, text="Role Management", font=("Arial", 16)).pack(pady=10)

    # Role Table
    self.role_table = ttk.Treeview(self.role_tab, columns=("Role", "Permissions"), show="headings")
    self.role_table.heading("Role", text="Role")
    self.role_table.heading("Permissions", text="Permissions")
    self.role_table.pack(pady=20, fill=tk.BOTH, expand=1)

    # Add, Modify, Delete Buttons
    button_frame = tk.Frame(self.role_tab)
    button_frame.pack(pady=10)

    add_role_button = tk.Button(button_frame, text="Add Role", command=self.add_role)
    add_role_button.grid(row=0, column=0, padx=10)

    modify_role_button = tk.Button(button_frame, text="Modify Role", command=self.modify_role)
    modify_role_button.grid(row=0, column=1, padx=10)

    delete_role_button = tk.Button(button_frame, text="Delete Role", command=self.delete_role)
    delete_role_button.grid(row=0, column=2, padx=10)

    # Load roles and permissions
    self.refresh_role_table()


def refresh_role_table(self):
    """
    Refresh the role table by fetching data from the database.
    """
    for row in self.role_table.get_children():
        self.role_table.delete(row)

    roles_data = self.db.connect().cursor().execute(
        "SELECT role, GROUP_CONCAT(permission, ', ') AS permissions FROM roles_permissions GROUP BY role"
    ).fetchall()

    for role, permissions in roles_data:
        self.role_table.insert("", "end", values=(role, permissions if permissions else "None"))


def add_role(self):
    """
    Add a new role via a popup window.
    """
    add_window = tk.Toplevel(self.role_tab)
    add_window.title("Add Role")
    add_window.geometry("300x200")

    tk.Label(add_window, text="Role Name:").pack(pady=5)
    role_entry = tk.Entry(add_window)
    role_entry.pack(pady=5)

    tk.Label(add_window, text="Permissions (comma-separated):").pack(pady=5)
    permissions_entry = tk.Entry(add_window)
    permissions_entry.pack(pady=5)

    def save_role():
        role_name = role_entry.get().strip()
        permissions = [perm.strip() for perm in permissions_entry.get().split(",")]

        if not role_name:
            messagebox.showerror("Error", "Role name cannot be empty!")
            return

        # Insert role and permissions into the database
        for permission in permissions:
            if permission:
                self.db.connect().cursor().execute(
                    "INSERT INTO roles_permissions (role, permission) VALUES (?, ?)", (role_name, permission)
                )
        self.db.connect().commit()
        messagebox.showinfo("Success", f"Role '{role_name}' added successfully!")
        self.refresh_role_table()
        add_window.destroy()

    save_button = tk.Button(add_window, text="Save", command=save_role)
    save_button.pack(pady=20)


def modify_role(self):
    """
    Open a popup window to add/remove permissions for a selected role.
    """
    selected_item = self.role_table.selection()
    if not selected_item:
        messagebox.showerror("Error", "No role selected!")
        return

    selected_role = self.role_table.item(selected_item, "values")[0]

    modify_window = tk.Toplevel(self.role_tab)
    modify_window.title(f"Modify Role: {selected_role}")
    modify_window.geometry("400x300")

    tk.Label(modify_window, text="Current Permissions:").pack(pady=5)
    current_permissions = self.db.connect().cursor().execute(
        "SELECT permission FROM roles_permissions WHERE role = ?", (selected_role,)
    ).fetchall()

    current_permissions = [perm[0] for perm in current_permissions]
    permissions_list = tk.Listbox(modify_window, selectmode=tk.MULTIPLE)
    for permission in current_permissions:
        permissions_list.insert(tk.END, permission)
    permissions_list.pack(pady=5)

    tk.Label(modify_window, text="Add New Permissions (comma-separated):").pack(pady=5)
    new_permissions_entry = tk.Entry(modify_window)
    new_permissions_entry.pack(pady=5)

    def save_modifications():
        # Remove selected permissions
        selected_to_remove = [permissions_list.get(i) for i in permissions_list.curselection()]
        for permission in selected_to_remove:
            self.db.connect().cursor().execute(
                "DELETE FROM roles_permissions WHERE role = ? AND permission = ?", (selected_role, permission)
            )

        # Add new permissions
        new_permissions = [perm.strip() for perm in new_permissions_entry.get().split(",")]
        for permission in new_permissions:
            if permission:
                self.db.connect().cursor().execute(
                    "INSERT INTO roles_permissions (role, permission) VALUES (?, ?)", (selected_role, permission)
                )

        self.db.connect().commit()
        messagebox.showinfo("Success", f"Permissions for role '{selected_role}' updated successfully!")
        self.refresh_role_table()
        modify_window.destroy()

    save_button = tk.Button(modify_window, text="Save Changes", command=save_modifications)
    save_button.pack(pady=20)


def delete_role(self):
    """
    Delete a role after confirmation.
    """
    selected_item = self.role_table.selection()
    if not selected_item:
        messagebox.showerror("Error", "No role selected!")
        return

    selected_role = self.role_table.item(selected_item, "values")[0]

    if selected_role == "admin":
        messagebox.showerror("Error", "Cannot delete the 'admin' role!")
        return

    confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the role '{selected_role}'?")
    if confirm:
        self.db.connect().cursor().execute("DELETE FROM roles_permissions WHERE role = ?", (selected_role,))
        self.db.connect().commit()
        messagebox.showinfo("Success", f"Role '{selected_role}' deleted successfully!")
        self.refresh_role_table()


    # Audit Logs Tab
    def build_audit_logs_tab(self):
        tk.Label(self.audit_tab, text="Audit Logs", font=("Arial", 16)).pack(pady=10)

        # Audit Table
        self.audit_table = ttk.Treeview(self.audit_tab, columns=("Timestamp", "Event", "Details"), show="headings")
        self.audit_table.heading("Timestamp", text="Timestamp")
        self.audit_table.heading("Event", text="Event")
        self.audit_table.heading("Details", text="Details")
        self.audit_table.pack(pady=20, fill=tk.BOTH, expand=1)

        # Placeholder Button to Load Logs
        load_logs_button = tk.Button(self.audit_tab, text="Load Logs", command=self.load_audit_logs)
        load_logs_button.pack(pady=5)

    def load_audit_logs(self):
        """
        Load audit logs from the database or log file.
        """
        messagebox.showinfo("Feature", "Loading logs... (Feature under development!)")

    # System Configuration Tab
    def build_system_config_tab(self):
        tk.Label(self.config_tab, text="System Configuration", font=("Arial", 16)).pack(pady=10)
        tk.Label(self.config_tab, text="(Under Development)").pack(pady=20)


if __name__ == "__main__":
    root = tk.Tk()
    dashboard = AdminDashboard(root)
    root.mainloop()
