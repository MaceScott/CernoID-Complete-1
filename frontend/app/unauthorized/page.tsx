'use client';

import { Box, Button, Container, Typography } from '@mui/material';
import { Home as HomeIcon, ArrowBack } from '@mui/icons-material';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function UnauthorizedPage() {
  const router = useRouter();

  return (
    <Container maxWidth="md">
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          textAlign: 'center',
          gap: 3,
        }}
      >
        <Typography variant="h1" component="h1" gutterBottom>
          401
        </Typography>
        <Typography variant="h4" component="h2" gutterBottom>
          Unauthorized Access
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          You do not have permission to access this page. Please contact your administrator if you believe this is an error.
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            onClick={() => router.back()}
            variant="outlined"
            startIcon={<ArrowBack />}
            size="large"
          >
            Go Back
          </Button>
          <Button
            component={Link}
            href="/dashboard"
            variant="contained"
            startIcon={<HomeIcon />}
            size="large"
          >
            Dashboard
          </Button>
        </Box>
      </Box>
    </Container>
  );
} 