-- USERS TABLE: Stores user details, roles, and face encodings
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,       -- Username for manual login
    password TEXT NOT NULL,              -- Hashed password for security
    role TEXT NOT NULL,                  -- Role (e.g., admin, user, visitor)
    face_encoding BLOB                   -- Facial recognition binary encoding
);

-- ROLES_PERMISSIONS TABLE: Maps roles to permissions
CREATE TABLE IF NOT EXISTS roles_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,                  -- User role (e.g., admin)
    permission TEXT NOT NULL             -- Specific permission (e.g., access_logs)
);

-- INITIAL DATA: Insert default roles and permissions
INSERT INTO roles_permissions (role, permission) VALUES
('admin', 'manage_users'),
('admin', 'access_logs'),
('admin', 'configure_system'),
('security', 'access_video_feed'),
('security', 'view_logs'),
('user', 'view_own_data');