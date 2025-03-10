'use client';

import React from 'react';
import { Box, Container, Grid, Paper, Typography } from '@mui/material';
import { useAuth } from '@/hooks/useAuth';

export const Dashboard = () => {
  const { user } = useAuth();

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column' }}>
            <Typography component="h1" variant="h4" color="primary" gutterBottom>
              Welcome back, {user?.name || 'User'}
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Here's what's happening in your security system
            </Typography>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column' }}>
            <Typography component="h2" variant="h6" color="primary" gutterBottom>
              Active Zones
            </Typography>
            <Typography component="p" variant="h4">
              {user?.zones?.length || 0}
            </Typography>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column' }}>
            <Typography component="h2" variant="h6" color="primary" gutterBottom>
              Permissions
            </Typography>
            <Typography component="p" variant="h4">
              {user?.permissions?.length || 0}
            </Typography>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column' }}>
            <Typography component="h2" variant="h6" color="primary" gutterBottom>
              Role
            </Typography>
            <Typography component="p" variant="h4">
              {user?.role || 'N/A'}
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
}; 