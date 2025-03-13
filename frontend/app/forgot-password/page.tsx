'use client';

// Remove or comment out the 'use client' directive if it exists
// export const metadata: Metadata = {
//   title: 'Forgot Password - CernoID Security',
//   description: 'Reset your password for CernoID Security System',
// };

// Force dynamic rendering
export const dynamic = 'force-dynamic';
export const revalidate = 0;

import React, { useState, useEffect } from 'react';
import { Box, Container, Paper, Typography, useTheme } from '@mui/material';
import { ForgotPassword } from '@/components/Auth/ForgotPassword';
import { TopBar } from '@/components/Navigation/TopBar';
import { motion } from 'framer-motion';

const MotionPaper = motion(Paper);
const MotionBox = motion(Box);

export default function ForgotPasswordPage() {
  const theme = useTheme();
  const [isDarkMode, setIsDarkMode] = useState(theme.palette.mode === 'dark');

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      setIsDarkMode(savedTheme === 'dark');
    }
  }, []);

  const toggleTheme = () => {
    const newTheme = isDarkMode ? 'light' : 'dark';
    setIsDarkMode(!isDarkMode);
    localStorage.setItem('theme', newTheme);
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: isDarkMode ? 'background.default' : 'grey.50',
      }}
    >
      <TopBar onThemeToggle={toggleTheme} isDarkMode={isDarkMode} />
      <Container maxWidth="sm" sx={{ mt: 8, mb: 4 }}>
        <MotionPaper
          elevation={3}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          sx={{
            p: 4,
            borderRadius: 2,
            bgcolor: isDarkMode ? 'background.paper' : 'white',
            boxShadow: isDarkMode
              ? '0 8px 32px rgba(0, 0, 0, 0.3)'
              : '0 8px 32px rgba(0, 0, 0, 0.1)',
          }}
        >
          <ForgotPassword />
        </MotionPaper>
      </Container>
    </Box>
  );
} 