import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import {
    Box,
    CssBaseline,
    Container,
    ThemeProvider,
    createTheme,
    useMediaQuery
} from '@mui/material';
import { Navigation } from './Navigation';
import { ErrorBoundary } from '../ErrorBoundary/ErrorBoundary';
import { useApp } from '../../context/AppContext';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

export const Layout: React.FC = () => {
    const { theme: themeMode } = useApp();
    const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');
    const [drawerOpen, setDrawerOpen] = useState(false);

    // Create theme based on user preference or system preference
    const theme = React.useMemo(
        () =>
            createTheme({
                palette: {
                    mode: themeMode === 'system' ? 
                        (prefersDarkMode ? 'dark' : 'light') : 
                        themeMode,
                    primary: {
                        main: '#1976d2',
                        light: '#42a5f5',
                        dark: '#1565c0'
                    },
                    secondary: {
                        main: '#9c27b0',
                        light: '#ba68c8',
                        dark: '#7b1fa2'
                    }
                },
                components: {
                    MuiDrawer: {
                        styleOverrides: {
                            paper: {
                                backgroundColor: '#1976d2',
                                color: '#fff'
                            }
                        }
                    }
                }
            }),
        [themeMode, prefersDarkMode]
    );

    return (
        <ThemeProvider theme={theme}>
            <Box sx={{ display: 'flex' }}>
                <CssBaseline />
                
                <Navigation
                    open={drawerOpen}
                    onClose={() => setDrawerOpen(false)}
                    onOpen={() => setDrawerOpen(true)}
                />

                <Box
                    component="main"
                    sx={{
                        flexGrow: 1,
                        height: '100vh',
                        overflow: 'auto',
                        backgroundColor: (theme) =>
                            theme.palette.mode === 'light'
                                ? theme.palette.grey[100]
                                : theme.palette.grey[900]
                    }}
                >
                    {/* Toolbar spacer */}
                    <Box sx={{ height: 64 }} />

                    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
                        <ErrorBoundary>
                            <Outlet />
                        </ErrorBoundary>
                    </Container>
                </Box>

                {/* Toast notifications */}
                <ToastContainer
                    position="top-right"
                    autoClose={5000}
                    hideProgressBar={false}
                    newestOnTop
                    closeOnClick
                    rtl={false}
                    pauseOnFocusLoss
                    draggable
                    pauseOnHover
                    theme={theme.palette.mode}
                />
            </Box>
        </ThemeProvider>
    );
}; 