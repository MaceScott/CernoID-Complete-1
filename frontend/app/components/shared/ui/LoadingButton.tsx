'use client';

import React from 'react';
import { Box, CircularProgress } from '@mui/material';

interface LoadingButtonContentProps {
    loading: boolean;
    children: React.ReactNode;
    size?: number;
}

export const LoadingButtonContent: React.FC<LoadingButtonContentProps> = ({
    loading,
    children,
    size = 20
}) => {
    return (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {loading && <CircularProgress size={size} color="inherit" />}
            {children}
        </Box>
    );
}; 