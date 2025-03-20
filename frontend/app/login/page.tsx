'use client';

// Remove or comment out the 'use client' directive if it exists
// export const metadata: Metadata = {
//   title: 'Login - CernoID Security',
//   description: 'Login to CernoID Security System',
// };

// Force dynamic rendering
export const dynamic = 'force-dynamic';
export const revalidate = 0;

import React from 'react';
import { Box, Container, Paper } from '@mui/material';
import { LoginForm } from '@/components/Auth';

export default function LoginPage() {
  return (
    <Container component="main" maxWidth="xs">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper
          elevation={3}
          sx={{
            padding: 4,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            width: '100%',
          }}
        >
          <LoginForm />
        </Paper>
      </Box>
    </Container>
  );
} 