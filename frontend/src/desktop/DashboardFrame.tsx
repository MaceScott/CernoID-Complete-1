import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  CircularProgress,
  IconButton,
  Tooltip,
  useTheme
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  Person as PersonIcon,
  Videocam as VideocamIcon
} from '@mui/icons-material';
import { BaseFrame } from './BaseFrame';
import { useApp } from '../context/AppContext';

interface SystemStats {
  totalFaces: number;
  activeCameras: number;
  processingRate: number;
  gpuUtilization: number;
  lastUpdate: string;
}

export const DashboardFrame: React.FC = () => {
  const theme = useTheme();
  const { state: { user } } = useApp();
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    try {
      setLoading(true);
      // TODO: Replace with actual API call
      const response = await fetch('/api/system/stats');
      const data = await response.json();
      setStats(data);
      setError(null);
    } catch (err) {
      setError('Failed to load system statistics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const StatCard: React.FC<{
    title: string;
    value: string | number;
    icon: React.ReactNode;
  }> = ({ title, value, icon }) => (
    <Paper
      elevation={2}
      sx={{
        p: 2,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        gap: 1
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        {icon}
        <Typography variant="h6" component="h2">
          {title}
        </Typography>
      </Box>
      <Typography variant="h4" component="p" sx={{ mt: 'auto' }}>
        {value}
      </Typography>
    </Paper>
  );

  return (
    <BaseFrame title="Dashboard">
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between' }}>
        <Typography variant="h4" component="h1">
          Welcome, {user?.name || user?.email}
        </Typography>
        <Box>
          <Tooltip title="Refresh Statistics">
            <IconButton onClick={fetchStats} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Settings">
            <IconButton>
              <SettingsIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {error && (
        <Paper
          sx={{
            p: 2,
            mb: 3,
            bgcolor: theme.palette.error.light,
            color: theme.palette.error.contrastText
          }}
        >
          {error}
        </Paper>
      )}

      {loading && !stats ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Total Faces"
              value={stats?.totalFaces || 0}
              icon={<PersonIcon color="primary" />}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Active Cameras"
              value={stats?.activeCameras || 0}
              icon={<VideocamIcon color="primary" />}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Processing Rate"
              value={`${stats?.processingRate || 0} fps`}
              icon={<RefreshIcon color="primary" />}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="GPU Utilization"
              value={`${stats?.gpuUtilization || 0}%`}
              icon={<SettingsIcon color="primary" />}
            />
          </Grid>
        </Grid>
      )}

      {stats && (
        <Typography
          variant="caption"
          sx={{ mt: 2, display: 'block', textAlign: 'right' }}
        >
          Last updated: {new Date(stats.lastUpdate).toLocaleString()}
        </Typography>
      )}
    </BaseFrame>
  );
}; 