'use client';

import React from 'react';
import { LoginForm } from '@/components/Auth/LoginForm';
import { Container, Box, Typography } from '@mui/material';
import { headers } from 'next/headers';

// Force dynamic rendering
export const dynamic = 'force-dynamic';
export const revalidate = 0;

export default function LoginPage() {
  // Force new headers on each request
  headers();
  
  // Generate a unique key for LoginForm on each render to force remount
  const formKey = React.useMemo(() => Date.now().toString(), []);

  return (
    <>
      {/* Add meta tags to prevent caching */}
      <meta httpEquiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
      <meta httpEquiv="Pragma" content="no-cache" />
      <meta httpEquiv="Expires" content="0" />
      
      <Container maxWidth="sm" sx={{ py: 4 }}>
        <Box sx={{ 
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'flex-start',
          pt: 8
        }}>
          <Box sx={{ mb: 6, textAlign: 'center' }}>
            <Typography 
              variant="h2" 
              component="h1" 
              sx={{ 
                fontWeight: 800,
                color: 'primary.main',
                mb: 2,
                fontSize: { xs: '2.5rem', sm: '3.5rem' }
              }}
            >
              CernoID Security
            </Typography>
            <Typography 
              variant="h5" 
              component="h2" 
              sx={{ 
                color: 'text.secondary',
                fontWeight: 500
              }}
            >
              Enterprise Security Management System
            </Typography>
          </Box>
          
          <LoginForm key={formKey} />
        </Box>
      </Container>
    </>
  );
} 