'use client';

// Remove or comment out the 'use client' directive if it exists
// export const metadata: Metadata = {
//   title: 'Login - CernoID Security',
//   description: 'Login to CernoID Security System',
// };

// Force dynamic rendering
export const dynamic = 'force-dynamic';
export const revalidate = 0;

import React, { useState, useEffect } from 'react';
import { Box, Container, Paper, Typography, useTheme } from '@mui/material';
import { LoginForm } from '@/components/Auth/LoginForm';
import { TopBar } from '@/components/Navigation/TopBar';
import { Metadata } from 'next';
import { motion } from 'framer-motion';

const MotionPaper = motion(Paper);
const MotionBox = motion(Box);

export default function LoginPage() {
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
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Typography
              variant="h4"
              component="h1"
              sx={{
                mb: 2,
                fontWeight: 600,
                background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                textAlign: 'center',
              }}
            >
              Welcome to CernoID Security
            </Typography>
          </motion.div>
          <LoginForm />
        </MotionPaper>
      </Container>
    </Box>
  );
} 