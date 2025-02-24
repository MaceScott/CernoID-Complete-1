-- ROLES TABLE: Stores predefined roles
CREATE TABLE IF NOT EXISTS Roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT UNIQUE NOT NULL,           -- Predefined role (e.g., admin, user, visitor)
    CONSTRAINT chk_role CHECK (role IN ('admin', 'security', 'user', 'visitor'))
);

-- USERS TABLE: Stores user details, roles, and face encodings
CREATE TABLE IF NOT EXISTS Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,       -- Username for manual login
    hashed_password TEXT NOT NULL,       -- Securely hashed password
    role_id INTEGER NOT NULL,            -- FK to Roles table
    face_encoding BLOB,                  -- Facial recognition binary encoding
    CONSTRAINT fk_role FOREIGN KEY (role_id) REFERENCES Roles (id) ON DELETE CASCADE
);

-- ROLE_PERMISSIONS TABLE: Maps roles to permissions
CREATE TABLE IF NOT EXISTS RolePermissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL,            -- FK to Roles table
    permission TEXT NOT NULL,            -- Specific permission (e.g., access_logs)
    CONSTRAINT chk_permission CHECK (permission IN (
        'manage_users', 'access_logs', 'configure_system', 'access_video_feed', 'view_logs', 'view_own_data'
    )),
    CONSTRAINT fk_role_permission FOREIGN KEY (role_id) REFERENCES Roles (id) ON DELETE CASCADE
);

-- INITIAL DATA: Insert default roles
INSERT INTO Roles (role) VALUES
('admin'),
('security'),
('user'),
('visitor');

-- INITIAL DATA: Insert default role-permission mappings
INSERT INTO RolePermissions (role_id, permission)
VALUES
((SELECT id FROM Roles WHERE role = 'admin'), 'manage_users'),
((SELECT id FROM Roles WHERE role = 'admin'), 'access_logs'),
((SELECT id FROM Roles WHERE role = 'admin'), 'configure_system'),
((SELECT id FROM Roles WHERE role = 'security'), 'access_video_feed'),
((SELECT id FROM Roles WHERE role = 'security'), 'view_logs'),
((SELECT id FROM Roles WHERE role = 'user'), 'view_own_data');

-- INDEXES: Optimize query performance on foreign key and lookup columns
CREATE INDEX idx_users_role_id ON Users (role_id);
CREATE INDEX idx_permissions_role_id ON RolePermissions (role_id);