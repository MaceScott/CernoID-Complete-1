import React, { useEffect, useState } from 'react';
import { Box, Container, useTheme } from '@mui/material';
import { useAuth } from '../hooks/useAuth';
import { useNavigation } from '../hooks/useNavigation';

interface BaseFrameProps {
  children: React.ReactNode;
  title?: string;
}

export const BaseFrame: React.FC<BaseFrameProps> = ({ children, title }) => {
  const theme = useTheme();
  const { isAuthenticated } = useAuth();
  const { navigate } = useNavigation();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check authentication
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    setIsLoading(false);
  }, [isAuthenticated, navigate]);

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