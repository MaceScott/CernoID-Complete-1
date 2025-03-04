'use client';

import { Box, CssBaseline } from '@mui/material';
import { useState } from 'react';
import DashboardHeader from '@/components/dashboard/Header';
import DashboardSidebar from '@/components/dashboard/Sidebar';
import { AuthProvider } from '@/providers/AuthProvider';
import { ThemeProvider } from '../../frontend/src/providers/ThemeProvider';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <ThemeProvider>
      <CssBaseline />
      <AuthProvider>
        <Box sx={{ display: 'flex', minHeight: '100vh' }}>
          <DashboardHeader onToggleSidebar={toggleSidebar} />
          <DashboardSidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
          <Box
            component="main"
            sx={{
              flexGrow: 1,
              p: 3,
              pt: 10,
              backgroundColor: 'background.default'
            }}
          >
            {children}
          </Box>
        </Box>
      </AuthProvider>
    </ThemeProvider>
  );
} 