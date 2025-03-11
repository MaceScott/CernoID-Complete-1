'use client';

import React, { useEffect } from 'react';
import { Box, CircularProgress } from '@mui/material';
import { MultiCameraClient } from '../components/features/cameras/MultiCameraClient';
import { useAuth } from '../hooks/useAuth';
import { useRouter } from 'next/navigation';

export default function CamerasPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [user, isLoading, router]);

  if (isLoading || !user) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  return <MultiCameraClient />;
} 