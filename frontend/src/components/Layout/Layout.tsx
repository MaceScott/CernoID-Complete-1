import React, { useState, useMemo } from 'react';
import { Outlet } from 'react-router-dom';
import {
    AppBar,
    Box,
    CssBaseline,
    Drawer,
    IconButton,
    ThemeProvider,
    Toolbar,
    Typography,
    useMediaQuery,
    createTheme
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import { Navigation } from './Navigation';
import { ErrorBoundary } from '../ErrorBoundary/ErrorBoundary';
import { useApp } from '@/context/AppContext';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

export const Layout: React.FC = () => {
    const { state: { theme: themeMode } } = useApp();
    const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');
    const [drawerOpen, setDrawerOpen] = useState(false);

    const theme = useMemo(
        () =>
            createTheme({
                palette: {
                    mode: themeMode === 'dark' || prefersDarkMode ? 'dark' : 'light',
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

    const handleDrawerToggle = () => {
        setDrawerOpen(!drawerOpen);
    };

    return (
        <ThemeProvider theme={theme}>
            <Box sx={{ display: 'flex' }}>
                <CssBaseline />
                <AppBar position="fixed">
                    <Toolbar>
                        <IconButton
                            color="inherit"
                            aria-label="open drawer"
                            edge="start"
                            onClick={handleDrawerToggle}
                            sx={{ mr: 2 }}
                        >
                            <MenuIcon />
                        </IconButton>
                        <Typography variant="h6" noWrap component="div">
                            CernoID Security
                        </Typography>
                    </Toolbar>
                </AppBar>
                <Drawer
                    variant="temporary"
                    anchor="left"
                    open={drawerOpen}
                    onClose={handleDrawerToggle}
                    ModalProps={{
                        keepMounted: true,
                    }}
                >
                    <Navigation onItemClick={() => setDrawerOpen(false)} />
                </Drawer>
                <Box
                    component="main"
                    sx={{
                        flexGrow: 1,
                        p: 3,
                        width: { sm: `calc(100% - 240px)` }
                    }}
                >
                    <Toolbar />
                    <ErrorBoundary>
                        <Outlet />
                    </ErrorBoundary>
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