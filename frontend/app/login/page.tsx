'use client';

import React from 'react';
import { LoginForm } from '@/components/Auth/LoginForm';
import { Container, Box } from '@mui/material';

export default function LoginPage() {
  return (
    <Container maxWidth="sm">
      <Box sx={{ 
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <LoginForm />
      </Box>
    </Container>
  );
} 