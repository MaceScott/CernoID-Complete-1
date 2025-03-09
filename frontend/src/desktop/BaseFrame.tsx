'use client';

import React, { useEffect, useState } from 'react';
import { Box, Container, useTheme } from '@mui/material';
import { useAuth } from '../hooks/useAuth';
import { useRouter } from 'next/navigation';

interface BaseFrameProps {
  children: React.ReactNode;
  title?: string;
}

export const BaseFrame: React.FC<BaseFrameProps> = ({ children, title }) => {
  const theme = useTheme();
  const { user } = useAuth();
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check authentication
    if (!user) {
      router.push('/login');
      return;
    }
    setIsLoading(false);
  }, [user, router]);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
        bgcolor: theme.palette.background.default
      }}
    >
      {/* Header */}
      <Box
        component="header"
        sx={{
          py: 2,
          px: 3,
          bgcolor: theme.palette.primary.main,
          color: theme.palette.primary.contrastText
        }}
      >
        {title}
      </Box>

      {/* Main content */}
      <Container
        maxWidth={false}
        sx={{
          flex: 1,
          py: 3,
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        {children}
      </Container>

      {/* Footer */}
      <Box
        component="footer"
        sx={{
          py: 2,
          px: 3,
          mt: 'auto',
          bgcolor: theme.palette.grey[100]
        }}
      >
        © {new Date().getFullYear()} CernoID
      </Box>
    </Box>
  );
}; 