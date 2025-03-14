'use client';

import { useContext } from 'react';
import { ThemeContext } from '../theme/ThemeProvider';
import { useMediaQuery } from '@mui/material';

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

export function useThemeMode() {
  const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');
  const { isDarkMode, setIsDarkMode } = useTheme();

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
  };

  return {
    isDarkMode,
    setIsDarkMode,
    toggleTheme,
    prefersDarkMode
  };
} 