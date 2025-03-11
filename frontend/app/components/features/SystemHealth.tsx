'use client';

import React, { useState, useEffect } from 'react';
import { Box, Card, CardContent, Typography, Grid, CircularProgress, Alert } from '@mui/material';
import { useAuth } from '@/hooks/useAuth';

interface SystemMetrics {
  cpu: number;
  memory: number;
  disk: number;
  gpu: number;
  temperature: number;
  uptime: string;
  activeUsers: number;
  lastUpdate: string;
}

export default function SystemHealth() {
  const { user } = useAuth();
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/system/metrics`, {
          credentials: 'include',
        });
        
        if (!response.ok) {
          throw new Error('Failed to fetch system metrics');
        }
        
        const data = await response.json();
        setMetrics(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load system metrics');
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!metrics) {
    return (
      <Alert severity="warning" sx={{ mt: 2 }}>
        No system metrics available
      </Alert>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        System Health
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                CPU Usage
              </Typography>
              <Typography variant="h4">
                {metrics.cpu}%
              </Typography>
              <Box sx={{ mt: 2 }}>
                <CircularProgress 
                  variant="determinate" 
                  value={metrics.cpu} 
                  color={metrics.cpu > 80 ? 'error' : metrics.cpu > 60 ? 'warning' : 'success'}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Memory Usage
              </Typography>
              <Typography variant="h4">
                {metrics.memory}%
              </Typography>
              <Box sx={{ mt: 2 }}>
                <CircularProgress 
                  variant="determinate" 
                  value={metrics.memory} 
                  color={metrics.memory > 80 ? 'error' : metrics.memory > 60 ? 'warning' : 'success'}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Disk Usage
              </Typography>
              <Typography variant="h4">
                {metrics.disk}%
              </Typography>
              <Box sx={{ mt: 2 }}>
                <CircularProgress 
                  variant="determinate" 
                  value={metrics.disk} 
                  color={metrics.disk > 80 ? 'error' : metrics.disk > 60 ? 'warning' : 'success'}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                System Uptime
              </Typography>
              <Typography variant="h4">
                {metrics.uptime}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Active Users: {metrics.activeUsers}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                Last Update: {new Date(metrics.lastUpdate).toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
} 