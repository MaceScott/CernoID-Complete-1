import { createTheme, alpha } from '@mui/material/styles';

// Define custom color palette
const primaryColor = '#1976d2';
const secondaryColor = '#9c27b0';

// Create base theme configuration
export const createAppTheme = (mode: 'light' | 'dark') => createTheme({
    palette: {
        mode,
        primary: {
            main: primaryColor,
            light: alpha(primaryColor, 0.8),
            dark: alpha(primaryColor, 1.2),
            contrastText: '#ffffff'
        },
        secondary: {
            main: secondaryColor,
            light: alpha(secondaryColor, 0.8),
            dark: alpha(secondaryColor, 1.2),
            contrastText: '#ffffff'
        },
        background: {
            default: mode === 'light' ? '#f5f5f5' : '#121212',
            paper: mode === 'light' ? '#ffffff' : '#1e1e1e'
        }
    },
    typography: {
        fontFamily: [
            'Inter',
            '-apple-system',
            'BlinkMacSystemFont',
            '"Segoe UI"',
            'Roboto',
            'Arial',
            'sans-serif'
        ].join(','),
        h1: {
            fontSize: '2.5rem',
            fontWeight: 600
        },
        h2: {
            fontSize: '2rem',
            fontWeight: 600
        },
        h3: {
            fontSize: '1.75rem',
            fontWeight: 600
        },
        h4: {
            fontSize: '1.5rem',
            fontWeight: 500
        },
        h5: {
            fontSize: '1.25rem',
            fontWeight: 500
        },
        h6: {
            fontSize: '1rem',
            fontWeight: 500
        }
    },
    components: {
        MuiButton: {
            styleOverrides: {
                root: {
                    textTransform: 'none',
                    borderRadius: 8,
                    padding: '8px 16px',
                    fontWeight: 500
                },
                contained: {
                    boxShadow: 'none',
                    '&:hover': {
                        boxShadow: 'none'
                    }
                }
            }
        },
        MuiPaper: {
            styleOverrides: {
                root: {
                    borderRadius: 12,
                    boxShadow: mode === 'light' 
                        ? '0 2px 12px rgba(0,0,0,0.08)'
                        : '0 2px 12px rgba(0,0,0,0.3)'
                }
            }
        },
        MuiCard: {
            styleOverrides: {
                root: {
                    borderRadius: 12,
                    boxShadow: mode === 'light'
                        ? '0 2px 12px rgba(0,0,0,0.08)'
                        : '0 2px 12px rgba(0,0,0,0.3)'
                }
            }
        },
        MuiTextField: {
            styleOverrides: {
                root: {
                    '& .MuiOutlinedInput-root': {
                        borderRadius: 8
                    }
                }
            }
        },
        MuiAppBar: {
            styleOverrides: {
                root: {
                    boxShadow: 'none',
                    borderBottom: `1px solid ${
                        mode === 'light' ? '#e0e0e0' : '#333333'
                    }`
                }
            }
        }
    },
    shape: {
        borderRadius: 8
    }
});

// Export default light theme
export const theme = createAppTheme('light'); 