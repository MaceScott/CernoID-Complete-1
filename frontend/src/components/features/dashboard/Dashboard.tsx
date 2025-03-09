'use client';

import { Box, Container, Grid, Paper, Typography } from '@mui/material';
import { useAuth } from '@/app/providers/AuthProvider';

export const Dashboard = () => {
  const { user } = useAuth();

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column' }}>
            <Typography component="h1" variant="h4" gutterBottom>
              Welcome, {user?.username}!
            </Typography>
            <Typography variant="body1">
              Access the features using the navigation menu.
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
}; 