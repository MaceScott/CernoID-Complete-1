'use client';

import { Box, CssBaseline } from '@mui/material';
import { useState } from 'react';
import DashboardHeader from '../../components/Dashboard/Header';
import DashboardSidebar from '../../components/Dashboard/Sidebar';
import { AuthProvider } from '../providers/AuthProvider';
import { ThemeProvider } from '../../components/providers/theme-provider';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const toggleSidebar = () => setSidebarOpen(!sidebarOpen);

  return (
    <ThemeProvider>
      <AuthProvider>
        <Box sx={{ display: 'flex', minHeight: '100vh' }}>
          <CssBaseline />
          <DashboardHeader onToggleSidebar={toggleSidebar} />
          <DashboardSidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
          <Box
            component="main"
            sx={{
              flexGrow: 1,
              p: 3,
              width: { sm: `calc(100% - 240px)` }
            }}
          >
            <Box sx={{ minHeight: 64 }} /> {/* Toolbar spacer */}
            {children}
          </Box>
        </Box>
      </AuthProvider>
    </ThemeProvider>
  )
} 