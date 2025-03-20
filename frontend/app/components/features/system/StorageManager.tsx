'use client';

import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  Grid, 
  CircularProgress, 
  Alert,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  LinearProgress
} from '@mui/material';
import { useAuth } from '@/hooks/useAuth';

interface StorageMetrics {
  total: number;
  used: number;
  available: number;
  backupSize: number;
  lastBackup: string;
  recordingsSize: number;
  logsSize: number;
  usagePercent: number;
}

interface BackupConfig {
  schedule: string;
  retention: number;
  location: string;
}

export default function StorageManager() {
  const { user } = useAuth();
  const [metrics, setMetrics] = useState<StorageMetrics | null>(null);
  const [config, setConfig] = useState<BackupConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [backupDialog, setBackupDialog] = useState(false);
  const [backupProgress, setBackupProgress] = useState(0);

  useEffect(() => {
    const fetchStorageData = async () => {
      try {
        const [metricsResponse, configResponse] = await Promise.all([
          fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/system/storage`, {
            credentials: 'include',
          }),
          fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/system/backup-config`, {
            credentials: 'include',
          })
        ]);
        
        if (!metricsResponse.ok || !configResponse.ok) {
          throw new Error('Failed to fetch storage data');
        }
        
        const [metricsData, configData] = await Promise.all([
          metricsResponse.json(),
          configResponse.json()
        ]);
        
        setMetrics(metricsData);
        setConfig(configData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load storage data');
      } finally {
        setLoading(false);
      }
    };

    fetchStorageData();
    const interval = setInterval(fetchStorageData, 60000); // Update every minute

    return () => clearInterval(interval);
  }, []);

  const handleBackup = async () => {
    try {
      setBackupProgress(0);
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/system/backup`, {
        method: 'POST',
        credentials: 'include',
      });
      
      if (!response.ok) {
        throw new Error('Backup failed');
      }
      
      // Simulate backup progress
      for (let i = 0; i <= 100; i += 10) {
        await new Promise(resolve => setTimeout(resolve, 500));
        setBackupProgress(i);
      }
      
      setBackupDialog(false);
      // Refresh storage data
      const metricsResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/system/storage`, {
        credentials: 'include',
      });
      const metricsData = await metricsResponse.json();
      setMetrics(metricsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Backup failed');
    }
  };

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
        No storage metrics available
      </Alert>
    );
  }

  const formatBytes = (bytes: number) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 Byte';
    const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)).toString());
    return Math.round(bytes / Math.pow(1024, i)) + ' ' + sizes[i];
  };

  const usagePercentage = (metrics.used / metrics.total) * 100;

  return (
    <Box sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">
          Storage Management
        </Typography>
        <Button 
          variant="contained" 
          color="primary"
          onClick={() => setBackupDialog(true)}
        >
          Create Backup
        </Button>
      </Box>
      
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Storage Usage
              </Typography>
              <Box sx={{ mt: 2 }}>
                <LinearProgress 
                  variant="determinate" 
                  value={usagePercentage}
                  color={usagePercentage > 80 ? 'error' : usagePercentage > 60 ? 'warning' : 'success'}
                  sx={{ height: 10, borderRadius: 5 }}
                />
              </Box>
              <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                {formatBytes(metrics.used)} of {formatBytes(metrics.total)} used
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Recordings Storage
              </Typography>
              <Typography variant="h4">
                {formatBytes(metrics.recordingsSize)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Logs Storage
              </Typography>
              <Typography variant="h4">
                {formatBytes(metrics.logsSize)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Backup Size
              </Typography>
              <Typography variant="h4">
                {formatBytes(metrics.backupSize)}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Last Backup: {new Date(metrics.lastBackup).toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Dialog open={backupDialog} onClose={() => setBackupDialog(false)}>
        <DialogTitle>Create System Backup</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            This will create a backup of all system data including:
            <ul>
              <li>User data and permissions</li>
              <li>Face recognition models</li>
              <li>System configurations</li>
              <li>Access logs</li>
            </ul>
          </Typography>
          {backupProgress > 0 && (
            <Box sx={{ mt: 2 }}>
              <LinearProgress variant="determinate" value={backupProgress} />
              <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                Progress: {backupProgress}%
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBackupDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleBackup} 
            variant="contained" 
            color="primary"
            disabled={backupProgress > 0}
          >
            Start Backup
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
} 