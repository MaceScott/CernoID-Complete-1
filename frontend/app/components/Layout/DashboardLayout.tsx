'use client';

import React, { useState } from 'react';
import { Box, useTheme } from '@mui/material';
import { TopBar } from '../Navigation/TopBar';
import Sidebar from '../Navigation/Sidebar';
import { useAuth } from '@/hooks/useAuth';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const theme = useTheme();

  const handleSidebarClose = () => {
    setSidebarOpen(false);
  };

  const handleSidebarOpen = () => {
    setSidebarOpen(true);
  };

  const handleThemeToggle = () => {
    setIsDarkMode(!isDarkMode);
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <TopBar
        onSidebarToggle={handleSidebarOpen}
        onThemeToggle={handleThemeToggle}
        isDarkMode={isDarkMode}
      />
      <Sidebar
        open={sidebarOpen}
        onClose={handleSidebarClose}
      />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: '100%',
          minHeight: '100vh',
          backgroundColor: theme.palette.background.default,
        }}
      >
        <Box sx={{ height: 64 }} /> {/* Toolbar spacer */}
        {children}
      </Box>
    </Box>
  );
} 