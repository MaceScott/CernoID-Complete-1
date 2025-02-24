import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { ProtectedRoute } from '../components/Routes/ProtectedRoute';
import { Login } from '../components/Auth/Login';
import { Dashboard } from '../components/Dashboard/Dashboard';
import { Recognition } from '../components/Recognition/Recognition';
import { UserManagement } from '../components/Users/UserManagement';
import { Settings } from '../components/Settings/Settings';
import { NotFound } from '../components/Error/NotFound';
import { Unauthorized } from '../components/Error/Unauthorized';

export const AppRoutes: React.FC = () => {
    return (
        <Routes>
            {/* Public routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/unauthorized" element={<Unauthorized />} />

            {/* Protected routes */}
            <Route
                path="/"
                element={
                    <ProtectedRoute>
                        <Layout />
                    </ProtectedRoute>
                }
            >
                <Route index element={<Navigate to="/dashboard" replace />} />
                <Route path="dashboard" element={<Dashboard />} />
                <Route path="recognition" element={<Recognition />} />
                
                {/* Admin-only routes */}
                <Route
                    path="users"
                    element={
                        <ProtectedRoute
                            requiredRole="admin"
                            requiredPermissions={['manage_users']}
                        >
                            <UserManagement />
                        </ProtectedRoute>
                    }
                />
                
                <Route
                    path="settings"
                    element={
                        <ProtectedRoute
                            requiredRole="admin"
                            requiredPermissions={['manage_settings']}
                        >
                            <Settings />
                        </ProtectedRoute>
                    }
                />

                {/* 404 route */}
                <Route path="*" element={<NotFound />} />
            </Route>
        </Routes>
    );
}; 