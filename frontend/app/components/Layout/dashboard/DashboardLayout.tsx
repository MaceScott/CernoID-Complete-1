'use client';

import React, { useState, useEffect } from 'react';
import { Box, useTheme, useMediaQuery, Drawer } from '@mui/material';
import { TopBar, Sidebar } from '@/components/Navigation';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [open, setOpen] = useState(!isMobile);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/auth/login');
    }
  }, [user, isLoading, router]);

  const handleSidebarToggle = () => {
    setOpen(!open);
  };

  const handleThemeToggle = () => {
    setIsDarkMode(!isDarkMode);
  };

  if (isLoading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
        }}
      >
        Loading...
      </Box>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <Drawer
        variant={isMobile ? 'temporary' : 'permanent'}
        open={open}
        onClose={() => setOpen(false)}
      >
        <Sidebar open={open} onClose={() => setOpen(false)} />
      </Drawer>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${240}px)` },
          ml: { sm: open ? `${240}px` : 0 },
          transition: theme.transitions.create('margin', {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
        }}
      >
        <TopBar
          onSidebarToggle={handleSidebarToggle}
          onThemeToggle={handleThemeToggle}
          isDarkMode={isDarkMode}
        />
        {children}
      </Box>
    </Box>
  );
} 