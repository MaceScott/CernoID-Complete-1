import React from 'react';
import {
    Backdrop,
    CircularProgress,
    Typography,
    Box
} from '@mui/material';
import { Theme } from '@mui/material/styles';

interface LoadingOverlayProps {
    open: boolean;
    message?: string;
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
    open,
    message = 'Loading...'
}) => {
    return (
        <Backdrop
            sx={{
                color: '#fff',
                zIndex: (theme: Theme) => theme.zIndex.drawer + 1,
                display: 'flex',
                flexDirection: 'column',
                gap: 2
            }}
            open={open}
        >
            <CircularProgress color="inherit" />
            {message && (
                <Typography variant="body1">
                    {message}
                </Typography>
            )}
        </Backdrop>
    );
};

interface LoadingButtonContentProps {
    loading: boolean;
    children: React.ReactNode;
}

export const LoadingButtonContent: React.FC<LoadingButtonContentProps> = ({
    loading,
    children
}) => {
    return (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {loading && <CircularProgress size={20} color="inherit" />}
            {children}
        </Box>
    );
}; 