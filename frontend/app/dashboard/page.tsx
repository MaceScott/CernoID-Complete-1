'use client';

import React from 'react';
import { Box, CircularProgress } from '@mui/material';
import { DashboardClient } from '@/components/features/dashboard/DashboardClient';
import { useAuth } from '@/hooks/useAuth';

export default function DashboardPage() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
          bgcolor: 'background.default',
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  // No need to check for !user here as middleware handles the redirect
  return <DashboardClient />;
} 