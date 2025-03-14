'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  ThemeProvider as MuiThemeProvider,
  createTheme,
  CssBaseline,
  useMediaQuery,
  Theme,
  Components,
  ThemeOptions,
} from '@mui/material';
import { Roboto } from 'next/font/google';

const roboto = Roboto({
  weight: ['300', '400', '500', '700'],
  subsets: ['latin'],
  display: 'swap',
});

// Brand colors
const brandColors = {
  primary: {
    main: '#2563eb', // Blue
    light: '#60a5fa',
    dark: '#1e40af',
    contrastText: '#ffffff',
  },
  secondary: {
    main: '#7c3aed', // Purple
    light: '#a78bfa',
    dark: '#5b21b6',
    contrastText: '#ffffff',
  },
  success: {
    main: '#059669', // Green
    light: '#34d399',
    dark: '#065f46',
    contrastText: '#ffffff',
  },
  warning: {
    main: '#d97706', // Orange
    light: '#fbbf24',
    dark: '#92400e',
    contrastText: '#ffffff',
  },
  error: {
    main: '#dc2626', // Red
    light: '#f87171',
    dark: '#991b1b',
    contrastText: '#ffffff',
  },
  info: {
    main: '#0284c7', // Light Blue
    light: '#38bdf8',
    dark: '#075985',
    contrastText: '#ffffff',
  },
};

// Common theme settings
const commonThemeSettings: ThemeOptions = {
  typography: {
    fontFamily: roboto.style.fontFamily,
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
      lineHeight: 1.2,
      letterSpacing: '-0.01562em',
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 700,
      lineHeight: 1.2,
      letterSpacing: '-0.00833em',
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 600,
      lineHeight: 1.2,
      letterSpacing: '0em',
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 600,
      lineHeight: 1.2,
      letterSpacing: '0.00735em',
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 500,
      lineHeight: 1.2,
      letterSpacing: '0em',
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 500,
      lineHeight: 1.2,
      letterSpacing: '0.0075em',
    },
    subtitle1: {
      fontSize: '1rem',
      fontWeight: 400,
      lineHeight: 1.5,
      letterSpacing: '0.00938em',
    },
    subtitle2: {
      fontSize: '0.875rem',
      fontWeight: 500,
      lineHeight: 1.57,
      letterSpacing: '0.00714em',
    },
    body1: {
      fontSize: '1rem',
      fontWeight: 400,
      lineHeight: 1.5,
      letterSpacing: '0.00938em',
    },
    body2: {
      fontSize: '0.875rem',
      fontWeight: 400,
      lineHeight: 1.43,
      letterSpacing: '0.01071em',
    },
    button: {
      fontSize: '0.875rem',
      fontWeight: 500,
      lineHeight: 1.75,
      letterSpacing: '0.02857em',
      textTransform: 'none' as const,
    },
    caption: {
      fontSize: '0.75rem',
      fontWeight: 400,
      lineHeight: 1.66,
      letterSpacing: '0.03333em',
    },
    overline: {
      fontSize: '0.75rem',
      fontWeight: 600,
      lineHeight: 2.66,
      letterSpacing: '0.08333em',
      textTransform: 'uppercase' as const,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      defaultProps: {
        disableRipple: true,
      },
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 500,
          padding: '8px 16px',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            transform: 'translateY(-1px)',
          },
          variants: [],
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          transition: 'all 0.2s ease-in-out',
        },
        elevation1: {
          boxShadow: '0px 2px 8px rgba(0, 0, 0, 0.1)',
        },
        elevation2: {
          boxShadow: '0px 4px 16px rgba(0, 0, 0, 0.1)',
        },
        elevation3: {
          boxShadow: '0px 8px 24px rgba(0, 0, 0, 0.1)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-1px)',
            },
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            transform: 'translateY(-2px)',
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 8,
        },
      },
    },
  } as Components<Theme>,
};

// Create themes
const lightTheme = createTheme({
  ...commonThemeSettings,
  palette: {
    mode: 'light',
    ...brandColors,
    background: {
      default: '#f8fafc',
      paper: '#ffffff',
    },
    text: {
      primary: '#1e293b',
      secondary: '#64748b',
    },
    divider: 'rgba(0, 0, 0, 0.12)',
  },
});

const darkTheme = createTheme({
  ...commonThemeSettings,
  palette: {
    mode: 'dark',
    ...brandColors,
    background: {
      default: '#0f172a',
      paper: '#1e293b',
    },
    text: {
      primary: '#f1f5f9',
      secondary: '#94a3b8',
    },
    divider: 'rgba(255, 255, 255, 0.12)',
  },
});

// Theme context
interface ThemeContextType {
  isDarkMode: boolean;
  setIsDarkMode: (isDark: boolean) => void;
}

export const ThemeContext = createContext<ThemeContextType>({
  isDarkMode: false,
  setIsDarkMode: () => {},
});

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');
  const [isDarkMode, setIsDarkMode] = useState(prefersDarkMode);

  useEffect(() => {
    // Check if user has a theme preference in localStorage
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      setIsDarkMode(savedTheme === 'dark');
    } else {
      setIsDarkMode(prefersDarkMode);
    }
  }, [prefersDarkMode]);

  useEffect(() => {
    // Save theme preference to localStorage
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
    // Update document class for global styling
    document.documentElement.classList.toggle('dark', isDarkMode);
  }, [isDarkMode]);

  const theme = isDarkMode ? darkTheme : lightTheme;

  return (
    <ThemeContext.Provider value={{ isDarkMode, setIsDarkMode }}>
      <MuiThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </MuiThemeProvider>
    </ThemeContext.Provider>
  );
} 