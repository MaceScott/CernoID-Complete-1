'use client';

import React from 'react';
import { Box, Container, Grid, Paper, Typography } from '@mui/material';
import { useAuth } from '@/hooks/useAuth';

export const DashboardClient = () => {
  const { user } = useAuth();

  if (!user) {
    return null;
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Welcome, {user.email.split('@')[0]}!
        </Typography>

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                User Information
              </Typography>
              <Typography>Email: {user.email}</Typography>
              <Typography>Role: {user.role}</Typography>
              <Typography>
                Permissions: {user.permissions.join(', ') || 'None'}
              </Typography>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Security Zones
              </Typography>
              {user.zones.length > 0 ? (
                <ul>
                  {user.zones.map((zone, index) => (
                    <li key={index}>{zone}</li>
                  ))}
                </ul>
              ) : (
                <Typography>No zones assigned</Typography>
              )}
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </Container>
  );
}; 