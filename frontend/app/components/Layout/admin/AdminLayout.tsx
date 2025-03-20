'use client';

import React from 'react';
import { Box, Container, useTheme } from '@mui/material';
import { AdminGuard } from '@/components/Auth/guards/AdminGuard';
import { TopBar } from '@/components/Navigation/TopBar';
import { Sidebar } from '@/components/Navigation/Sidebar';

interface AdminLayoutProps {
  children: React.ReactNode;
}

export function AdminLayout({ children }: AdminLayoutProps) {
  const theme = useTheme();
  const [sidebarOpen, setSidebarOpen] = React.useState(true);
  const [isDarkMode, setIsDarkMode] = React.useState(false);

  const handleSidebarToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleThemeToggle = () => {
    setIsDarkMode(!isDarkMode);
  };

  return (
    <AdminGuard>
      <Box sx={{ display: 'flex', minHeight: '100vh' }}>
        <TopBar
          onSidebarToggle={handleSidebarToggle}
          onThemeToggle={handleThemeToggle}
          isDarkMode={isDarkMode}
        />
        <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            p: 3,
            width: { sm: `calc(100% - ${240}px)` },
            ml: { sm: `${240}px` },
            mt: '64px',
            bgcolor: theme.palette.background.default,
          }}
        >
          <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
            {children}
          </Container>
        </Box>
      </Box>
    </AdminGuard>
  );
} 