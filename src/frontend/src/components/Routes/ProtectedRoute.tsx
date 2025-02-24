import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { CircularProgress, Box } from '@mui/material';
import { useApp } from '../../context/AppContext';

interface ProtectedRouteProps {
    children: React.ReactNode;
    requiredRole?: string;
    requiredPermissions?: string[];
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
    children,
    requiredRole,
    requiredPermissions
}) => {
    const { user, isInitialized } = useApp();
    const location = useLocation();

    // Show loading while checking authentication
    if (!isInitialized) {
        return (
            <Box 
                sx={{ 
                    display: 'flex', 
                    justifyContent: 'center', 
                    alignItems: 'center',
                    height: '100vh' 
                }}
            >
                <CircularProgress />
            </Box>
        );
    }

    // Redirect to login if not authenticated
    if (!user) {
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    // Check role requirement
    if (requiredRole && user.role !== requiredRole) {
        return <Navigate to="/unauthorized" replace />;
    }

    // Check permissions requirement
    if (requiredPermissions) {
        const hasRequiredPermissions = requiredPermissions.every(
            permission => user.permissions.includes(permission)
        );
        if (!hasRequiredPermissions) {
            return <Navigate to="/unauthorized" replace />;
        }
    }

    return <>{children}</>;
}; 