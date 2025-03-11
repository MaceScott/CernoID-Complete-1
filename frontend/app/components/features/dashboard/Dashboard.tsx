'use client';

import React from 'react';
import { Box, Paper, Typography, Grid } from '@mui/material';
import { useAuth } from '@/hooks/useAuth';

export const Dashboard = () => {
  const { user } = useAuth();

  if (!user) {
    return null;
  }

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column' }}>
            <Typography component="h1" variant="h4" color="primary" gutterBottom>
              Welcome back, {user.email.split('@')[0]}
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Here's what's happening in your security system
            </Typography>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column' }}>
            <Typography component="h2" variant="h6" color="primary" gutterBottom>
              Access Level
            </Typography>
            <Typography variant="body1">
              Role: {user.role}
            </Typography>
            <Typography variant="body1">
              Permissions: {user.permissions.join(', ')}
            </Typography>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column' }}>
            <Typography component="h2" variant="h6" color="primary" gutterBottom>
              Security Zones
            </Typography>
            <Typography variant="body1">
              {user.zones.length > 0 ? (
                <ul>
                  {user.zones.map((zone, index) => (
                    <li key={index}>{zone}</li>
                  ))}
                </ul>
              ) : (
                'No zones assigned'
              )}
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}; 